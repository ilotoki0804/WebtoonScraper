'''Download Webtoons from Kakaopage.'''

from __future__ import annotations

from async_lru import alru_cache
from requests_utils.exceptions import EmptyResultError

if __name__ in ("__main__", "M_KakaopageWebtoonScraper"):
    from C_Scraper import Scraper
    from M_Kakaopage_queries import WEBTOON_DATA_QUERY, EPISODE_IMAGES_QUERY
else:
    from .C_Scraper import Scraper
    from .M_Kakaopage_queries import WEBTOON_DATA_QUERY, EPISODE_IMAGES_QUERY


class KakaopageWebtoonScraper(Scraper):
    '''Scrape webtoons from Kakaopage.'''
    def __init__(self, pbar_independent=False, cookie: str = ''):
        super().__init__(pbar_independent)
        self.BASE_URL = 'https://page.kakao.com'
        self.IS_STABLE_CONNECTION = False
        self.COOKIE = cookie
        self.HEADERS = {}
        self.GRAPHQL_HEADERS = {
            "Accept": "application/graphql+json, application/json",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "ko,en-US;q=0.9,en;q=0.8",
            "Cache-Control": "no-cache",
            "Content-Length": "4371",
            "Content-Type": "application/json",
            "Cookie": self.COOKIE,
            "Dnt": "1",
            "Origin": "https://page.kakao.com",
            "Pragma": "no-cache",
            "Referer": "https://page.kakao.com/content/53397318/viewer/53486401",
            "Sec-Ch-Ua": '"Not/A)Brand";v="99", "Microsoft Edge";v="115", "Chromium";v="115"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Gpc": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
        }

    @alru_cache(maxsize=4)
    async def get_webtoon_data(self, titleid: int):
        res = self.requests.get(f"https://page.kakao.com/content/{titleid}")
        title = res.soup_select_one('meta[property="og:title"]', no_empty_result=True).get("content")
        thumnail_url = res.soup_select_one('meta[property="og:image"]', no_empty_result=True).get("content")

        query = WEBTOON_DATA_QUERY

        curser = 0
        # episode_length: int = 0
        has_next_page: bool = True
        webtoon_episodes_data = []
        while has_next_page:
            post_data = {
                "operationName": "contentHomeProductList",
                "query": query,
                "variables": {"seriesId": titleid, "after": str(curser), "boughtOnly": False, "sortType": "asc"},
            }

            res = self.requests.post(
                "https://page.kakao.com/graphql",
                json=post_data,
                headers=self.GRAPHQL_HEADERS,
            )

            webtoon_raw_data = res.json()["data"]["contentHomeProductList"]

            # episode_length = webtoon_raw_data["totalCount"]
            has_next_page = webtoon_raw_data["pageInfo"]["hasNextPage"]
            curser = webtoon_raw_data["pageInfo"]["endCursor"]
            webtoon_episodes_data += webtoon_raw_data["edges"]

        # urls: list[str] = []
        episode_ids: list[int] = []
        is_free: list[bool] = []
        subtitles: list[str] = []
        for webtoon_episode_data in webtoon_episodes_data:
            # urls += "https://page.kakao.com/" + raw_url.removeprefix("kakaopage://open/")
            episode_ids.append(webtoon_episode_data["node"]["single"]["productId"])  # 에피소드 id
            is_free.append(webtoon_episode_data["node"]["single"]["isFree"])  # 무료인지 여부
            subtitles.append(webtoon_episode_data["node"]["single"]["title"])

        return {'subtitles': subtitles, 'episode_ids': episode_ids, 'title': title, 'webtoon_thumbnail': thumnail_url}

    async def download_single_image(self, episode_dir, url: str, image_no: int, default_file_extension: str | None = 'jpg') -> None:
        """Download image from url and returns to {episode_dir}/{file_name(translated to accactable name)}."""
        image_extension = self.get_file_extension(url)

        # for Bufftoon
        if image_extension is None:
            if default_file_extension is None:
                raise ValueError('File extension not detected.')
            image_extension = default_file_extension

        file_name = f'{image_no:03d}.{image_extension}'

        # self._set_pbar(f'{episode_dir}|{file_name}')
        # 'headers' is changed.
        image_raw: bytes = (await self.requests.aget(url, headers={})).content

        file_dir = episode_dir / file_name
        file_dir.write_bytes(image_raw)

    async def save_webtoon_thumbnail(self, titleid, title: str, thumbnail_dir, default_file_extension: str | None = 'jpg') -> None:
        return await super().save_webtoon_thumbnail(titleid, title, thumbnail_dir, default_file_extension)

    async def get_episode_images_url(self, titleid, episode_no):
        episode_id = await self.episode_no_to_episode_id(titleid, episode_no)

        query = EPISODE_IMAGES_QUERY

        post_data = {
            "operationName": "viewerInfo",
            "query": query,
            "variables": {"seriesId": titleid, "productId": episode_id},
        }

        res = self.requests.post(
            "https://page.kakao.com/graphql",
            json=post_data,
            headers=self.GRAPHQL_HEADERS,
        ).json()

        return [i['secureUrl']
                for i in res["data"]["viewerInfo"]["viewerData"]["imageDownloadData"]["files"]]

    async def check_if_legitimate_titleid(self, titleid: int) -> str | None:
        res = self.requests.get(f"https://page.kakao.com/content/{titleid}")
        try:
            title = res.soup_select_one('meta[property="og:title"]', no_empty_result=True).get("content")
        except EmptyResultError:
            return None
        if isinstance(title, str):
            return None if title == '카카오페이지' else title


if __name__ == '__main__':
    wt = KakaopageWebtoonScraper()
    wt.download_one_webtoon(53397318)  # 부기
