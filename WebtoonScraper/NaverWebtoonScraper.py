'''Download Webtoons from Naver Webtoon.
'''
from WebtoonScraper.Scraper import Scraper
class NaverWebtoonScraper(Scraper):
    '''Scrape webtoons from Naver Webtoon.'''
    def __init__(self, pbar_independent=False, short_connection=False):
        super().__init__(pbar_independent, short_connection)
        self.BASE_URL = 'https://comic.naver.com/webtoon'
        if not short_connection:
            self.IS_STABLE_CONNECTION = True
        self.EPISODE_IMAGES_URL_SELECTOR = '#sectionContWide > img' # for best challenge

    async def get_title(self, titleid, file_acceptable):
        url = f'{self.BASE_URL}/list?titleId={titleid}'
        title = await self.get_internet(get_type='soup_select_one', url=url,
                                        selector='meta[property="og:title"]')
        title = title['content']
        if file_acceptable:
            title = self.get_acceptable_file_name(title)
        return title

    async def save_webtoon_thumbnail(self, titleid, title, thumbnail_dir):
        url = f'{self.BASE_URL}/list?titleId={titleid}'
        image_url = await self.get_internet(get_type='soup_select_one', url=url,
                                            selector='meta[property="og:image"]')
        image_url = image_url['content']
        image_extension = self.get_file_extension(image_url)
        image_raw = await self.get_internet(get_type='requests', url=image_url)
        image_raw = image_raw.content
        with open(f'{thumbnail_dir}/{title}.{image_extension}', 'wb') as image:
            image.write(image_raw) # write_byte로 변환

    async def get_all_episode_no(self, titleid, attempt):
        selector = '.item > a > div > img'
        for i in range(1, attempt + 1):
            url = f'{self.BASE_URL}/detail?titleId={titleid}&no={i}'
            selected = await self.get_internet(get_type='soup_select', url=url,
                                               selector=selector)
            if selected:
                break
        if not selected:
            raise ConnectionRefusedError('soup is empty. Maybe attempt is too low?')
        return (int(selected_one.get('alt')) for selected_one in selected)

    async def get_subtitle(self, titleid, episode_no, file_acceptable):
        url = f'{self.BASE_URL}/detail?titleId={titleid}&no={episode_no}'
        subtitle = await self.get_internet(get_type='soup_select_one', url=url,
                                            selector='#subTitle_toolbar')
        
        if not subtitle:
            return None
        
        if file_acceptable:
            subtitle = self.get_acceptable_file_name(subtitle.text)
        else:
            subtitle = subtitle.text
        return subtitle
    
    async def get_episode_images_url(self, titleid, episode_no):
        url = f'{self.BASE_URL}/detail?titleId={titleid}&no={episode_no}'
        episode_images_url = await self.get_internet(get_type='soup_select', url=url,
                                            selector=self.EPISODE_IMAGES_URL_SELECTOR)
        return [element['src'] for element in episode_images_url if not ('agerate' in element['src'] or 'ctguide' in element['src'])]
    
if __name__ == '__main__':
    wt = NaverWebtoonScraper()
    wt.download_one_webtoon(809590)