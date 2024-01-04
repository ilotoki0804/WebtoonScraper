"""Download Webtoons from Naver Post."""

from __future__ import annotations
import asyncio
from collections import defaultdict, deque
from itertools import count
import logging
import time
from typing import NamedTuple, TYPE_CHECKING

import demjson3
from bs4 import BeautifulSoup
from tqdm import tqdm

from ..miscs import EpisodeNoRange
from ..exceptions import InvalidFetchResultError

from .A_scraper import Scraper, reload_manager


class NaverPostWebtoonId(NamedTuple):
    series_no: int
    member_no: int


class NaverPostScraper(Scraper[tuple[int, int]]):
    """Scrape webtoons from Naver Post."""

    TEST_WEBTOON_ID = NaverPostWebtoonId(597061, 19803452)  # 겜덕겜소
    IS_CONNECTION_STABLE = True
    BASE_URL = "https://post.naver.com"
    URL_REGEX: str = (
        r"(?:https?:\/\/)?(?:m|www)[.]post[.]naver[.]com\/my\/series\/detail[.]naver"
        r"\?(?:.*&)*seriesNo=(?P<webtoon_id>\d+)(?:&.*)*(?:.*&)*memberNo=(?P<memberNo>\d+)(?:&.*)*"
    )
    INTERVAL_BETWEEN_EPISODE_DOWNLOAD_SECONDS = 1

    def __init__(self, webtoon_id) -> None:
        super().__init__(webtoon_id)
        self.headers = {
            "Accept": "image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "ko,en-US;q=0.9,en;q=0.8",
            "Cache-Control": "no-cache",
            "Dnt": "1",
            "Pragma": "no-cache",
            "Referer": "https://m.post.naver.com/",
            "Sec-Ch-Ua": '"Chromium";v="116", "Not)A;Brand";v="24", "Microsoft Edge";v="116"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "image",
            "Sec-Fetch-Mode": "no-cors",
            "Sec-Fetch-Site": "cross-site",
            "Sec-Gpc": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36 Edg/116.0.1938.69",
        }

    def get_webtoon_directory_name(self) -> str:
        # tuple already contains parentheses, and without tuple, NamedTuple can be stringfied.
        return f"{self.title}{tuple(self.webtoon_id)}"

    async def _download_episodes(self, episode_no_list, webtoon_directory) -> None:
        self.pbar = tqdm(total=len(episode_no_list))
        episode_ids_to_try: deque[int] = deque(range(len(episode_no_list)))
        try_counts = defaultdict(int)
        async with self.hxoptions.build_async_client() as client:
            while True:
                episode_no = episode_ids_to_try.popleft()
                time.sleep(self.INTERVAL_BETWEEN_EPISODE_DOWNLOAD_SECONDS)

                try:
                    await self._download_episode(episode_no, webtoon_directory, client)
                except InvalidFetchResultError:
                    attempts = self.hxoptions.attempts
                    try_counts[episode_no] += 1
                    if attempts is None or attempts <= try_counts[episode_no]:
                        logging.warning(
                            "Failed to download following episodes: "
                            + ", ".join(f"{self.episode_titles[i]}(tried {try_counts[i]} time(s))" for i in sorted(episode_ids_to_try))
                        )
                        return

                    episode_ids_to_try.append(episode_no)
                else:
                    self.pbar.update(1)
                    if not episode_ids_to_try:
                        return

    @reload_manager
    def fetch_episode_informations(self, *, reload: bool = False) -> None:
        series_no, member_no = self.webtoon_id
        subtitle_list: list[str] = []
        episode_id_list: list[int] = []
        prev_data = decoded_response_data = None
        for i in count(1):
            # n번째 리스트 불러옴
            url = (
                f"{self.BASE_URL}/my/series/detail/more.nhn"
                f"?memberNo={member_no}&seriesNo={series_no}&lastSortOrder=49"
                f"&prevVolumeNo=&fromNo={i}&totalCount=68"
            )
            response_text: str = self.hxoptions.get(url).text

            # 네이버는 기본적으로 json이 망가져 있기에 json이 망가져 있어도 parse를 해주는 demjson이 필요
            # demjson3.decode()의 결과값은 dict임. 하지만 어째선지 타입 체커가 오작동하니 type: ignore가 필요.
            decoded_response_data = demjson3.decode(response_text)["html"]  # type: ignore
            soup = BeautifulSoup(decoded_response_data, "html.parser")

            if prev_data == decoded_response_data is not None:
                break

            subtitle_list += [
                tag.text.strip() for tag in soup.select("ul > li > a > div > span.ell")
            ]
            episode_id_list += [
                next(map(int, tag.get("data-cid").split("_")))  # type: ignore
                for tag in soup.select("ul > li > a > div > span.spot_post_like")
            ]

            prev_data = decoded_response_data

        self.episode_titles = subtitle_list[::-1]
        self.episode_ids = episode_id_list[::-1]

    @reload_manager
    def fetch_webtoon_information(self, *, reload: bool = False) -> None:
        series_no, member_no = self.webtoon_id
        response = self.hxoptions.get(
            f"https://m.post.naver.com/my/series/detail.naver?seriesNo={series_no}&memberNo={member_no}"
        )
        title: str = response.soup_select_one(
            "h2.tit_series > span", no_empty_result=True
        ).text.strip()

        image_url_original = response.soup_select_one(
            'meta[property="og:image"]', no_empty_result=True
        )
        image_url: str = image_url_original["content"]  # type: ignore

        self.title = title
        self.webtoon_thumbnail = image_url

    def get_episode_image_urls(self, episode_no):
        series_no, member_no = self.webtoon_id
        episode_id = self.episode_ids[episode_no]
        url = f"https://m.post.naver.com/viewer/postView.naver?volumeNo={episode_id}&memberNo={member_no}"
        response = self.hxoptions.get(url)
        content = response.soup_select_one("#__clipContent")
        if content is None:
            raise InvalidFetchResultError

        content = content.text
        soup_content = BeautifulSoup(content, "html.parser")

        # 문서 내에 있는 모든 이미지 링크를 불러옴
        selector = "div.se_component_wrap.sect_dsc.__se_component_area > div > div > div > div > a > img"
        episode_images_url = [tag["data-src"] for tag in soup_content.select(selector)]
        if TYPE_CHECKING:
            episode_images_url = [
                episode_image_url
                for episode_image_url in episode_images_url
                if isinstance(episode_image_url, str)
            ]

        return [
            url
            for url in episode_images_url
            if not url.startswith("https://mail.naver.com/read/image/")
        ]
