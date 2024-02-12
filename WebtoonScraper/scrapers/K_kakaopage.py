"""Download Webtoons from Kakaopage."""

from __future__ import annotations
from pathlib import Path

from hxsoup.client import AsyncClient

from .A_scraper import Scraper, reload_manager
from .K_kakaopage_queries import WEBTOON_DATA_QUERY, EPISODE_IMAGES_QUERY
from ..exceptions import InvalidWebtoonIdError


class KakaopageScraper(Scraper[int]):
    """Scrape webtoons from Kakaopage."""

    BASE_URL = "https://page.kakao.com"
    IS_CONNECTION_STABLE = False
    TEST_WEBTOON_ID = 53397318  # 부기영화
    URL_REGEX = r"(?:https?:\/\/)?page[.]kakao[.]com\/content\/(?P<webtoon_id>\d+)"
    DEFAULT_IMAGE_FILE_EXTENSION = "jpg"
    INTERVAL_BETWEEN_EPISODE_DOWNLOAD_SECONDS = 0.5

    def __init__(self, webtoon_id: int):
        super().__init__(webtoon_id)
        self.headers = {}
        self.graphql_headers = {
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "ko,en-US;q=0.9,en;q=0.8",
            "Cache-Control": "no-cache",
            "Content-Type": "application/json",
            # "Cookie": self.cookie,
            "Dnt": "1",
            "Origin": "https://page.kakao.com",
            "Pragma": "no-cache",
            "Referer": "https://page.kakao.com/content/53397318",
            "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Microsoft Edge";v="120"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Gpc": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        }

    @reload_manager
    def fetch_webtoon_information(self, *, reload: bool = False) -> None:
        res = self.hxoptions.get(f"https://page.kakao.com/content/{self.webtoon_id}")

        title = res.soup_select_one(
            'meta[property="og:title"]', no_empty_result=True
        ).get("content")
        if title == "카카오페이지" or not isinstance(title, str):
            raise InvalidWebtoonIdError.from_webtoon_id(
                self.webtoon_id, type(self), rating_notice=True
            )

        thumbnail_url = res.soup_select_one(
            'meta[property="og:image"]', no_empty_result=True
        ).get("content")
        assert isinstance(thumbnail_url, str)

        self.title = title
        self.webtoon_thumbnail_url = thumbnail_url

    @reload_manager
    def fetch_episode_informations(self, *, reload: bool = False) -> None:
        curser = "0"
        # episode_length: int = 0
        has_next_page: bool = True
        webtoon_episodes_data = []
        while has_next_page:
            post_data = {
                "query": WEBTOON_DATA_QUERY,
                "variables": {
                    "boughtOnly": False,
                    "after": curser,
                    "seriesId": self.webtoon_id,
                    "sortType": "asc",
                },
            }

            res = self.hxoptions.post(
                "https://page.kakao.com/graphql",
                json=post_data,
                headers=self.graphql_headers,
            )

            webtoon_raw_data = res.json()["data"]["contentHomeProductList"]

            # episode_length = webtoon_raw_data["totalCount"]
            has_next_page = webtoon_raw_data["pageInfo"]["hasNextPage"]
            curser = webtoon_raw_data["pageInfo"]["endCursor"]
            webtoon_episodes_data += webtoon_raw_data["edges"]

        # urls: list[str] = []
        episode_ids: list[int] = []
        is_free: list[bool] = []
        subtitles: list[str] = []
        for webtoon_episode_data in webtoon_episodes_data:
            # urls += "https://page.kakao.com/" + raw_url.removeprefix("kakaopage://open/")
            episode_ids.append(
                webtoon_episode_data["node"]["single"]["productId"]
            )  # 에피소드 id
            is_free.append(webtoon_episode_data["node"]["single"]["isFree"])  # 무료인지 여부
            subtitles.append(webtoon_episode_data["node"]["single"]["title"])

        self.episode_titles = subtitles
        self.episode_ids = episode_ids

    def get_episode_image_urls(self, episode_no) -> list[str]:
        episode_id = self.episode_ids[episode_no]

        post_data = {
            "operationName": "viewerInfo",
            "query": EPISODE_IMAGES_QUERY,
            "variables": {"seriesId": self.webtoon_id, "productId": episode_id},
        }

        res = self.hxoptions.post(
            "https://page.kakao.com/graphql",
            json=post_data,
            headers=self.graphql_headers,
        ).json()["data"]

        return [
            i["secureUrl"]
            for i in res["viewerInfo"]["viewerData"]["imageDownloadData"]["files"]
        ]
