'''Download Webtoons from Webtoon Originals.
'''
from WebtoonScraper.Scraper import Scraper

from bs4 import BeautifulSoup as bs
class WebtoonOriginalsScraper(Scraper):
    '''Scrape webtoons from Webtoon Originals.'''
    def __init__(self, pbar_independent=False, short_connection=False):
        super().__init__(pbar_independent, short_connection)
        self.BASE_URL = 'https://www.webtoons.com/en/fantasy/watermelon'
        self.IS_STABLE_CONNECTION = False
        self.USER_AGENT = {
            'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36',
            "Referer": "http://www.webtoons.com"
        }

    async def get_title(self, titleid, file_acceptable):
        url = f'{self.BASE_URL}/list?title_no={titleid}'
        title = await self.get_internet(get_type='soup_select_one', url=url,
                                        selector='meta[property="og:title"]')
        title = title['content']
        if file_acceptable:
            title = self.get_acceptable_file_name(title)
        return title

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
        thumbnail_file = thumbnail_dir / f'{title}.{image_extension}'
        thumbnail_file.write_bytes(image_raw)

    async def get_all_episode_no(self, titleid, attempt):
        selector = '#_bottomEpisodeList > div.episode_cont > ul > li'
        for i in range(1, attempt + 1):
            url = f'{self.BASE_URL}/prologue/viewer?title_no={titleid}&episode_no={1}'
            selected = await self.get_internet(get_type='soup_select', url=url,
                                               selector=selector)
            if selected:
                break
        if not selected:
            raise ConnectionRefusedError('soup is empty. Maybe attempt is too low?')
        return (int(selected_one.get('data-episode-no')) for selected_one in selected)

    async def get_subtitle(self, titleid, episode_no, file_acceptable):
        url = f'{self.BASE_URL}/prologue/viewer?title_no={titleid}&episode_no={episode_no}'
        subtitle = await self.get_internet(get_type='soup_select_one', url=url,
                                            selector='#toolbar > div.info > div > h1')
        
        if not subtitle:
            return None
        
        if file_acceptable:
            subtitle = self.get_acceptable_file_name(subtitle.text)
        else:
            subtitle = subtitle.text
        return subtitle
    
    async def get_episode_images_url(self, titleid, episode_no):
        url =  f'{self.BASE_URL}/prologue/viewer?title_no={titleid}&episode_no={episode_no}'
        episode_images_url = await self.get_internet(get_type='soup_select', url=url,
                                            selector='#_imageList > img')
        return [element['data-url'] for element in episode_images_url if not ('agerate' in element['src'] or 'ctguide' in element['src'])]

if __name__ == '__main__':
    wt = WebtoonOriginalsScraper()
    wt.download_one_webtoon(5384)