"""Download Webtoons from `webtoons.com/en`."""

from __future__ import annotations
import re

from typing import TYPE_CHECKING

from ..exceptions import InvalidWebtoonIdError
from .A_scraper import Scraper, reload_manager


class WebtoonsDotcomScraper(Scraper[int]):
    """Scrape webtoons from Webtoon Originals."""

    BASE_URL = "https://www.webtoons.com/en/action/jungle-juice"
    IS_CONNECTION_STABLE = False
    TEST_WEBTOON_ID = 5291  # Wumpus
    TEST_WEBTOON_IDS = (
        5291,  # Wumpus
        263735,  # Spook
    )
    URL_REGEX = re.compile(
        r"(?:https?:\/\/)?(?:m|www)[.]webtoons[.]com\/(?:[^/]+\/){3}list\?(?:.*&)*title_no=(?P<webtoon_id>\d+)(?:&.*)*"
    )
    base_url: str

    def __init__(self, titleid) -> None:
        super().__init__(titleid)
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
        assert isinstance(title, str), f"Title is not string. webtoon_id: {self.webtoon_id}"

        # # 자세한 건 잘 모르겠지만 네이버 오리지날은 webtoon thumbnail이 2개고 이 방식으로는 다른 형식의 thubnail을 이용할 수 있음.
        # url = f'{self.BASE_URL}/rss?title_no={self.webtoon_id}'
        # webtoon_thumbnail = self.requests.get(url).soup_select_one('channel > image > url', no_empty_result=True).text

        webtoon_thumbnail = response.soup_select_one('meta[property="og:image"]', no_empty_result=True).get("content")
        assert isinstance(
            webtoon_thumbnail, str
        ), f"""Cannot get webtoon thumbnail. "og:image": {response.soup_select_one('meta[property="og:image"]')}"""

        self.title = title
        self.webtoon_thumbnail_url = webtoon_thumbnail

    @reload_manager
    def fetch_episode_informations(self, *, reload: bool = False) -> None:
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
            episode_no_str = element.get("data-episode-no")
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
