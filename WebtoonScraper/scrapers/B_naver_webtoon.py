'''Scrape Webtoons from Naver Webtoon.'''

from __future__ import annotations
from itertools import count
import logging
from json.decoder import JSONDecodeError
from typing import TYPE_CHECKING, ClassVar

from typing_extensions import override

if __name__ in ("__main__", "B_naver_webtoon"):
    from A_scraper import Scraper, force_reload_if_reload
    from WebtoonScraper.exceptions import InvalidPlatformError
else:
    from .A_scraper import Scraper, force_reload_if_reload
    from ..exceptions import InvalidPlatformError


class NaverWebtoonScraper(Scraper[int]):
    '''Scrape webtoons from Naver Webtoon.'''
    BASE_URL = 'https://comic.naver.com/webtoon'
    IS_CONNECTION_STABLE = True
    TEST_WEBTOON_ID = 809590  # 이번 생
    IS_BEST_CHALLENGE: ClassVar[bool] = False
    # 네이버 웹툰과 베스트 도전은 selector가 다르기 때문에 필요함.
    EPISODE_IMAGES_URL_SELECTOR: ClassVar[str] = '#sectionContWide > img'
    URL_REGEX: str = r"(?:https?:\/\/)?(?:m[.])?comic[.]naver[.]com\/webtoon\/list\?(?:.*&)*titleId=(?P<webtoon_id>\d+)(?:&.*)*"

    @force_reload_if_reload
    @override
    def fetch_webtoon_information(self) -> None:
        webtoon_json_info = self.requests.get(f'https://comic.naver.com/api/article/list/info?titleId={self.webtoon_id}').json()
        # webtoon_json_info['thumbnailUrl']  # 정사각형 썸네일
        webtoon_thumbnail = webtoon_json_info['sharedThumbnailUrl']  # 실제로 웹툰 페이지에 사용되는 썸네일
        title = webtoon_json_info['titleName']  # 제목
        is_best_challenge = webtoon_json_info['webtoonLevelCode']  # BEST_CHALLENGE or WEBTOON

        self.webtoon_thumbnail = webtoon_thumbnail
        self.title = title
        self.is_best_challenge = is_best_challenge == 'BEST_CHALLENGE'

        if self.is_best_challenge is not self.IS_BEST_CHALLENGE:
            platform_name = 'Best Challenge' if is_best_challenge else 'Naver Webtoon'
            raise InvalidPlatformError(f"Use {platform_name} Scraper to download {platform_name}.")

    @force_reload_if_reload
    @override
    def fetch_episode_informations(self) -> None:
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
        except (InvalidPlatformError, Exception):
            return None
        return self.title if self.is_best_challenge is self.IS_BEST_CHALLENGE else None
