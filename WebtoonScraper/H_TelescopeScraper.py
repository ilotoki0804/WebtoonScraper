"""Download Webtoons from Manhwakyung."""
import time

from async_lru import alru_cache

if __name__ in ("__main__", "H_TelescopeScraper"):
    from C_Scraper import Scraper
else:
    from .C_Scraper import Scraper


class TelescopeScraper(Scraper):
    """Scrape webtoons from Manhwakyung."""

    def __init__(self, pbar_independent=False):
        super().__init__(pbar_independent)
        self.BASE_URL = 'https://www.manhwakyung.com'
        self.IS_STABLE_CONNECTION = False
        self.TIMEOUT = 3

    @alru_cache(maxsize=4)
    async def get_webtoon_data(self, titleid):
        XHR_HEADER = {
            "authority": 'api.manhwakyung.com',
            "method": 'GET',
            "path": f'/episodes?titleId={titleid}',
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
        subtitles = []
        episode_ids = []
        for episode in episodes:
            subtitle = episode['name']
            episode_no = episode['episodeNumber']
            episode_id = episode['id']
            # episode_infomation[episode_no] = {'subtitle': subtitle, 'episode_id': episode_id}
            subtitles.append(subtitle)
            episode_ids.append(episode_id)

        # list_thumbnail_url
        return {'title': title, 'webtoon_thumbnail': grid_thumbnail_url, 'subtitles': subtitles[::-1], 'episode_ids': episode_ids[::-1]}

    async def get_title(self, titleid):
        return await super().get_title(titleid)

    async def save_webtoon_thumbnail(self, titleid, title, thumbnail_dir):
        return await super().save_webtoon_thumbnail(titleid, title, thumbnail_dir)

    async def get_all_episode_no(self, titleid):
        return await super().get_all_episode_no(titleid)

    async def get_subtitle(self, titleid, episode_no):
        time.sleep(1)  # 없으면 작동 안 함.
        return await super().get_subtitle(titleid, episode_no)

    async def get_episode_images_url(self, titleid, episode_no):
        # episode_id: int = (await self.get_webtoon_data(titleid))['episode_ids'][episode_no]
        episode_id: int = await self.episode_no_to_episode_id(titleid, episode_no)
        elemetents = await self.get_internet('soup_select', f'https://www.manhwakyung.com/episode/{episode_id}',
                                             '#__next > div.css-0.euvlwci0 > div.css-0.ebi66ty0 > div > div > img')
        return [element.get('data-src') for element in elemetents]


if __name__ == '__main__':
    wt = TelescopeScraper()
    wt.download_one_webtoon(137)  # 물망초
