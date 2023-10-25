'''Download Webtoons from Bufftoon.'''

from __future__ import annotations
import re
from pathlib import Path
import time
import logging
from typing import TYPE_CHECKING

from typing_extensions import override

if __name__ in ("__main__", "G_bufftoon"):
    from A_scraper import Scraper, force_reload_if_reload
else:
    from .A_scraper import Scraper, force_reload_if_reload

TitleId = int


class BufftoonScraper(Scraper[int]):
    '''Scrape webtoons from Bufftoon.'''
    INTERVAL_BETWEEN_EPISODE_DOWNLOAD_SECONDS = 1
    BASE_URL = 'https://bufftoon.plaync.com'
    TEST_WEBTOON_ID = 1001216  # 비트
    IS_CONNECTION_STABLE = True
    URL_REGEX = r"(?:https?:\/\/)?bufftoon[.]plaync[.]com\/series\/(?P<webtoon_id>\d+)"

    @override
    def __init__(self, webtoon_id, cookie: str | None = None) -> None:
        super().__init__(webtoon_id)
        self.info_headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'ko,en-US;q=0.9,en;q=0.8',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            # 'Cookie': self.cookie,
            'Dnt': '1',
            'Host': 'bufftoon.plaync.com',
            'If-None-Match': '"3a315-EG2ELuRZJEgvGHGM2DBBGcLckb4"',
            'Referer': 'https://bufftoon.plaync.com/series/10099',  # 작동하면 바꾸고, 작동 안 해도 바꾸기
            'Sec-Ch-Ua': '"Not.A/Brand";v="8", "Chromium";v="114", "Microsoft Edge";v="114"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Sec-Gpc': '1',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.43',
        }
        self.cookie = cookie if cookie is not None else ''
        self.update_requests()

    @force_reload_if_reload
    @override
    def fetch_episode_informations(
        self,
        get_payment_required_episode: bool = False,
        get_login_requiered_episode: bool | None = None,
        limit: int = 500
    ) -> None:
        if not self.cookie:
            # 웹툰에 대한 정보를 알고 싶을 때도 호출되어서 성가실 수도 있음.
            logging.warning('Without setting cookie extremely limiting the range of downloadable episodes. '
                            'Please set cookie to valid download. '
                            'The tutoral is avilable in https://github.com/ilotoki0804/WebtoonScraper#레진코믹스-다운로드하기')

        url = f'https://api-bufftoon.plaync.com/v2/series/{self.webtoon_id}/episodes?sortType=2&offset=0&limit={limit}'
        raw_data = self.requests.get(url).json()
        subtitles = []
        episode_ids = []
        if get_login_requiered_episode is None:
            get_login_requiered_episode = bool(self.cookie)
        for raw_episode in raw_data['result']['episodes']:
            if not get_payment_required_episode and raw_episode['isPaymentEpisode']:
                logging.warning(f"Episode '{raw_episode['title']}' is not free of charge episode. It won't be downloaded.")
                continue
            if not get_login_requiered_episode and not raw_episode['isOpenFreeEpisode']:
                logging.warning(f"Episode '{raw_episode['title']}' is not opened for non-login users. It'll be not downloaded.")
                continue
            # episode_no = raw_episode['episodeOrder']
            raw_episode_id = raw_episode['listImgPath']
            raw_episode_id_processed = re.search(rf'contents\/.\/{self.webtoon_id}\/(\d+)\/', raw_episode_id)
            assert isinstance(raw_episode_id_processed, re.Match)
            episode_id = int(raw_episode_id_processed[1])
            episode_ids.append(episode_id)
            subtitles.append(raw_episode['title'])

        self.episode_titles = subtitles
        self.episode_ids = episode_ids

    @force_reload_if_reload
    @override
    def fetch_webtoon_information(self):
        response = self.requests.get(f'{self.BASE_URL}/series/{self.webtoon_id}')
        selector = '#content > div > div > div.series-info > div.cont > div.title'
        title = response.soup_select_one(selector, no_empty_result=True).text.strip()

        image_url_original = response.soup_select_one('#content > div > div > div.series-info > div.img',
                                                      no_empty_result=True)
        image_url_original = image_url_original['style']
        assert isinstance(image_url_original, str)
        image_url_processed = re.search(r'background-image:url[(](.+)[)];', image_url_original)
        assert isinstance(image_url_processed, re.Match)
        image_url = image_url_processed.group(1)

        self.title = title
        self.webtoon_thumbnail = image_url

    @override
    def get_episode_image_urls(self, episode_no) -> list[str]:
        episode_id = self.episode_ids[episode_no]
        url = f'{self.BASE_URL}/series/{self.webtoon_id}/{episode_id}'
        selector = '#content > div > div > div.viewer-wrapper > div > img'
        episode_images_url = self.requests.get(url, headers=self.info_headers).soup_select(selector)
        episode_images_url = [element['src'] for element in episode_images_url]

        if TYPE_CHECKING:
            episode_images_url = [
                element
                for element in episode_images_url
                if isinstance(element, str)
            ]

        return episode_images_url

    @override
    def download_image(self, episode_directory: Path, url: str, image_no: int, file_extension: str | None = 'png') -> None:
        super().download_image(episode_directory, url, image_no, file_extension)
