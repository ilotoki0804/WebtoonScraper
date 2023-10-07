'''Download Webtoons from Lezhin Comics.'''

from __future__ import annotations
import logging
from pathlib import Path
import re
import json
from json import JSONDecodeError
import shutil
from typing import ClassVar
import itertools

from typing_extensions import override

from ..exceptions import UseFetchEpisode

if __name__ in ("__main__", "J_lezhin_comics"):
    from A_scraper import Scraper, force_reload_if_reload
    from J_lezhin_unshuffler import unshuffle_typical_webtoon_directory_and_return_target_directory
else:
    from .A_scraper import Scraper, force_reload_if_reload
    from .J_lezhin_unshuffler import unshuffle_typical_webtoon_directory_and_return_target_directory

TitleId = str


class LezhinComicsScraper(Scraper[str]):
    '''Scrape webtoons from Lezhin Comics.'''
    BASE_URL = 'https://www.lezhin.com/ko/comic'
    TEST_WEBTOON_ID = 'noway'
    TEST_WEBTOON_ID_SHUFFLED: ClassVar[str] = 'brianoslab'
    IS_CONNECTION_STABLE = True

    @override
    def __init__(self, webtoon_id: str, authkey: str | None = None) -> None:
        super().__init__(webtoon_id)
        self.headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "ko,en-US;q=0.9,en;q=0.8",
            # "Authorization": self.AUTHORIZATION,
            "Cache-Control": "no-cache",
            # "Cookie": self.cookie,
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
        self.cookie: str = ''
        self.authkey = authkey or ''

        self.do_not_unshuffle = False
        self.delete_shuffled_file = False
        self.download_episode_id_ints_if_shuffled = True
        self.get_paid_episode = False

        # self.authkey 설정에서 되기 때문에 굳이 하지는 않아도 됨.
        self.update_requests()

    @property
    def authkey(self) -> str:
        return self._authkey

    @authkey.setter
    def authkey(self, value: str) -> None:
        """구현상의 이유로 header는 authkey보다 더 먼저 구현되어야 합니다."""
        self._authkey = value
        self.headers['Authorization'] = value
        self.update_requests()

    @override
    def get_webtoon_directory_name(self) -> str:
        return (f'{self.get_safe_file_name(self.title)}({self.webtoon_id}, shuffled)'
                if self.is_shuffled else f'{self.get_safe_file_name(self.title)}({self.webtoon_id})')

    @force_reload_if_reload
    @override
    def fetch_webtoon_information(self) -> None:
        # 웹툰에 대한 정보를 알고 싶을 때도 호출되어서 성가실 수 있으니 주의.
        # logging.warning('Without setting authkey extremely limiting the range of downloadable episodes. '
        #                 'Please set authkey to valid download. '
        #                 'The tutoral is avilable in https://github.com/ilotoki0804/WebtoonScraper#레진코믹스-다운로드하기')
        raise UseFetchEpisode()

    @force_reload_if_reload
    @override
    def fetch_episode_informations(self) -> None:
        """Default titleid is titleid_str, and default episode_id is episode_id_str, which is displayed to users."""
        res = self.requests.get(f'{self.BASE_URL}/{self.webtoon_id}')
        if res.soup_select_one('meta[property="og:title"]', no_empty_result=True).content == "404 - 레진코믹스":
            raise ValueError(f'Invalid {self.webtoon_id = }')

        title = res.soup_select_one("h2.comicInfo__title", no_empty_result=True).text
        thumbnail_url = res.soup_select_one('meta[property="og:image"]', no_empty_result=True).get("content")
        assert isinstance(thumbnail_url, str), f'Invalid {thumbnail_url = }.'

        webtoon_raw_data = res.soup_select('script')[5]
        assert "src" not in webtoon_raw_data.attrs, f'Invalid {self.webtoon_id = }.'

        try:
            product_start = re.search(r"__LZ_PRODUCT__ *= *{\n *productType: *'comic',\n *product: *", webtoon_raw_data.text).end()  # type: ignore
            product_end, departure_start = re.search(",\n *departure: *'',\n *all: *", webtoon_raw_data.text).span()  # type: ignore
            departure_end = re.search(",\n *prefree", webtoon_raw_data.text).start()  # type: ignore

            product = json.loads(webtoon_raw_data.text[product_start:product_end])

            # # departure는 product["episodes"]와 완전히 같기 때문에 굳이 사용할 이유가 없다.
            # departure = json.loads(webtoon_raw_data.text[departure_start:departure_end])
        except (AttributeError, JSONDecodeError) as e:
            raise ValueError("JavaScript cannot be parsed with regex; because it's not regular language. "
                             "But sometimes, people have to compromise with effeciency and hope it does not break. "
                             "That's why this failed. call developer to fix this problem.") from e

        # webtoon 정보를 받아옴.
        title = product["display"]["title"]
        # webtoon_id_str = product["alias"]  # webtoon_id가 바로 이것이라 필요없음.
        webtoon_int_id = product["id"]
        # is_adult = product["isAdult"]
        if "metadata" in product:
            metadata = product["metadata"]
            is_shuffled = metadata["imageShuffle"] if "imageShuffle" in metadata else False
        else:
            is_shuffled = False

        # departure는 product['episodes']와 동일하기에 product['episodes']를 사용해도 무관하다.
        self.get_episode_informations_from_json_data(product["episodes"])

        # webtoon infomation
        self.webtoon_thumbnail = thumbnail_url
        self.title = title

        # 기타 레진 한정 정보들
        self.is_shuffled = is_shuffled
        self.webtoon_int_id = webtoon_int_id

    def get_episode_informations_from_json_data(
        self,
        episode_informations_raw: list[dict],
        get_paid_episode: bool | None = None,
        get_unusable_episode: bool = False,
    ) -> None:
        get_paid_episode = get_paid_episode if get_paid_episode is not None else self.get_paid_episode
        episode_int_ids: list[int] = []
        episode_str_ids: list[str] = []
        subtitles: list[str] = []
        episode_type_chars: list[str] = []
        display_names: list[str] = []
        is_episode_unusable_list: list[bool] = []
        is_episode_free_list: list[bool] = []
        # for episode in reversed(departure):
        for episode in reversed(episode_informations_raw):
            is_episode_expired = episode["properties"]["expired"]
            is_episode_not_for_sale = episode["properties"]["notForSale"]
            # bool(episode["coin"])도 `"freedAt" in episode` 동일한 역할을 할 것으로 기대된다.
            is_episode_unusable = is_episode_expired or is_episode_not_for_sale
            is_episode_free = "freedAt" in episode

            episode_int_ids.append(episode["id"])
            episode_str_ids.append(episode["name"])
            subtitles.append(episode["display"]["title"])
            episode_type_chars.append(episode["display"]["type"])
            # episode_id_strs와 거의 같지만 특별편인 경우 'x1' 등으로 표시되는 episode_id_strs과는 달리
            # '공지'와 같은 글자로 나타나며 에피소드 위 작은 글씨를 의미한다. 스크래핑과는 큰 관련이 없는 자료이다.
            display_names.append(episode["display"]["displayName"])
            is_episode_unusable_list.append(is_episode_unusable)
            is_episode_free_list.append(is_episode_free)

        lists_to_filter = (episode_int_ids,
                           episode_str_ids,
                           subtitles,
                           episode_type_chars,
                           display_names,
                           is_episode_unusable_list,
                           is_episode_free_list)

        if not get_unusable_episode:
            episode_titles_of_unusables = [episode_title
                                           for episode_title, is_unusable in zip(subtitles, is_episode_unusable_list)
                                           if is_unusable]
            if episode_titles_of_unusables:
                logging.warning('Unusable episode is skipped. Following epsodes will be skipped: '
                                f'{", ".join(episode_titles_of_unusables)}')

                for list_ in lists_to_filter:
                    list_[:] = [i for i, is_unusable in zip(list_, is_episode_unusable_list) if not is_unusable]

        if not get_paid_episode:
            episode_titles_of_not_free = [episode_title
                                          for episode_title, is_free in zip(subtitles, is_episode_free_list)
                                          if not is_free]

            if episode_titles_of_not_free:
                logging.warning('Not for free episode is skipped. Following epsodes will be skipped: '
                                f'{", ".join(episode_titles_of_not_free)}')

                for list_ in lists_to_filter:
                    list_[:] = [i for i, is_free in zip(list_, is_episode_free_list) if is_free]

        # episode infomations
        self.episode_titles = subtitles
        self.episode_ids: list[str] = episode_str_ids
        self.episode_int_ids = episode_int_ids

        # 기타 레진 한정 정보들
        self.information_chars = episode_type_chars

    @override
    def download_webtoon_thumbnail(self, webtoon_directory, file_extension: str | None = 'jpg') -> None:
        super().download_webtoon_thumbnail(webtoon_directory, file_extension=file_extension)
        if self.is_shuffled and self.download_episode_id_ints_if_shuffled:
            self.download_episode_int_ids_as_file(webtoon_directory)

    def download_episode_int_ids_as_file(self, webtoon_directory: Path) -> None:
        if not self.is_episode_informations_loaded:
            self.setup()
        file_content = '\n'.join(map(str, self.episode_int_ids))
        file_path = webtoon_directory / f'{self.webtoon_id}_ids.txt'
        file_path.write_text(file_content, encoding='utf-8')

    @override
    def get_episode_image_urls(self, episode_no, attempts: int = 3) -> list[str] | None:
        # sourcery skip: simplify-fstring-formatting
        episode_id_str = self.episode_ids[episode_no]
        episode_id_int = self.episode_int_ids[episode_no]

        keygen_url = (f"https://www.lezhin.com/lz-api/v2/cloudfront/signed-url/generate?"
                      f"contentId={self.webtoon_int_id}&episodeId={episode_id_int}&purchased={'false'}&q={30}&firstCheckType={'P'}")

        keys_response = self.requests.get(keygen_url)
        if keys_response.status_code == 403:
            if self.authkey:
                logging.warning(f"can't retrieve data from {self.episode_titles[episode_no]}. "
                                "It's probably because Episode is not available or not for free episode. ")
            else:
                logging.warning(f"can't retrieve data from {self.episode_titles[episode_no]}. "
                                "It's almost certainly because you don't have authkey. Set authkey to get data.")
            return None

        response_data = keys_response.json()["data"]
        policy = response_data["Policy"]
        signature = response_data["Signature"]
        key_pair_id = response_data["Key-Pair-Id"]

        images_retrieve_url = ("https://www.lezhin.com/lz-api/v2/inventory_groups/comic_viewer_k?"
                               f"platform=web&store=web&alias={self.webtoon_id}&name={episode_id_str}&preload=false"
                               "&type=comic_episode")
        try:
            images_data = self.requests.get(images_retrieve_url).json()
            # return images_data # for debug purpose
        except json.JSONDecodeError:
            # 가끔씩 실패할 때가 있다. 그냥 requests의 attempts를 올리는 것으로 해결되는지는 불명이다.
            if attempts <= 1:
                raise
            logging.warning('Retrying json decode...')
            return self.get_episode_image_urls(episode_no, attempts=attempts - 1)

        # created_at = images_data["data"]["createdAt"]
        image_urls: list[str] = []
        for image_url_data in images_data["data"]["extra"]["episode"]["scrollsInfo"]:
            image_url = (f'https://rcdn.lezhin.com/v2{image_url_data["path"]}'
                         f'.webp?purchased={"false"}&q={30}&updated={1587628135437}'
                         f'&Policy={policy}&Signature={signature}&Key-Pair-Id={key_pair_id}')
            image_urls.append(image_url)

        return image_urls

    @override
    def unshuffle_lezhin_webtoon(self, base_webtoon_directory: Path) -> Path:
        """For lezhin's shuffle process. This function changes webtoon_directory to unshuffled webtoon's directory."""
        if not self.is_shuffled or self.do_not_unshuffle:
            if self.is_shuffled:
                logging.warning("This webtoon is shuffled, but because self.do_not_unshuffle is set to True, webtoon won't be shuffled.")
            return base_webtoon_directory

        target_webtoon_directory = unshuffle_typical_webtoon_directory_and_return_target_directory(base_webtoon_directory, self.episode_int_ids)
        if self.delete_shuffled_file:
            shutil.rmtree(base_webtoon_directory)
            print('Shuffled webtoon directory is deleted.')
        return target_webtoon_directory

    @override
    def check_if_legitimate_webtoon_id(self) -> str | None:
        try:
            title = self.requests.get(f'https://www.lezhin.com/ko/comic/{self.webtoon_id}').soup_select_one(
                'h2.comicInfo__title')
        except Exception:
            return None
        return title.text if title else None
