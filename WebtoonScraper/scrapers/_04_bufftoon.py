"""Download Webtoons from Bufftoon."""

from __future__ import annotations

import re
import ssl
from typing import TYPE_CHECKING

from ..base import logger
from ._01_scraper import Scraper, reload_manager


class BufftoonScraper(Scraper[int]):
    """Scrape webtoons from Bufftoon."""

    DOWNLOAD_INTERVAL = 1
    BASE_URL = "https://bufftoon.plaync.com"
    TEST_WEBTOON_ID = 1001216  # 비트
    URL_REGEX = re.compile(r"(?:https?:\/\/)?bufftoon[.]plaync[.]com\/series\/(?P<webtoon_id>\d+)")
    DEFAULT_IMAGE_FILE_EXTENSION = "png"
    PLATFORM = "bufftoon"
    INFORMATION_VARS = Scraper.INFORMATION_VARS | dict(
        login_required_episodes=None,
    )

    def __init__(self, webtoon_id, cookie: str | None = None) -> None:
        super().__init__(webtoon_id)
        self.cookie = "" if cookie is None else cookie
        self.hxoptions.verify = self._create_ssl_context()

    async def async_download_webtoon(self, *args, **kwargs) -> None:
        if not self.cookie:
            logger.warning(
                "Without setting cookie extremely limiting the range of downloadable episodes. "
                "Please set cookie to valid download. "
                "The tutorial is available in https://github.com/ilotoki0804/WebtoonScraper#레진코믹스-다운로드하기"
            )
        return await super().async_download_webtoon(*args, **kwargs)

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
        image_url_processed = re.search(r"background-image:url[(](.+)[)];", image_url_original)
        assert isinstance(image_url_processed, re.Match)
        image_url = image_url_processed.group(1)

        self.title = title
        self.webtoon_thumbnail_url = image_url

    @reload_manager
    def fetch_episode_information(
        self,
        get_payment_required_episode: bool = True,
        limit: int = 500,
        *,
        reload: bool = False,
    ) -> None:
        url = f"https://api-bufftoon.plaync.com/v2/series/{self.webtoon_id}/episodes?sortType=2&offset=0&limit={limit}"
        raw_data = self.hxoptions.get(url).json()
        subtitles = []
        episode_ids = []
        not_free_episodes = []
        login_required_episodes = []
        for raw_episode in raw_data["result"]["episodes"]:
            if not get_payment_required_episode and raw_episode["isPaymentEpisode"]:
                not_free_episodes.append(raw_episode["title"])
                continue
            if not self.cookie and not raw_episode["isOpenFreeEpisode"]:
                login_required_episodes.append(raw_episode["title"])
                continue
            # episode_no = raw_episode['episodeOrder']
            raw_episode_id = raw_episode["listImgPath"]
            raw_episode_id_processed = re.search(rf"contents\/.\/{self.webtoon_id}\/(\d+)\/", raw_episode_id)
            assert isinstance(raw_episode_id_processed, re.Match)
            episode_id = int(raw_episode_id_processed[1])
            episode_ids.append(episode_id)
            subtitles.append(raw_episode["title"])

        if not_free_episodes:
            logger.warning(
                f"Following episodes won't be downloaded because they're not free: {', '.join(not_free_episodes)}"
            )
        if login_required_episodes:
            logger.warning(
                f"Following episodes won't be downloaded because they're not free: {', '.join(login_required_episodes)}"
            )

        self.episode_titles = subtitles
        self.episode_ids = episode_ids
        self.login_required_episodes = login_required_episodes

    def get_episode_image_urls(self, episode_no) -> list[str]:
        episode_id = self.episode_ids[episode_no]
        url = f"{self.BASE_URL}/series/{self.webtoon_id}/{episode_id}"
        selector = "#content > div > div > div.viewer-wrapper > div > img"
        episode_images_url = self.hxoptions.get(url).soup_select(selector)
        episode_images_url = [element["src"] for element in episode_images_url]

        if TYPE_CHECKING:
            episode_images_url = [element for element in episode_images_url if isinstance(element, str)]

        return episode_images_url

    @staticmethod
    def _create_ssl_context():
        context = ssl.create_default_context()
        context.options |= 0x4
        return context
