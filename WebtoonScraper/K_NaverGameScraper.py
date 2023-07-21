'''Download Webtoons from Naver Post.'''

import contextlib
# from pathlib import Path
from itertools import count
import json
from async_lru import alru_cache

if __name__ in ("__main__", "NaverGameScraper"):
    from C_Scraper import Scraper
else:
    from .C_Scraper import Scraper


class NaverGameScraper(Scraper):
    '''Scrape webtoons from Naver Post.'''
    def __init__(self, pbar_independent=False):
        super().__init__(pbar_independent)
        self.BASE_URL = 'https://game.naver.com/original_series'
        self.IS_STABLE_CONNECTION: bool = True

    @alru_cache(maxsize=4)
    async def _get_webtoon_infomation(self, titleid):
        url = f'https://apis.naver.com/nng_main/nng_main/original/series/{titleid}'
        webtoon_raw_data = await self.get_internet(get_type='requests', url=url)
        webtoon_raw_data = webtoon_raw_data.json()
        title = webtoon_raw_data['content']['seriesName']
        thumbnail = webtoon_raw_data['content']['seriesImage']['verticalLogoImageUrl']
        return title, thumbnail

    @alru_cache(maxsize=4)
    async def get_webtoon_data(self, titleid, episode_max_limit=500):
        # 여러 시즌을 하나로 통합
        content_raw_data = []
        for season in count(1):
            url = (f'https://apis.naver.com/nng_main/nng_main/original/series/{titleid}/seasons/{season}/contents'
                   f'?direction=NEXT&pagingType=CURSOR&sort=FIRST&limit={episode_max_limit}')
            res = await self.get_internet(get_type='requests', url=url)
            res = res.json()
            if not res['content']:
                break
            content_raw_data += res['content']['data']

        # 부제목, 이미지 데이터 불러옴
        # episodes_data = {}
        subtitles = []
        episode_images_url = []
        episode_ids = []
        for i, episode in enumerate(content_raw_data, 1):
            subtitle = episode['feed']['title']
            content_json_data = json.loads(episode['feed']['contents'])
            image_urls = []
            for image_url in content_json_data['document']['components']:
                with contextlib.suppress(KeyError):
                    image_urls.append(image_url['src'])
            # episodes_data[i] = {'subtitle': subtitle, 'image_urls': image_urls}
            episode_ids.append(i)
            subtitles.append(subtitle)
            episode_images_url.append(image_urls)

        title, thumbnail = await self._get_webtoon_infomation(titleid)

        return {'subtitles': subtitles, 'episode_images_url': episode_images_url, 'episode_ids': episode_ids, 'title': title, 'webtoon_thumbnail': thumbnail}

    async def get_title(self, titleid):
        return await super().get_title(titleid)

    async def save_webtoon_thumbnail(self, titleid, title, thumbnail_dir):
        return await super().save_webtoon_thumbnail(titleid, title, thumbnail_dir)

    async def get_all_episode_no(self, titleid):
        return await super().get_all_episode_no(titleid)

    async def get_subtitle(self, titleid, episode_no):
        return await super().get_subtitle(titleid, episode_no)

    async def get_episode_images_url(self, titleid, episode_no):
        return await super().get_episode_images_url(titleid, episode_no)


if __name__ == '__main__':
    wt = NaverGameScraper()
    wt.get_webtoon(5)  # 모배툰
