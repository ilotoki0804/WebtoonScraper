"""Download Webtoons from `webtoons.com/en`."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from ..exceptions import InvalidWebtoonIdError
from ._01_scraper import Scraper, reload_manager


class WebtoonsDotcomScraper(Scraper[int]):
    """Scrape webtoons from Webtoon Originals."""

    BASE_URL = "https://www.webtoons.com/en/action/jungle-juice"
    TEST_WEBTOON_ID = 5291  # Wumpus
    TEST_WEBTOON_IDS = (
        5291,  # Wumpus
        263735,  # Spook
    )
    URL_REGEX = re.compile(
        r"(?:https?:\/\/)?(?:m|www)[.]webtoons[.]com\/(?:[^/]+\/){3}list\?(?:[^&]*&)*title_no=(?P<webtoon_id>\d+)(?:&.*)*"
    )
    base_url: str
    PLATFORM = "webtoons_dotcom"

    def __init__(self, webtoon_id) -> None:
        super().__init__(webtoon_id)
        self.headers.update(Referer="http://www.webtoons.com")

    @reload_manager
    def fetch_webtoon_information(self, *, reload: bool = False) -> None:
        self.base_url = "https://www.webtoons.com/en/action/jungle-juice"
        self.is_original = True
        response = self.hxoptions.get(f"{self.base_url}/list?title_no={self.webtoon_id}")

        if response.status_code == 404:
            self.base_url = "https://www.webtoons.com/en/challenge/meme-girls"
            self.is_original = False
            response = self.hxoptions.get(f"{self.base_url}/list?title_no={self.webtoon_id}")

        if response.status_code == 404:
            del self.is_original
            raise InvalidWebtoonIdError.from_webtoon_id(self.webtoon_id, type(self), rating_notice=True)

        title = response.soup_select_one('meta[property="og:title"]', no_empty_result=True).get("content")
        assert isinstance(title, str)

        webtoon_thumbnail = response.soup_select_one('meta[property="og:image"]', no_empty_result=True).get("content")
        assert isinstance(
            webtoon_thumbnail, str
        ), f"""Cannot get webtoon thumbnail. "og:image": {response.soup_select_one('meta[property="og:image"]')}"""

        self.title = title
        self.webtoon_thumbnail_url = webtoon_thumbnail

    @reload_manager
    def fetch_episode_information(self, *, reload: bool = False) -> None:
        # getting title_no
        url = f"{self.base_url}/list?title_no={self.webtoon_id}"
        title_no_str = (
            self.hxoptions.get(url).soup_select_one("#_listUl > li", no_empty_result=True).get("data-episode-no")
        )
        assert isinstance(title_no_str, str)
        title_no = int(title_no_str)

        # getting list of titles
        selector = "#_bottomEpisodeList > div.episode_cont > ul > li"
        url = f"{self.base_url}/prologue/viewer?title_no={self.webtoon_id}&episode_no={title_no}"
        selected = self.hxoptions.get(url).soup_select(selector)

        subtitles = []
        episode_ids = []
        for element in selected:
            episode_no_str = element["data-episode-no"]
            assert isinstance(episode_no_str, str)
            episode_no = int(episode_no_str)
            subtitles.append(element.select_one("span.subj").text)  # type: ignore
            episode_ids.append(episode_no)

        self.episode_titles = subtitles
        self.episode_ids = episode_ids

    def get_episode_image_urls(self, episode_no) -> list[str]:
        episode_id = self.episode_ids[episode_no]
        url = f"{self.base_url}/prologue/viewer?title_no={self.webtoon_id}&episode_no={episode_id}"
        episode_images_url = self.hxoptions.get(url).soup_select("#_imageList > img")
        episode_image_urls = [element["data-url"] for element in episode_images_url]
        if TYPE_CHECKING:
            episode_image_urls = [
                episode_image_url for episode_image_url in episode_image_urls if isinstance(episode_image_url, str)
            ]
        return episode_image_urls
