'''Download Webtoons from Naver Post.'''

import contextlib
from pathlib import Path
from itertools import count
import json
from async_lru import alru_cache

if __name__ in ("__main__", "NaverGameScraper"):
    from Scraper import Scraper
else:
    from .Scraper import Scraper


class NaverGameScraper(Scraper):
    '''Scrape webtoons from Naver Post.'''
    def __init__(self, pbar_independent=False):
        super().__init__(pbar_independent)
        self.BASE_URL = 'https://game.naver.com/original_series'
        self.IS_STABLE_CONNECTION = True

    @alru_cache(maxsize=4)
    async def _get_webtoon_infomation(self, titleid):
        url = f'https://apis.naver.com/nng_main/nng_main/original/series/{titleid}'
        webtoon_raw_data = await self.get_internet(get_type='requests', url=url)
        webtoon_raw_data = webtoon_raw_data.json()
        title = webtoon_raw_data['content']['seriesName']
        thumbnail = webtoon_raw_data['content']['seriesImage']['verticalLogoImageUrl']
        return title, thumbnail

    @alru_cache(maxsize=4)
    async def _get_episode_infomation(self, titleid, episode_max_limit=500):
        # 여러 시즌을 하나로 통합
        content_raw_data = []
        for season in count(1):
            url = f'https://apis.naver.com/nng_main/nng_main/original/series/{titleid}/seasons/{season}/contents'\
                  f'?direction=NEXT&pagingType=CURSOR&sort=FIRST&limit={episode_max_limit}'
            res = await self.get_internet(get_type='requests', url=url)
            res = res.json()
            if not res['content']:
                break
            content_raw_data += res['content']['data']

        # 부제목, 이미지 데이터 불러옴
        episodes_data = {}
        for i, episode in enumerate(content_raw_data, 1):
            subtitle = episode['feed']['title']
            content_json_data = json.loads(episode['feed']['contents'])
            image_urls = []
            for image_url in content_json_data['document']['components']:
                with contextlib.suppress(KeyError):
                    image_urls.append(image_url['src'])
            episodes_data[i] = {'subtitle': subtitle, 'image_urls': image_urls}

        return episodes_data

    async def get_title(self, titleid, file_acceptable=True):
        title, _ = await self._get_webtoon_infomation(titleid)
        if file_acceptable:
            title = self.get_safe_file_name(title)
        return title

    async def save_webtoon_thumbnail(self, titleid, title, thumbnail_dir):
        _, image_url = await self._get_webtoon_infomation(titleid)
        image_extension = self.get_file_extension(image_url)
        image_raw = await self.get_internet(get_type='requests', url=image_url)
        image_raw = image_raw.content
        Path(f'{thumbnail_dir}/{title}.{image_extension}').write_bytes(image_raw)

    async def get_all_episode_no(self, titleid):
        episodes_data = await self._get_episode_infomation(titleid)
        return list(episodes_data)

    async def get_subtitle(self, titleid, episode_no, file_acceptable):
        episodes_data = await self._get_episode_infomation(titleid)
        subtitle = episodes_data[episode_no]['subtitle']
        if file_acceptable:
            subtitle = self.get_safe_file_name(subtitle)
        return subtitle

    async def get_episode_images_url(self, titleid, episode_no):
        episodes_data = await self._get_episode_infomation(titleid)
        return episodes_data[episode_no]['image_urls']


if __name__ == '__main__':
    wt = NaverGameScraper()
    wt.get_webtoon(5)  # 모배툰
