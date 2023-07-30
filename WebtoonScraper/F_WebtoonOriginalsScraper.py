'''Download Webtoons from Webtoon Originals.'''

from bs4 import BeautifulSoup as bs
from async_lru import alru_cache

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
        title = await self.get_internet(get_type='soup_select_one', url=url,
                                        selector='meta[property="og:title"]')
        if not title:
            raise ConnectionError('Webtoon Originals changed their api specification. Contect developer to update get_title.')
        return title['content']

    @alru_cache(maxsize=4)
    async def get_webtoon_data(self, titleid):
        # getting title_no
        url = f'{self.BASE_URL}/list?title_no={titleid}'
        title_no_tag = await self.get_internet('soup_select_one', url, '#_listUl > li')
        if not title_no_tag:
            raise ConnectionError('Webtoon Originals changed their api specification. Contect developer to update get_title.')
        title_no = int(title_no_tag['data-episode-no'])

        # getting list of titles
        selector = '#_bottomEpisodeList > div.episode_cont > ul > li'
        url = f'{self.BASE_URL}/prologue/viewer?title_no={titleid}&episode_no={title_no}'
        selected = await self.get_internet(get_type='soup_select', url=url,
                                           selector=selector)

        subtitles = []
        episode_ids = []
        for element in selected:
            episode_no = int(element["data-episode-no"])
            # subtitles[episode_no] = element.select_one("span.subj").text
            subtitles.append(element.select_one("span.subj").text)
            episode_ids.append(episode_no)

        return {'subtitles': subtitles, 'episode_ids': episode_ids}

    async def save_webtoon_thumbnail(self, titleid, title, thumbnail_dir):
        url = f'{self.BASE_URL}/list?title_no={titleid}'
        image_url_original = await self.get_internet(get_type='soup_select_one', url=url,
                                                     selector='meta[property="og:image"]')
        if not image_url_original:
            raise ConnectionError('Webtoon Originals changed their api specification. Contect developer to update get_title.')
        image_url: str = image_url_original['content']
        image_extension = self.get_file_extension(image_url)
        image_raw = await self.get_internet(get_type='requests', url=image_url)
        image_raw = image_raw.content
        thumbnail_file = thumbnail_dir / f'{title}.{image_extension}'
        thumbnail_file.write_bytes(image_raw)

    async def save_real_webtoon_thumbnail(self, titleid, title, thumbnail_dir):
        '''save another form of thumbnail.'''
        url = f'{self.BASE_URL}/rss?title_no={titleid}'
        response = await self.get_internet(get_type='requests', url=url)
        soup = bs(response.text, 'xml')
        image_url = soup.select_one('channel > image > url').text
        image_extension = self.get_file_extension(image_url)
        image_raw = await self.get_internet(get_type='requests', url=image_url)
        image_raw = image_raw.content
        thumbnail_path = thumbnail_dir / f'{title}.{image_extension}'
        thumbnail_path.write_bytes(image_raw)

    async def get_all_episode_no(self, titleid):
        return await super().get_all_episode_no(titleid)

    async def get_subtitle(self, titleid, episode_no):
        return await super().get_subtitle(titleid, episode_no)

    async def get_episode_images_url(self, titleid, episode_no):
        episode_id = await self.episode_no_to_episode_id(titleid, episode_no)
        url = f'{self.BASE_URL}/prologue/viewer?title_no={titleid}&episode_no={episode_id}'
        episode_images_url = await self.get_internet(get_type='soup_select', url=url,
                                                     selector='#_imageList > img')
        return [element['data-url'] for element in episode_images_url]


if __name__ == '__main__':
    wt = WebtoonOriginalsScraper()
    wt.download_one_webtoon(5291)  # Wumpus
