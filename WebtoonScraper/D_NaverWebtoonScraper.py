'''Download Webtoons from Naver Webtoon.'''

from __future__ import annotations
from itertools import count

from async_lru import alru_cache

if __name__ in ("__main__", "D_NaverWebtoonScraper"):
    from C_Scraper import Scraper
else:
    # from Scraper import Scraper
    from .C_Scraper import Scraper


class NaverWebtoonScraper(Scraper):
    '''Scrape webtoons from Naver Webtoon.'''
    def __init__(self, pbar_independent=False):
        super().__init__(pbar_independent)
        self.BASE_URL = 'https://comic.naver.com/webtoon'
        self.IS_STABLE_CONNECTION = True
        self.EPISODE_IMAGES_URL_SELECTOR = '#sectionContWide > img'  # for best challenge

    @alru_cache(maxsize=4)
    async def get_webtoon_data(self, titleid: int):
        prev_articleList = []
        subtitles = []
        episode_id = []
        for i in count(1):
            url = f"https://comic.naver.com/api/article/list?titleId={titleid}&page={i}&sort=ASC"
            res = await self.get_internet('requests', url)
            res = res.json()

            curr_articleList = res["articleList"]
            if prev_articleList == curr_articleList:
                break
            for article in curr_articleList:
                # subtitles[article["no"]] = article["subtitle"]
                subtitles.append(article["subtitle"])
                episode_id.append(article["no"])

            prev_articleList = curr_articleList

        return {'subtitles': subtitles, 'episode_ids': episode_id}

    async def get_title(self, titleid):
        url = f'{self.BASE_URL}/list?titleId={titleid}'
        title = await self.get_internet(get_type='soup_select_one', url=url,
                                        selector='meta[property="og:title"]')
        if not title:
            raise ConnectionError('Naver Webtoon changed their api specification. Contect developer to update get_title. '
                                  'Webtoon you want to download is can be adult webtoon. '
                                  'WebtoonScraper currently not support downloading adult webtoon.')
        return title['content']

    async def save_webtoon_thumbnail(self, titleid, title, thumbnail_dir):
        url = f'{self.BASE_URL}/list?titleId={titleid}'
        image_url_tag = await self.get_internet(get_type='soup_select_one', url=url,
                                                selector='meta[property="og:image"]')
        if not image_url_tag:
            raise ConnectionError('Naver Webtoon changed their api specification. Contect developer to update get_title.')
        image_url: str = image_url_tag['content']
        image_extension = self.get_file_extension(image_url)
        image_raw = await self.get_internet(get_type='requests', url=image_url)
        image_raw = image_raw.content
        image_path = thumbnail_dir / f'{title}.{image_extension}'
        image_path.write_bytes(image_raw)

    async def get_all_episode_no(self, titleid):
        return await super().get_all_episode_no(titleid)

    async def get_subtitle(self, titleid, episode_no):
        return await super().get_subtitle(titleid, episode_no)

    async def get_episode_images_url(self, titleid, episode_no):
        # sourcery skip: de-morgan
        episode_id = await self.episode_no_to_episode_id(titleid, episode_no)
        url = f'{self.BASE_URL}/detail?titleId={titleid}&no={episode_id}'
        episode_images_url = await self.get_internet(get_type='soup_select', url=url,
                                                     selector=self.EPISODE_IMAGES_URL_SELECTOR)
        return [
            element['src'] for element in episode_images_url
            if not ('agerate' in element['src'] or 'ctguide' in element['src'])
        ]


if __name__ == '__main__':
    wt = NaverWebtoonScraper()
    wt.download_one_webtoon(809590)  # 이번 생

    # # get_internet test(Scraper는 abstract class라 직접 실행이 불가해서 대신 사용)
    # import asyncio
    # wt.IS_STABLE_CONNECTION = False
    # asyncio.run(wt.get_internet('requests', 'https://koifoiewofi.com'))
