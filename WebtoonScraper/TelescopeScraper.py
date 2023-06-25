'''Download Webtoons from Manhwakyung.
'''
from WebtoonScraper.Scraper import Scraper

import time

class TelescopeScraper(Scraper):
    '''Scrape webtoons from Manhwakyung.'''
    def __init__(self, pbar_independent=False, short_connection=False):
        super().__init__(pbar_independent, short_connection)
        self.BASE_URL = 'https://www.manhwakyung.com'
        self.IS_STABLE_CONNECTION = False
        self.TIMEOUT = 3

    async def download_one_webtoon_async(self, titleid, episode_no_range: tuple|int|None=None):
        self.title, self.list_thumbnail_url, self.grid_thumbnail_url, self.episode_infomation = await self._get_episode_infomation(titleid)
        # return await super().download_one_webtoon_async(titleid, episode_no_range)
        await super().download_one_webtoon_async(titleid, episode_no_range)

    async def _get_episode_infomation(self, titleid):
        XHR_HEADER = {
            "authority": 'api.manhwakyung.com',
            "method": 'GET',
            "path": '/episodes?titleId=180',
            "scheme": 'https',
            "accept": 'application/json, text/plain, */*',
            "accept-encoding": 'gzip, deflate, br',
            "accept-language": 'ko,en-US;q=0.9,en;q=0.8',
            "dnt": '1',
            "main-domain": 'MANHWAKYUNG',
            "origin": 'https://www.manhwakyung.com',
            "referer": 'https://www.manhwakyung.com/',
            "sec-ch-ua": '"Microsoft Edge";v="113", "Chromium";v="113", "Not-A.Brand";v="24"',
            "sec-ch-ua-mobile": '?0',
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": 'empty',
            "sec-fetch-mode": 'cors',
            "sec-fetch-site": 'same-site',
            "sec-gpc": '1',
            "user-agent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36 Edg/113.0.1774.57',
            "version": '3'
        }
        seasons = await self.get_internet('requests', f'https://api.manhwakyung.com/episodes?titleId={titleid}', headers=XHR_HEADER)
        seasons = seasons.json()
        episodes = []
        for season in seasons['seasons']:
            episodes += season['episodes']

        # about webtoon
        title = episodes[0]['title']['name']
        list_thumbnail_url = episodes[0]['title']['listThumbnailImageUrl']
        grid_thumbnail_url = episodes[0]['title']['gridThumbnailImageUrl']

        # about episode
        episode_infomation = {}
        for episode in episodes:
            subtitle = episode['name']
            episode_no = episode['episodeNumber']
            episode_id = episode['id']
            episode_infomation[episode_no] = {'subtitle': subtitle, 'episode_id': episode_id}
            
        return title, list_thumbnail_url, grid_thumbnail_url, episode_infomation

    async def get_title(self, titleid, file_acceptable):
        return self.title

    async def save_webtoon_thumbnail(self, titleid, title, thumbnail_dir):
        image_url = self.grid_thumbnail_url
        image_extension = self.get_file_extension(image_url)
        image_raw = await self.get_internet(get_type='requests', url=image_url)
        image_raw = image_raw.content
        thumbnail_file = thumbnail_dir / f'{title}.{image_extension}'
        thumbnail_file.write_bytes(image_raw)
        # with open(f'{thumbnail_dir}/{title}.{image_extension}', 'wb') as image:
        #     image.write(image_raw) # write_byte로 변환

    async def get_all_episode_no(self, titleid, attempt):
        return reversed(list(self.episode_infomation))

    async def get_subtitle(self, titleid, episode_no, file_acceptable):
        time.sleep(1)
        subtitle = self.episode_infomation[episode_no]['subtitle']
        if file_acceptable:
            subtitle = self.get_acceptable_file_name(subtitle)
        return subtitle
    
    async def get_episode_images_url(self, titleid, episode_no):
        episode_id = self.episode_infomation[episode_no]['episode_id']
        elemetents = await self.get_internet('soup_select', f'https://www.manhwakyung.com/episode/{episode_id}',
                                             '#__next > div.css-0.euvlwci0 > div.css-0.ebi66ty0 > div > div > img')
        # elemetents = get_soup_from_requests(f'https://www.manhwakyung.com/episode/{episode_id}', '#__next > div.css-0.euvlwci0 > div.css-0.ebi66ty0 > div > div > img') # get_internet으로
        return [element.get('data-src') for element in elemetents]

if __name__ == '__main__':
    # from WebtoonScraper import Webtoon
    import Webtoon
    Webtoon.get_webtoon(146, Webtoon.M)
    