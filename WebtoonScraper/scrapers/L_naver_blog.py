'''Download Webtoons from Naver Blog.'''

from __future__ import annotations
from pathlib import Path
from itertools import count
import logging
import time
from typing import NamedTuple, TYPE_CHECKING, NoReturn

from typing_extensions import override

from .A_scraper import Scraper, reload_manager
from ..exceptions import InvalidWebtoonId, InvalidBlogId, InvalidCategoryNo


class NaverBlogWebtoonId(NamedTuple):
    blog_id: str
    category_no: int


class NaverBlogScraper(Scraper[tuple[str, int]]):
    '''Scrape webtoons from Naver Blog.'''
    # __slots__ = 'title', 'webtoon_id', 'headers', 'webtoon_thumbnail', 'subtitle_list', 'episode_id_list'
    # __slots__ 구현하면 _return_cache같은 것들이 구현될 수 없을 수 있음(실제 그런지는 직접 확인하기.).
    # 따라서 만약 구현해야 할 경우 주의 요함.

    TEST_WEBTOON_ID = NaverBlogWebtoonId('bkid4', 55)  # 상덕
    IS_CONNECTION_STABLE = True
    BASE_URL = 'https://m.blog.naver.com'
    URL_REGEX = r'(?:https?:\/\/)?m[.]blog[.]naver[.]com\/(?P<blog_id>\w+)\?(?:.*&)*categoryNo=(?P<category_no>\d+)(?:&.*)*'

    @override
    def __init__(self, webtoon_id) -> None:
        super().__init__(webtoon_id)
        self.headers = {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'ko',
            'Cache-Control': 'no-cache',
            'Dnt': '1',
            'Pragma': 'no-cache',
            'Referer': 'https://m.blog.naver.com/',
            'Sec-Ch-Ua': '"Microsoft Edge";v="117", "Not;A=Brand";v="8", "Chromium";v="117"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36 Edg/117.0.2045.47'
        }
        self.update_requests()

    @override
    def get_webtoon_directory_name(self) -> str:
        blog_id, category_no = self.webtoon_id

        # string은 tuple()을 이용해면 quote가 제거되지 않아서 이 방식을 이용함.
        # 예를 들어 ('hello', 123)을 stringfy하면 "('hello', 123)"이 됨.
        return f'{self.title}({blog_id}, {category_no})'

    @reload_manager
    @override
    def fetch_episode_informations(self, limit: int = 1000, *, reload: bool = False):
        blog_id, category_no = self.webtoon_id

        url = f'{self.BASE_URL}/api/blogs/{blog_id}/post-list?categoryNo={category_no}&itemCount={limit}&page=1'

        response = self.requests.get(url)
        if response.json()['isSuccess'] is False:
            raise InvalidBlogId("Invalid blog id. Maybe there's a typo or blog is closed.")
        if response.json()['result']['categoryName'] == '전체글':
            raise InvalidCategoryNo("Invalid category number. Maybe there's a typo or category is deleted.")

        fetch_result = response.json()['result']

        if len(fetch_result['items']) == limit:
            logging.warning('It seems to go beyond limit. automatically increase limit.')
            return self.fetch_episode_informations(limit * 2)

        self.title: str = fetch_result['categoryName']
        self.webtoon_thumbnail: str = fetch_result['items'][0]['thumbnailUrl'] + '?type=ffn640_640'

        self.episode_titles: list[str] = []
        self.episode_ids: list[int] = []
        self.episodes_image_urls: list[list[str]] = []
        for episode in reversed(fetch_result['items']):
            self.episode_titles.append(episode['titleWithInspectMessage'])
            self.episode_ids.append(episode['logNo'])

            # 아래 코드보다 콤펙트한 버전. 만약 다운로드가 잘 안 될 경우
            # 이 코드를 비활성화하고 아래 코드를 활성화해서 경고가 나오지는 않는지 확인할 것.
            one_episode_image_urls = [thumbnail['encodedThumbnailUrl'] + '?type=w800'
                                      for thumbnail in fetch_result['items'][-1]['thumbnailList']]

            # 흔하지 않은 타입에 대한 경고를 포함한 버전.
            # 위의 리스트 컴프리헨션 버전이 실사용 시에 충분히 문제 없이 동작한다면 제거하기.
            # one_episode_image_urls = []
            # for thumbnail in episode['thumbnailList']:
            #     if thumbnail['type'] != 'P':
            #         logging.warning(f'Unknown type {thumbnail["type"]}')
            #     if (thumbnail['videoAniThumbnailUrl']
            #             or thumbnail['videoPlayTime']
            #             or thumbnail['videoThumbnail']
            #             or thumbnail['vrthumbnail']):
            #         logging.warning(f'Unexpected information detected: {thumbnail}')
            #     one_episode_image_urls.append(thumbnail['encodedThumbnailUrl'] + '?type=w800')

            self.episodes_image_urls.append(one_episode_image_urls)

    @reload_manager
    @override
    def fetch_webtoon_information(self, *, reload: bool = False) -> None:
        # raise UseFetchEpisode()
        self.fetch_episode_informations()

    @override
    def get_episode_image_urls(self, episode_no):
        return self.episodes_image_urls[episode_no]

    def check_if_legitimate_webtoon_id(self) -> str | None:
        return super().check_if_legitimate_webtoon_id(InvalidWebtoonId)
