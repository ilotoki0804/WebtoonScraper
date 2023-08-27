'''Scrape Webtoons from Naver Webtoon.'''

from __future__ import annotations
from itertools import count

from async_lru import alru_cache
from requests_utils.exceptions import EmptyResultError

if __name__ in ("__main__", "D_NaverWebtoonScraper"):
    from C_Scraper import Scraper
else:
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
            res = self.requests.get(url).json()

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
        res = self.requests.get(url)
        try:
            return res.soup_select_one('meta[property="og:title"]', no_empty_result=True).get('content')
        except EmptyResultError:
            raise ValueError('Naver Webtoon changed their api specification. Contect developer to update get_title. '
                             'Webtoon you want to download is can be adult webtoon. '
                             'WebtoonScraper currently not support downloading adult webtoon.')

    async def save_webtoon_thumbnail(self, titleid, title, thumbnail_dir):
        url = f'{self.BASE_URL}/list?titleId={titleid}'
        res = self.requests.get(url)
        image_url = res.soup_select_one('meta[property="og:image"]', no_empty_result=True).get('content')
        if not isinstance(image_url, str):
            raise ValueError(f'image_url is not str. image_url: {image_url}')
        image_extension = self.get_file_extension(image_url)
        image_raw = self.requests.get(image_url).content
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
        episode_images_url = self.requests.get(url).soup_select(self.EPISODE_IMAGES_URL_SELECTOR)
        return [
            element['src'] for element in episode_images_url
            if not ('agerate' in element['src'] or 'ctguide' in element['src'])
        ]

    async def check_if_legitimate_titleid(self, titleid) -> str | None:
        title = self.requests.get(f'{self.BASE_URL}/list?titleId={titleid}').soup_select_one('span.text')
        return title.text if title else None


if __name__ == '__main__':
    wt = NaverWebtoonScraper()
    wt.download_one_webtoon(809590)  # 이번 생

    # # get_internet test(Scraper는 abstract class라 직접 실행이 불가해서 대신 사용)
    # import asyncio
    # wt.IS_STABLE_CONNECTION = False
    # asyncio.run(wt.get_internet('requests', 'https://not-working-url.com'))
