'''Download Webtoons from Naver Webtoon.'''
from itertools import count
from async_lru import alru_cache

print(__name__)
if __name__ in ("__main__", "NaverWebtoonScraper"):
    from Scraper import Scraper
else:
    # from Scraper import Scraper
    from .Scraper import Scraper


class NaverWebtoonScraper(Scraper):
    '''Scrape webtoons from Naver Webtoon.'''
    def __init__(self, pbar_independent=False, short_connection=False):
        super().__init__(pbar_independent, short_connection)
        self.BASE_URL = 'https://comic.naver.com/webtoon'
        if not short_connection:
            self.IS_STABLE_CONNECTION = True
        self.EPISODE_IMAGES_URL_SELECTOR = '#sectionContWide > img'  # for best challenge

    @alru_cache(maxsize=4)
    async def _get_webtoon_data(self, titleid: int):
        prev_articleList = []
        subtitles = {}
        for i in count(1):
            url = f"https://comic.naver.com/api/article/list?titleId={titleid}&page={i}&sort=ASC"
            res = await self.get_internet('requests', url)
            res = res.json()

            curr_articleList = res["articleList"]
            if prev_articleList == curr_articleList:
                break
            for article in curr_articleList:
                subtitles[article["no"]] = article["subtitle"]

            prev_articleList = curr_articleList

        return subtitles

    async def get_title(self, titleid, file_acceptable):
        url = f'{self.BASE_URL}/list?titleId={titleid}'
        title = await self.get_internet(get_type='soup_select_one', url=url,
                                        selector='meta[property="og:title"]')
        title = title['content']
        if file_acceptable:
            title = self.get_safe_file_name(title)
        return title

    async def save_webtoon_thumbnail(self, titleid, title, thumbnail_dir):
        url = f'{self.BASE_URL}/list?titleId={titleid}'
        image_url = await self.get_internet(get_type='soup_select_one', url=url,
                                            selector='meta[property="og:image"]')
        image_url = image_url['content']
        image_extension = self.get_file_extension(image_url)
        image_raw = await self.get_internet(get_type='requests', url=image_url)
        image_raw = image_raw.content
        image_path = thumbnail_dir / f'{title}.{image_extension}'
        image_path.write_bytes(image_raw)

    async def get_all_episode_no(self, titleid):
        subtitles = await self._get_webtoon_data(titleid)
        return list(subtitles)

    async def get_subtitle(self, titleid, episode_no, file_acceptable):
        subtitles = await self._get_webtoon_data(titleid)
        subtitle = subtitles[episode_no]

        return self.get_safe_file_name(subtitle) if file_acceptable else subtitle

    async def get_episode_images_url(self, titleid, episode_no):
        # sourcery skip: de-morgan
        url = f'{self.BASE_URL}/detail?titleId={titleid}&no={episode_no}'
        episode_images_url = await self.get_internet(get_type='soup_select', url=url,
                                                     selector=self.EPISODE_IMAGES_URL_SELECTOR)
        return [element['src'] for element in episode_images_url if not ('agerate' in element['src'] or 'ctguide' in element['src'])]


if __name__ == '__main__':
    wt = NaverWebtoonScraper()
    wt.download_one_webtoon(809590)  # 이번 생

    # # get_internet test(Scraper는 abstract class라 직접 실행이 불가해서 대신 사용)
    # import asyncio
    # wt.IS_STABLE_CONNECTION = False
    # asyncio.run(wt.get_internet('requests', 'https://koifoiewofi.com'))
