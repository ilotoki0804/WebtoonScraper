'''Scrape Webtoons from Naver Webtoon.'''

from __future__ import annotations
from itertools import count
import logging
from json.decoder import JSONDecodeError
from typing_extensions import override
from typing import TYPE_CHECKING, ClassVar

from requests_utils.exceptions import EmptyResultError
from async_lru import alru_cache

if __name__ in ("__main__", "B_naver_webtoon"):
    from A_scraper import Scraper
else:
    from .A_scraper import Scraper


class NaverWebtoonScraper(Scraper):
    '''Scrape webtoons from Naver Webtoon.'''
    BASE_URL = 'https://comic.naver.com/webtoon'
    IS_CONNECTION_STABLE = True
    IS_BEST_CHALLENGE: ClassVar[bool] = False
    # 네이버 웹툰과 베스트 도전은 selector가 다르기 때문에 필요함.
    EPISODE_IMAGES_URL_SELECTOR: ClassVar[str] = '#sectionContWide > img'

    @override
    def fetch_webtoon_information(self) -> None:
        super().fetch_webtoon_information()

        webtoon_json_info = self.requests.get(f'https://comic.naver.com/api/article/list/info?titleId={self.webtoon_id}').json()
        # webtoon_json_info['thumbnailUrl']  # 정사각형 썸네일
        webtoon_thumbnail = webtoon_json_info['sharedThumbnailUrl']  # 실제로 웹툰 페이지에 사용되는 썸네일
        title = webtoon_json_info['titleName']  # 제목
        is_best_challenge = webtoon_json_info['webtoonLevelCode']  # BEST_CHALLENGE or WEBTOON

        self.webtoon_thumbnail = webtoon_thumbnail
        self.title = title
        self.is_best_challenge = is_best_challenge == 'BEST_CHALLENGE'

        self.is_webtoon_information_loaded = True

    @override
    def fetch_episode_informations(self) -> None:
        super().fetch_episode_informations()

        prev_articleList = []
        subtitles = []
        episode_ids = []
        for i in count(1):
            url = f"https://comic.naver.com/api/article/list?titleId={self.webtoon_id}&page={i}&sort=ASC"
            try:
                res = self.requests.get(url).json()
            except JSONDecodeError:
                raise ValueError('Naver Webtoon changed their api specification. Contect developer to update get_title. '
                                 '...Or just webtoon you tried to download invalid or adult webtoon. '
                                 'WebtoonScraper currently not support downloading adult webtoon.')

            curr_articleList = res["articleList"]
            if prev_articleList == curr_articleList:
                break
            for article in curr_articleList:
                # subtitles[article["no"]] = article["subtitle"]
                subtitles.append(article["subtitle"])
                episode_ids.append(article["no"])

            prev_articleList = curr_articleList

        self.episode_titles = subtitles
        self.episode_ids = episode_ids

        self.is_episode_informations_loaded = True

    # # 이전 방식의 웹툰 썸네일 다운로더. 사용성은 다르지 않지만 API에 통합하는 방법이 더 깔끔하기에 사용하지 않는다.
    # # 이 주석은 일정한 기간 뒤에도 사용되지 않으면 삭제할 것.
    # async def download_webtoon_thumbnail(self, titleid, title, thumbnail_dir):
    #     url = f'{self.BASE_URL}/list?titleId={titleid}'
    #     res = self.requests.get(url)
    #     image_url = res.soup_select_one('meta[property="og:image"]', no_empty_result=True).get('content')
    #     if not isinstance(image_url, str):
    #         raise ValueError(f'image_url is not str. image_url: {image_url}')
    #     image_extension = self.get_file_extension(image_url)
    #     image_raw = self.requests.get(image_url).content
    #     image_path = thumbnail_dir / f'{title}.{image_extension}'
    #     image_path.write_bytes(image_raw)

    @override
    def get_episode_image_urls(self, episode_no) -> list[str]:
        # sourcery skip: de-morgan
        episode_id = self.episode_ids[episode_no]
        url = f'{self.BASE_URL}/detail?titleId={self.webtoon_id}&no={episode_id}'
        episode_image_urls_raw = self.requests.get(url).soup_select(self.EPISODE_IMAGES_URL_SELECTOR)
        episode_image_urls = [
            element['src'] for element in episode_image_urls_raw
            if not ('agerate' in element['src'] or 'ctguide' in element['src'])
        ]

        if TYPE_CHECKING:
            episode_image_urls = [
                url
                for url in episode_image_urls
                if isinstance(url, str)
            ]

        return episode_image_urls

    @override
    def check_if_legitimate_webtoon_id(self) -> str | None:
        try:
            self.fetch_webtoon_information()
        except ValueError:
            return None
        return self.title if self.is_best_challenge is self.IS_BEST_CHALLENGE else None


if __name__ == '__main__':
    wt = NaverWebtoonScraper(809590)  # 이번 생
    wt.download_webtoon()
