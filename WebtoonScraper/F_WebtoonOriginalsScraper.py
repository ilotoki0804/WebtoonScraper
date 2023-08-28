'''Download Webtoons from Webtoon Originals.'''

from __future__ import annotations
from bs4 import BeautifulSoup
from async_lru import alru_cache
from requests_utils.exceptions import EmptyResultError

from WebtoonScraper.C_Scraper import TitleId

if __name__ in ("__main__", "F_WebtoonOriginalsScraper"):
    from C_Scraper import Scraper
else:
    from .C_Scraper import Scraper


class WebtoonOriginalsScraper(Scraper):
    '''Scrape webtoons from Webtoon Originals.'''
    def __init__(self, pbar_independent=False):
        super().__init__(pbar_independent)
        self.BASE_URL = 'https://www.webtoons.com/en/fantasy/watermelon'
        self.IS_STABLE_CONNECTION = False
        self.HEADERS = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36',
            "Referer": "http://www.webtoons.com"
        }

    async def get_title(self, titleid):
        url = f'{self.BASE_URL}/list?title_no={titleid}'
        title = self.requests.get(url).soup_select_one('meta[property="og:title"]', no_empty_result=True).get('content')
        if not isinstance(title, str):
            raise ValueError(f'Title is not string. titleid: {titleid}')
        return title

    @alru_cache(maxsize=4)
    async def get_webtoon_data(self, titleid):
        # getting title_no
        url = f'{self.BASE_URL}/list?title_no={titleid}'
        title_no_tag = self.requests.get(url).soup_select_one('#_listUl > li', no_empty_result=True)
        title_no = int(title_no_tag['data-episode-no'])

        # getting list of titles
        selector = '#_bottomEpisodeList > div.episode_cont > ul > li'
        url = f'{self.BASE_URL}/prologue/viewer?title_no={titleid}&episode_no={title_no}'
        selected = self.requests.get(url).soup_select(selector)

        subtitles = []
        episode_ids = []
        for element in selected:
            episode_no = int(element["data-episode-no"])
            # subtitles[episode_no] = element.select_one("span.subj").text
            subtitles.append(element.select_one("span.subj").text)
            episode_ids.append(episode_no)

        return {'subtitles': subtitles, 'episode_ids': episode_ids}

    async def download_webtoon_thumbnail(self, titleid, title, thumbnail_dir):
        url = f'{self.BASE_URL}/list?title_no={titleid}'
        image_url_original = self.requests.get(url).soup_select_one('meta[property="og:image"]', no_empty_result=True)
        image_url: str = image_url_original['content']
        image_extension = self.get_file_extension(image_url)
        image_raw = self.requests.get(image_url).content
        thumbnail_file = thumbnail_dir / f'{title}.{image_extension}'
        thumbnail_file.write_bytes(image_raw)

    async def save_real_webtoon_thumbnail(self, titleid, title, thumbnail_dir):
        '''save another form of thumbnail.'''
        url = f'{self.BASE_URL}/rss?title_no={titleid}'
        image_url = self.requests.get(url).soup_select_one('channel > image > url', no_empty_result=True).text
        image_extension = self.get_file_extension(image_url)
        image_raw = self.requests.get(image_url).content
        thumbnail_path = thumbnail_dir / f'{title}.{image_extension}'
        thumbnail_path.write_bytes(image_raw)

    async def get_all_episode_no(self, titleid):
        return await super().get_all_episode_no(titleid)

    async def get_subtitle(self, titleid, episode_no):
        return await super().get_subtitle(titleid, episode_no)

    async def get_episode_images_url(self, titleid, episode_no):
        episode_id = await self.episode_no_to_episode_id(titleid, episode_no)
        url = f'{self.BASE_URL}/prologue/viewer?title_no={titleid}&episode_no={episode_id}'
        episode_images_url = self.requests.get(url).soup_select('#_imageList > img')
        return [element['data-url'] for element in episode_images_url]

    async def check_if_legitimate_titleid(self, titleid) -> str | None:
        try:
            return await self.get_title(titleid)
        except EmptyResultError:
            return None

if __name__ == '__main__':
    wt = WebtoonOriginalsScraper()
    wt.download_one_webtoon(5291)  # Wumpus
