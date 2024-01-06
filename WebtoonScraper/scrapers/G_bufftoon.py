"""Download Webtoons from Bufftoon."""

from __future__ import annotations
import re
from pathlib import Path
import time
import logging
from typing import TYPE_CHECKING

import hxsoup

from WebtoonScraper.miscs import EpisodeNoRange

from .A_scraper import Scraper, reload_manager

TitleId = int


class BufftoonScraper(Scraper[int]):
    """Scrape webtoons from Bufftoon."""

    INTERVAL_BETWEEN_EPISODE_DOWNLOAD_SECONDS = 1
    BASE_URL = "https://bufftoon.plaync.com"
    TEST_WEBTOON_ID = 1001216  # 비트
    IS_CONNECTION_STABLE = True
    URL_REGEX = r"(?:https?:\/\/)?bufftoon[.]plaync[.]com\/series\/(?P<webtoon_id>\d+)"
    DEFAULT_IMAGE_FILE_EXTENSION = "png"

    def __init__(self, webtoon_id, cookie: str | None = None) -> None:
        super().__init__(webtoon_id)
        self.cookie = "" if cookie is None else cookie
        self.avoid_sslerror = True

    async def async_download_webtoon(
        self,
        episode_no_range: EpisodeNoRange = None,
        merge_number: int | None = None
    ) -> None:
        if not self.cookie:
            logging.warning(
                "Without setting cookie extremely limiting the range of downloadable episodes. "
                "Please set cookie to valid download. "
                "The tutoral is avilable in https://github.com/ilotoki0804/WebtoonScraper#레진코믹스-다운로드하기"
            )
        return await super().async_download_webtoon(episode_no_range, merge_number)

    @reload_manager
    def fetch_webtoon_information(self, *, reload: bool = False) -> None:
        response = self.hxoptions.get(f"{self.BASE_URL}/series/{self.webtoon_id}")
        selector = "#content > div > div > div.series-info > div.cont > div.title"
        title = response.soup_select_one(selector, no_empty_result=True).text.strip()

        image_url_original = response.soup_select_one(
            "#content > div > div > div.series-info > div.img", no_empty_result=True
        )
        image_url_original = image_url_original["style"]
        assert isinstance(image_url_original, str)
        image_url_processed = re.search(
            r"background-image:url[(](.+)[)];", image_url_original
        )
        assert isinstance(image_url_processed, re.Match)
        image_url = image_url_processed.group(1)

        self.title = title
        self.webtoon_thumbnail_url = image_url

    @reload_manager
    def fetch_episode_informations(
        self,
        get_payment_required_episode: bool = False,
        get_login_requiered_episode: bool | None = None,
        limit: int = 500,
        *,
        reload: bool = False,
    ) -> None:
        url = f"https://api-bufftoon.plaync.com/v2/series/{self.webtoon_id}/episodes?sortType=2&offset=0&limit={limit}"
        raw_data = self.hxoptions.get(url).json()
        subtitles = []
        episode_ids = []
        if get_login_requiered_episode is None:
            get_login_requiered_episode = bool(self.cookie)
        for raw_episode in raw_data["result"]["episodes"]:
            if not get_payment_required_episode and raw_episode["isPaymentEpisode"]:
                logging.warning(
                    f"Episode '{raw_episode['title']}' is not free of charge episode. It won't be downloaded."
                )
                continue
            if not get_login_requiered_episode and not raw_episode["isOpenFreeEpisode"]:
                logging.warning(
                    f"Episode '{raw_episode['title']}' is not opened for non-login users. It'll be not downloaded."
                )
                continue
            # episode_no = raw_episode['episodeOrder']
            raw_episode_id = raw_episode["listImgPath"]
            raw_episode_id_processed = re.search(
                rf"contents\/.\/{self.webtoon_id}\/(\d+)\/", raw_episode_id
            )
            assert isinstance(raw_episode_id_processed, re.Match)
            episode_id = int(raw_episode_id_processed[1])
            episode_ids.append(episode_id)
            subtitles.append(raw_episode["title"])

        self.episode_titles = subtitles
        self.episode_ids = episode_ids

    def get_episode_image_urls(self, episode_no) -> list[str]:
        episode_id = self.episode_ids[episode_no]
        url = f"{self.BASE_URL}/series/{self.webtoon_id}/{episode_id}"
        selector = "#content > div > div > div.viewer-wrapper > div > img"
        episode_images_url = self.hxoptions.get(url).soup_select(selector)
        episode_images_url = [element["src"] for element in episode_images_url]

        if TYPE_CHECKING:
            episode_images_url = [
                element for element in episode_images_url if isinstance(element, str)
            ]

        return episode_images_url
