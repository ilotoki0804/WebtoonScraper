'''Download Webtoons from Lezhin Comics.'''

from __future__ import annotations
import logging
from pathlib import Path
import os
import re
import json
import shutil
import multiprocessing

from async_lru import alru_cache
import pyjsparser
from PIL import Image

if __name__ in ("__main__", "J_lezhin_comics"):
    from A_scraper import Scraper
    from J_lezhin_unshuffler import unshuffle_typical_webtoon_directory
else:
    from .A_scraper import Scraper
    from .J_lezhin_unshuffler import unshuffle_typical_webtoon_directory

TitleId = str


class LezhinComicsScraper(Scraper):
    '''Scrape webtoons from Lezhin Comics.'''
    def __init__(self, pbar_independent=False):
        super().__init__(pbar_independent)
        self.BASE_URL = 'https://www.lezhin.com/ko/comic'
        self.IS_STABLE_CONNECTION = True
        self.EPISODE_IMAGES_URL_SELECTOR = '#sectionContWide > img'  # for best challenge
        self.COOKIE: str = ''
        self.AUTHORIZATION: str = ''

        self.DO_NOT_UNSHUFFLE = False
        self.DELETE_SHUFFLED_FILE = False

    async def get_webtoon_dir_name(self, titleid, title: str) -> str:
        is_shuffled = (await self.get_webtoon_data(titleid))['is_shuffled']
        return f'{title}({titleid}, shuffled)' if is_shuffled else f'{title}({titleid})'

    @alru_cache(maxsize=4)
    async def get_webtoon_data(self, titleid: str, get_paid_episode: bool = False, get_unusable_episode: bool = False):
        """Default titleid is titleid_str, and default episode_id is episode_id_str, which is displayed to users."""
        res = self.requests.get(f'{self.BASE_URL}/{titleid}')
        if res.soup_select_one('meta[property="og:title"]', no_empty_result=True).content == "404 - 레진코믹스":
            raise ValueError(f'Invalid {titleid = }')

        title = res.soup_select_one("h2.comicInfo__title", no_empty_result=True).text
        thumbnail_url = res.soup_select_one('meta[property="og:image"]', no_empty_result=True).get("content")

        webtoon_raw_data = res.soup_select('script')[5]

        if "src" in webtoon_raw_data.attrs:
            raise ValueError(f'Invalid {titleid = }.')

        try:
            product_start = re.search(r"__LZ_PRODUCT__ *= *{\n *productType: *'comic',\n *product: *", webtoon_raw_data.text).end()
            product_end, departure_start = re.search(",\n *departure: *'',\n *all: *", webtoon_raw_data.text).span()
            # departure_end = re.search(",\n *prefree", webtoon_raw_data.text).start()

            product = json.loads(webtoon_raw_data.text[product_start:product_end])
            # # departure는 product["episodes"]와 완전히 같기 때문에 굳이 사용할 이유가 없다.
            # departure = json.loads(webtoon_raw_data.text[departure_start:departure_end])
        except (AttributeError, json.JSONDecodeError) as e:
            raise ValueError("JavaScript cannot be parsed by regex; because it's not regular language. "
                             "But sometimes, people have to compromise with effeciency and hope it does not break. "
                             "That's why this failed. call developer to fix this problem "
                             "and Use `old_get_webtoon_data` instead while developer fix this.") from e

        title = product["display"]["title"]
        # titleid_str = product["alias"]
        titleid_int = product["id"]
        # is_adult = product["isAdult"]
        if "metadata" in product:
            metadata = product["metadata"]
            is_shuffled = metadata["imageShuffle"] if "imageShuffle" in metadata else False
        else:
            is_shuffled = False

        # departure는 product['episodes']와 동일하다.
        episode_id_ints: list[int] = []
        episode_id_strs: list[str] = []
        subtitles: list[str] = []
        episode_type_chars: list[str] = []
        display_names: list[str] = []
        # for episode in departure:
        for episode in product["episodes"]:
            # print(episode)
            is_episode_expired = episode["properties"]["expired"]
            is_episode_not_for_sale = episode["properties"]["notForSale"]
            is_episode_free = "freedAt" in episode

            # if is_episode_free == episode["coin"]:
            #     # bool(episode["coin"])도 `"freedAt" in episode` 동일한 역할을 할 것으로 기대된다.
            #     # 가설이 맞는지 확인하고, 어떤 추측이 더 알맞는 방법인지를 확인한다.
            #     # 적당히 확인하고 나서는 없애도 무관하다.
            #     logging.warning(
            #         '`"freedAt" in episode == (not episode["coin"])` turned out to be false.'
            #         "[Developing purpose message]")
            #     logging.warning(f'{is_episode_free = }, {bool(episode["coin"]) = }')

            if (is_episode_expired or is_episode_not_for_sale) and not get_unusable_episode:
                logging.warning(
                    f"episode {episode['display']['title']} is not usable because it's marked as "
                    + "expired." * is_episode_expired
                    + "And it's " * (is_episode_expired and is_episode_not_for_sale)
                    + "not-for-sale." * is_episode_not_for_sale
                )
                continue
            # logging.warning((is_episode_free, get_paid_episode))
            if not is_episode_free and not get_paid_episode:
                logging.warning(
                    f"episode {episode['display']['title']} is not free so it'll be skipped. "
                    "If you want to get data about paid episode too, make parameter "
                    "`get_unusable_episode` to True.")
                continue

            episode_id_ints.append(episode["id"])
            episode_id_strs.append(episode["name"])
            subtitles.append(episode["display"]["title"])
            episode_type_chars.append(episode["display"]["type"])
            # episode_id_strs와 거의 같지만 특별편인 경우 'x1' 등으로 표시되는 episode_id_strs과는 달리
            # '공지'와 같은 글자로 나타나며 에피소드 위 작은 글씨를 의미한다. 스크래핑과는 큰 관련이 없는 자료이다.
            display_names.append(episode["display"]["displayName"])

            # episode_ids[::-1], episode_id_strs[::-1], subtitles[::-1], episode_type_chars[::-1], display_names[::-1]
            # title, titleid_str, titleid_int, is_adult, is_shuffled

        return {'title': title, 'webtoon_thumbnail': thumbnail_url,
                'episode_ids': episode_id_strs[::-1], 'subtitles': subtitles[::-1],
                'episode_id_ints': episode_id_ints[::-1], 'infomation_chars': episode_type_chars[::-1],
                'titleid_str': titleid, 'titleid_int': titleid_int, 'is_shuffled': is_shuffled, }

    async def get_title(self, titleid):
        return await super().get_title(titleid)

    async def download_webtoon_thumbnail(self, titleid, title, thumbnail_dir):
        return await super().download_webtoon_thumbnail(titleid, title, thumbnail_dir, default_file_extension='jpg')

    async def get_all_episode_no(self, titleid):
        return await super().get_all_episode_no(titleid)

    async def get_subtitle(self, titleid, episode_no):
        return await super().get_subtitle(titleid, episode_no)

    async def get_episode_images_url(self, titleid, episode_no, _attempt: int = 1):
        # sourcery skip: simplify-fstring-formatting
        HEADERS = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "ko,en-US;q=0.9,en;q=0.8",
            "Authorization": self.AUTHORIZATION,
            "Cache-Control": "no-cache",
            "Cookie": self.COOKIE,
            "Dnt": "1",
            "Referer": "https://www.lezhin.com/ko/comic/revatoon/x1",
            "Sec-Ch-Ua": '"Not.A/Brand";v="8", "Chromium";v="114", "Microsoft Edge";v="114"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Gpc": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.82",
            "X-Lz-Adult": "0",
            "X-Lz-Allowadult": "false",
            "X-Lz-Country": "kr",
            "X-Lz-Locale": "ko-KR",
        }
        episode_id_str = (await self.get_webtoon_data(titleid))['episode_ids'][episode_no]
        episode_id_int = (await self.get_webtoon_data(titleid))['episode_id_ints'][episode_no]
        titleid_int = (await self.get_webtoon_data(titleid))['titleid_int']

        keygen_url = (f"https://www.lezhin.com/lz-api/v2/cloudfront/signed-url/generate?"
                      f"contentId={titleid_int}&episodeId={episode_id_int}&purchased={'false'}&q={30}&firstCheckType={'P'}")

        keys_res = self.requests.get(keygen_url, headers=HEADERS)
        if keys_res.status_code == 403:
            logging.warning(f"can't retrieve data from {episode_id_int = }. "
                            "It's probably because Episode is not available or not for free episode.")
            return

        res_json = keys_res.json()["data"]
        lz_policy = res_json["Policy"]
        lz_signature = res_json["Signature"]
        lz_key_pair_id = res_json["Key-Pair-Id"]

        images_retrieve_url = ("https://www.lezhin.com/lz-api/v2/inventory_groups/comic_viewer_k?"
                               f"platform=web&store=web&alias={titleid}&name={episode_id_str}&preload=false"
                               "&type=comic_episode")
        try:
            images_data = self.requests.get(images_retrieve_url, headers=HEADERS).json()
            # return images_data # for debug purpose
        except json.JSONDecodeError:
            if _attempt >= 3:
                raise
            logging.warning('Retrying json decode...')
            return await self.get_episode_images_url(titleid, episode_no, _attempt=_attempt + 1)
        # print(images_data)

        # created_at = images_data["data"]["createdAt"]
        image_urls = []
        for image_url_data in images_data["data"]["extra"]["episode"]["scrollsInfo"]:
            image_url = (f'https://rcdn.lezhin.com/v2{image_url_data["path"]}'
                         f'.webp?purchased={"false"}&q={30}&updated={1587628135437}'
                         f'&Policy={lz_policy}&Signature={lz_signature}&Key-Pair-Id={lz_key_pair_id}')
            image_urls.append(image_url)

        return image_urls

    async def unshuffle_lezhin_webtoon(self, titleid, base_webtoon_dir: Path):
        """For lezhin's shuffle process. This function changes webtoon_dir to unshuffled webtoon's directory."""
        webtoon_data = await self.get_webtoon_data(titleid)
        is_shuffled = webtoon_data['is_shuffled']

        if not is_shuffled or self.DO_NOT_UNSHUFFLE:
            if is_shuffled:
                logging.warning("This webtoon is shuffled, but because self.DO_NOT_UNSHUFFLE is set to True, webtoon won't be shuffled.")
            return base_webtoon_dir

        episode_id_ints = webtoon_data['episode_id_ints']
        target_webtoon_directory = unshuffle_typical_webtoon_directory(base_webtoon_dir, episode_id_ints)
        if self.DELETE_SHUFFLED_FILE:
            shutil.rmtree(base_webtoon_dir)
            print('Shuffled webtoon directory is deleted.')
        return target_webtoon_directory

    async def check_if_legitimate_titleid(self, titleid: TitleId) -> str | None:
        title = self.requests.get(f'https://www.lezhin.com/ko/comic/{titleid}').soup_select_one('h2.comicInfo__title')
        return title.text if title else None


if __name__ == '__main__':
    wt = LezhinComicsScraper()
    wt.download_one_webtoon('revatoon')  # unshuffled
    wt.download_one_webtoon('cartoon_hero')  # shuffled
