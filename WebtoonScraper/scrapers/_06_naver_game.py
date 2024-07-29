"""Download Webtoons from Naver Game."""

from __future__ import annotations

import json
import re
from itertools import count

from ..base import logger
from ._01_scraper import Scraper, reload_manager


class NaverGameScraper(Scraper[int]):
    """Scrape webtoons from Naver Game."""

    TEST_WEBTOON_ID = 5  # 모배툰
    BASE_URL = "https://game.naver.com/original_series"
    URL_REGEX = re.compile(
        r"(?:https?:\/\/)?game[.]naver[.]com\/original_series\/(?P<webtoon_id>\d+)(\?(?:[^&]*&)*season=(?P<season>\d+))?"
    )
    PLATFORM = "naver_game"
    DEFAULT_IMAGE_FILE_EXTENSION = "png"
    INFORMATION_VARS = Scraper.INFORMATION_VARS | dict(
        episodes_image_urls=None,
        episodes_contents=None,
    )

    @reload_manager
    def fetch_webtoon_information(self, *, reload: bool = False) -> None:
        url = f"https://apis.naver.com/nng_main/nng_main/original/series/{self.webtoon_id}"
        webtoon_data = self.hxoptions.get(url).json()["content"]
        title = webtoon_data["seriesName"]
        thumbnail = webtoon_data["seriesImage"]["verticalLogoImageUrl"]

        self.title = title
        self.webtoon_thumbnail_url = thumbnail

    @reload_manager
    def fetch_episode_information(self, episode_max_limit=500, *, reload: bool = False) -> None:
        # 여러 시즌을 하나로 통합
        content_raw_data = []
        for season in count(1):
            url = (
                f"https://apis.naver.com/nng_main/nng_main/original/series/{self.webtoon_id}/seasons/{season}/contents"
                f"?direction=NEXT&pagingType=CURSOR&sort=FIRST&limit={episode_max_limit}"
            )
            res = self.hxoptions.get(url)
            res = res.json()
            if not res["content"]:
                break
            content_raw_data += res["content"]["data"]

        # 부제목, 이미지 데이터 불러옴
        subtitles = []
        episodes_image_urls = []
        episode_ids = []
        episodes_contents = []
        for i, episode in enumerate(content_raw_data, 1):
            subtitle = episode["feed"]["title"]
            contents_raw = episode["feed"]["contents"]
            contents = json.loads(contents_raw)
            image_urls = []
            for component in contents["document"]["components"]:
                ctype = component["@ctype"]
                if ctype == "image":
                    image_urls.append(component["src"])
                elif ctype == "imageGroup":
                    for image in component["images"]:
                        image_urls.append(image["src"])
                else:
                    if "src" in component:
                        logger.error(
                            f"A component with ctype: {ctype} has `src` key with value {component['src']!r}. It won't be downloaded and need to be checked."
                        )

            episode_ids.append(i)
            subtitles.append(subtitle)
            episodes_image_urls.append(image_urls)
            episodes_contents.append(contents_raw)

        self.episode_titles = subtitles
        self.episodes_image_urls = episodes_image_urls
        self.episode_ids = episode_ids
        self.episodes_contents = episodes_contents

    def get_episode_image_urls(self, episode_no):
        return self.episodes_image_urls[episode_no]
