'''Download Webtoons from Kakaopage.'''

from __future__ import annotations

from typing_extensions import override

from .A_scraper import Scraper, reload_manager
from .K_kakaopage_queries import WEBTOON_DATA_QUERY, EPISODE_IMAGES_QUERY
from ..exceptions import InvalidWebtoonIdError


class KakaopageScraper(Scraper[int]):
    '''Scrape webtoons from Kakaopage.'''
    BASE_URL = 'https://page.kakao.com'
    IS_CONNECTION_STABLE = False
    TEST_WEBTOON_ID = 53397318  # 부기영화
    URL_REGEX = r"(?:https?:\/\/)?page[.]kakao[.]com\/content\/(?P<webtoon_id>\d+)"

    def __init__(self, webtoon_id: int):
        super().__init__(webtoon_id)
        self.headers = {}
        self.graphql_headers = {
            "Accept": "application/graphql+json, application/json",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "ko,en-US;q=0.9,en;q=0.8",
            "Cache-Control": "no-cache",
            "Content-Length": "4371",
            "Content-Type": "application/json",
            # "Cookie": self.cookie,
            "Dnt": "1",
            "Origin": "https://page.kakao.com",
            "Pragma": "no-cache",
            "Referer": "https://page.kakao.com/content/53397318/viewer/53486401",
            "Sec-Ch-Ua": '"Not/A)Brand";v="99", "Microsoft Edge";v="115", "Chromium";v="115"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Gpc": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
        }
        self.update_requests()

    @reload_manager
    def fetch_webtoon_information(self, *, reload: bool = False) -> None:
        res = self.requests.get(f"https://page.kakao.com/content/{self.webtoon_id}")

        title = res.soup_select_one('meta[property="og:title"]', no_empty_result=True).get("content")
        if title == '카카오페이지' or not isinstance(title, str):
            raise InvalidWebtoonIdError("WebtoonId is invalid or that of adult webtoon.")

        thumnail_url = res.soup_select_one('meta[property="og:image"]', no_empty_result=True).get("content")
        assert isinstance(thumnail_url, str)

        self.title = title
        self.webtoon_thumbnail = thumnail_url

    @reload_manager
    def fetch_episode_informations(self, *, reload: bool = False) -> None:
        curser = 0
        # episode_length: int = 0
        has_next_page: bool = True
        webtoon_episodes_data = []
        while has_next_page:
            post_data = {
                "operationName": "contentHomeProductList",
                "query": WEBTOON_DATA_QUERY,
                "variables": {"seriesId": self.webtoon_id, "after": str(curser), "boughtOnly": False, "sortType": "asc"},
            }

            res = self.requests.post(
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
            episode_ids.append(webtoon_episode_data["node"]["single"]["productId"])  # 에피소드 id
            is_free.append(webtoon_episode_data["node"]["single"]["isFree"])  # 무료인지 여부
            subtitles.append(webtoon_episode_data["node"]["single"]["title"])

        self.episode_titles = subtitles
        self.episode_ids = episode_ids

    def download_image(self, episode_directory, url: str, image_no: int, file_extension: str | None = 'jpg') -> None:
        return super().download_image(episode_directory, url, image_no, file_extension)

    def download_webtoon_thumbnail(self, thumbnail_directory, file_extension: str | None = 'jpg') -> None:
        return super().download_webtoon_thumbnail(thumbnail_directory, file_extension)

    def get_episode_image_urls(self, episode_no) -> list[str]:
        episode_id = self.episode_ids[episode_no]

        query = EPISODE_IMAGES_QUERY

        post_data = {
            "operationName": "viewerInfo",
            "query": query,
            "variables": {"seriesId": self.webtoon_id, "productId": episode_id},
        }

        res = self.requests.post(
            "https://page.kakao.com/graphql",
            json=post_data,
            headers=self.graphql_headers,
        ).json()

        return [i['secureUrl']
                for i in res["data"]["viewerInfo"]["viewerData"]["imageDownloadData"]["files"]]
