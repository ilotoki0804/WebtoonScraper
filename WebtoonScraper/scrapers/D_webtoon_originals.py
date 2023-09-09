'''Download Webtoons from Webtoon Originals.'''

from __future__ import annotations
from typing import TYPE_CHECKING
from typing_extensions import override
from bs4 import BeautifulSoup
from bs4.element import Tag
from async_lru import alru_cache
from requests_utils.exceptions import EmptyResultError

if __name__ in ("__main__", "D_webtoon_originals"):
    from A_scraper import Scraper
else:
    from .A_scraper import Scraper


class WebtoonOriginalsScraper(Scraper[int]):
    '''Scrape webtoons from Webtoon Originals.'''
    BASE_URL = 'https://www.webtoons.com/en/fantasy/watermelon'
    IS_CONNECTION_STABLE = False
    TEST_WEBTOON_ID = 5291  # Wumpus

    @override
    def __init__(self, titleid) -> None:
        super().__init__(titleid)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36',
            "Referer": "http://www.webtoons.com"
        }
        self.update_requests()

    @override
    def fetch_webtoon_information(self) -> None:
        super().fetch_webtoon_information()

        response = self.requests.get(f'{self.BASE_URL}/list?title_no={self.webtoon_id}')
        title = response.soup_select_one('meta[property="og:title"]', no_empty_result=True).get('content')
        assert isinstance(title, str), f'Title is not string. webtoon_id: {self.webtoon_id}'

        # # 자세한 건 잘 모르지만 네이버 오리지날은 webtoon thumbnail이 2개고 이 방식으로는 다른 형식의 thubnail을 이용할 수 있음.
        # url = f'{self.BASE_URL}/rss?title_no={self.webtoon_id}'
        # webtoon_thumbnail = self.requests.get(url).soup_select_one('channel > image > url', no_empty_result=True).text

        webtoon_thumbnail = response.soup_select_one('meta[property="og:image"]', no_empty_result=True).get('content')
        assert isinstance(
            webtoon_thumbnail, str
        ), f'''Cannot get webtoon thumbnail. "og:image": {response.soup_select_one('meta[property="og:image"]')}'''

        self.title = title
        self.webtoon_thumbnail = webtoon_thumbnail

        self.is_webtoon_information_loaded = True

    @override
    def fetch_episode_informations(self) -> None:
        super().fetch_episode_informations()

        # getting title_no
        url = f'{self.BASE_URL}/list?title_no={self.webtoon_id}'
        title_no_str = self.requests.get(url).soup_select_one('#_listUl > li', no_empty_result=True).get('data-episode-no')
        assert isinstance(title_no_str, str)
        title_no = int(title_no_str)

        # getting list of titles
        selector = '#_bottomEpisodeList > div.episode_cont > ul > li'
        url = f'{self.BASE_URL}/prologue/viewer?title_no={self.webtoon_id}&episode_no={title_no}'
        selected = self.requests.get(url).soup_select(selector)

        subtitles = []
        episode_ids = []
        for element in selected:
            episode_no_str = element.get('data-episode-no')
            assert isinstance(episode_no_str, str)
            episode_no = int(episode_no_str)
            # subtitles[episode_no] = element.select_one("span.subj").text
            subtitles.append(element.select_one("span.subj").text)  # type: ignore
            episode_ids.append(episode_no)

        # return {'subtitles': subtitles, 'episode_ids': episode_ids}
        self.episode_titles = subtitles
        self.episode_ids = episode_ids

        self.is_webtoon_information_loaded = True

    # async def download_webtoon_thumbnail(self, titleid, title, thumbnail_dir):
    #     url = f'{self.BASE_URL}/list?title_no={titleid}'
    #     image_url_original = self.requests.get(url).soup_select_one('meta[property="og:image"]', no_empty_result=True)
    #     image_url: str = image_url_original['content']
    #     image_extension = self.get_file_extension(image_url)
    #     image_raw = self.requests.get(image_url).content
    #     thumbnail_file = thumbnail_dir / f'{title}.{image_extension}'
    #     thumbnail_file.write_bytes(image_raw)

    # async def save_real_webtoon_thumbnail(self, titleid, title, thumbnail_dir):
    #     '''save another form of thumbnail.'''
    #     url = f'{self.BASE_URL}/rss?title_no={titleid}'
    #     image_url = self.requests.get(url).soup_select_one('channel > image > url', no_empty_result=True).text
    #     image_extension = self.get_file_extension(image_url)
    #     image_raw = self.requests.get(image_url).content
    #     thumbnail_path = thumbnail_dir / f'{title}.{image_extension}'
    #     thumbnail_path.write_bytes(image_raw)

    # async def get_all_episode_no(self, titleid):
    #     return await super().get_all_episode_no(titleid)

    # async def get_subtitle(self, titleid, episode_no):
    #     return await super().get_subtitle(titleid, episode_no)

    @override
    def get_episode_image_urls(self, episode_no) -> list[str]:
        episode_id = self.episode_ids[episode_no]
        url = f'{self.BASE_URL}/prologue/viewer?title_no={self.webtoon_id}&episode_no={episode_id}'
        episode_images_url = self.requests.get(url).soup_select('#_imageList > img')
        episode_image_urls = [element['data-url'] for element in episode_images_url]
        if TYPE_CHECKING:
            episode_image_urls = [episode_image_url for episode_image_url in episode_image_urls
                                  if isinstance(episode_image_url, str)]
        return episode_image_urls
