"""Download Webtoons from Manhwakyung."""

from __future__ import annotations
import time

from async_lru import alru_cache

if __name__ in ("__main__", "F_telescope"):
    from A_scraper import Scraper
else:
    from .A_scraper import Scraper

TitleId = int


class TelescopeScraper(Scraper):
    """작동하지 않음; 만약 나중에 만화경이 웹 서비스를 재게하면 다시 제작할 것."""
    BASE_URL = 'https://www.manhwakyung.com'
    INTERVAL_BETWEEN_EPISODE_DOWNLOAD_SECONDS = 1
    TEST_WEBTOON_ID = 137

    def __init__(self, pbar_independent=False):
        super().__init__(pbar_independent)
        self.set_to_instant_connection()

    @alru_cache(maxsize=4)
    async def fetch_episode_informations(self, titleid):
        XHR_HEADERS = {
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
        seasons = self.requests.get(f'https://api.manhwakyung.com/episodes?titleId={titleid}', headers=XHR_HEADERS).json()
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
        for episode in reversed(episodes):
            subtitle = episode['name']
            episode_no = episode['episodeNumber']
            episode_id = episode['id']
            # episode_infomation[episode_no] = {'subtitle': subtitle, 'episode_id': episode_id}
            subtitles.append(subtitle)
            episode_ids.append(episode_id)

        self.title = title
        self.webtoon_thumbnail = grid_thumbnail_url
        self.episode_titles = subtitles
        self.episode_ids = episode_ids

    # async def get_title(self, titleid):
    #     return await super().get_title(titleid)

    # async def download_webtoon_thumbnail(self, titleid, title, thumbnail_dir):
    #     return await super().download_webtoon_thumbnail(titleid, title, thumbnail_dir)

    # async def get_all_episode_no(self, titleid):
    #     return await super().get_all_episode_no(titleid)

    # async def get_subtitle(self, titleid, episode_no):
    #     time.sleep(1)  # 없으면 작동 안 함.
    #     return await super().get_subtitle(titleid, episode_no)

    async def get_episode_image_urls(self, titleid, episode_no):
        # episode_id: int = (await self.get_webtoon_data(titleid))['episode_ids'][episode_no]
        episode_id: int = self.episode_ids[episode_no]
        response = self.requests.get(f'https://www.manhwakyung.com/episode/{episode_id}')
        elemetents = response.soup_select('#__next > div.css-0.euvlwci0 > div.css-0.ebi66ty0 > div > div > img')
        return [element.get('data-src') for element in elemetents]

    async def check_if_legitimate_webtoon_id(self, titleid: TitleId) -> str | None:
        url = f'https://www.manhwakyung.com/title/{titleid}'
        title = self.requests.get(url).soup_select_one('meta[property="og:title"]',
                                                       no_empty_result=True).get('content')
        assert isinstance(title, str)
        return None if title == "에러 페이지 | 만화경" else title.removesuffix(' | 만화경')
