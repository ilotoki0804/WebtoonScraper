'''Download Webtoons from Webtoon Originals.
'''
from bs4 import BeautifulSoup as bs
from async_lru import alru_cache

if __name__ in ("__main__", "WebtoonOriginalsScraper"):
    from Scraper import Scraper
else:
    from .Scraper import Scraper


class WebtoonOriginalsScraper(Scraper):
    '''Scrape webtoons from Webtoon Originals.'''
    def __init__(self, pbar_independent=False, short_connection=False):
        super().__init__(pbar_independent, short_connection)
        self.BASE_URL = 'https://www.webtoons.com/en/fantasy/watermelon'
        self.IS_STABLE_CONNECTION = False
        self.USER_AGENT = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36',
            "Referer": "http://www.webtoons.com"
        }

    async def get_title(self, titleid, file_acceptable):
        url = f'{self.BASE_URL}/list?title_no={titleid}'
        title = await self.get_internet(get_type='soup_select_one', url=url,
                                        selector='meta[property="og:title"]')
        title = title['content']
        if file_acceptable:
            title = self.get_safe_file_name(title)
        return title

    @alru_cache(maxsize=4)
    async def _get_webtoon_infomation(self, titleid):
        # getting title_no
        url = f'{self.BASE_URL}/list?title_no={titleid}'
        title_no = await self.get_internet('soup_select_one', url, '#_listUl > li')
        title_no = int(title_no['data-episode-no'])

        # getting list of titles
        selector = '#_bottomEpisodeList > div.episode_cont > ul > li'
        url = f'{self.BASE_URL}/prologue/viewer?title_no={titleid}&episode_no={title_no}'
        selected = await self.get_internet(get_type='soup_select', url=url,
                                           selector=selector)

        subtitles = {}
        for element in selected:
            episode_no = int(element["data-episode-no"])
            subtitles[episode_no] = element.select_one("span.subj").text

        return subtitles

    async def save_webtoon_thumbnail(self, titleid, title, thumbnail_dir):
        url = f'{self.BASE_URL}/list?title_no={titleid}'
        image_url = await self.get_internet(get_type='soup_select_one', url=url,
                                            selector='meta[property="og:image"]')
        image_url = image_url['content']
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
        subtitles = await self._get_webtoon_infomation(titleid)
        return list(subtitles)

    async def get_subtitle(self, titleid, episode_no, file_acceptable):
        subtitles = await self._get_webtoon_infomation(titleid)
        subtitle = subtitles[episode_no]

        return self.get_safe_file_name(subtitle) if file_acceptable else subtitle

    async def get_episode_images_url(self, titleid, episode_no):
        url = f'{self.BASE_URL}/prologue/viewer?title_no={titleid}&episode_no={episode_no}'
        episode_images_url = await self.get_internet(get_type='soup_select', url=url,
                                                     selector='#_imageList > img')
        return [
            element['data-url']
            for element in episode_images_url
            if not ('agerate' in element['src'] or 'ctguide' in element['src'])
        ]

if __name__ == '__main__':
    wt = WebtoonOriginalsScraper()
    wt.download_one_webtoon(5291)  # Wumpus
