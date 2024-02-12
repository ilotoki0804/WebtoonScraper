"""Download Webtoons from Kakaopage."""

from __future__ import annotations

import base64
import hashlib
import itertools
import json
import random
import time
from datetime import datetime
from pathlib import Path

from Cryptodome.Cipher import AES
from hxsoup import AsyncClient
from hxsoup.exceptions import EmptyResultError

from WebtoonScraper.miscs import EpisodeNoRange

from ..exceptions import InvalidWebtoonIdError, UnsupportedWebtoonRatingError
from ..miscs import logger
from .A_scraper import Scraper, reload_manager


class KakaoWebtoonScraper(Scraper[int]):
    """Scrape webtoons from Kakaopage."""

    BASE_URL = "https://webtoon.kakao.com"
    IS_CONNECTION_STABLE = True  # 아닐 경우 변경하기
    TEST_WEBTOON_ID = 1180  # 국민
    URL_REGEX = r"(?:https?:\/\/)?webtoon[.]kakao[.]com\/content\/(?P<webtoon_id>\d+)"
    DEFAULT_IMAGE_FILE_EXTENSION = "webp"
    INTERVAL_BETWEEN_EPISODE_DOWNLOAD_SECONDS = 0.5

    def __init__(self, webtoon_id: int):
        super().__init__(webtoon_id)

        self.client_id = int(random.random() * 2**32)
        self.timestamp = int(time.time() * 1000)  # time.time을 사용할 수도 있음.
        chars = [*range(0x30, 0x3A), *range(0x61, 0x7B)]
        self.nonce = "".join(chr(i) for i in random.choices(chars, k=10))
        self.app_id = f"KP.{self.client_id}.{self.timestamp + 1}"

        self.post_headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "ko",
            "Cache-Control": "no-cache",
            "Content-Type": "application/json;charset=UTF-8",
            "Cookie": f"theme=dark; _kp_collector={self.app_id}",
            "Dnt": "1",
            "Origin": "https://webtoon.kakao.com",
            "Pragma": "no-cache",
            "Referer": "https://webtoon.kakao.com/",
            "Sec-Ch-Ua": '"Not A(Brand";v="99", "Microsoft Edge";v="121", "Chromium";v="121"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "Sec-Gpc": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        }
        self.episode_headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "ko",
            "Cache-Control": "no-cache",
            "Cookie": f"theme=dark; _kp_collector={self.app_id}",
            "Dnt": "1",
            "Origin": "https://webtoon.kakao.com",
            "Pragma": "no-cache",
            "Referer": "https://webtoon.kakao.com/",
            "Sec-Ch-Ua": '"Not A(Brand";v="99", "Microsoft Edge";v="121", "Chromium";v="121"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "Sec-Gpc": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        }

    @reload_manager
    def fetch_webtoon_information(self, *, reload: bool = False) -> None:
        self.fetch_episode_informations()

        res = self.hxoptions.get(
            f"https://webtoon.kakao.com/content/{self.webtoon_seo_id}/{self.webtoon_id}"
        )

        try:
            title = res.soup_select_one(
                "#root > main > div > div > div > div > p", True
            ).text
        except EmptyResultError:
            title = res.soup_select_one(
                'meta[property="og:title"]', True
            ).text.removeprefix(" | 카카오웹툰")

        thumnail_url = res.soup_select_one('meta[property="og:image"]', True).get(
            "content"
        )
        assert isinstance(thumnail_url, str)

        self.title = title
        self.webtoon_thumbnail_url = thumnail_url

    @reload_manager
    def fetch_episode_informations(self, *, reload: bool = False) -> None:
        offset = 0
        limit = 30
        is_last: bool = False
        webtoon_episodes_data = []
        while not is_last:
            res = self.hxoptions.get(
                f"https://gateway-kw.kakao.com/episode/v2/views/content-home/contents/{self.webtoon_id}/episodes"
                f"?sort=-NO&offset={offset}&limit={limit}",
                headers=self.episode_headers,
            )
            if res.status_code == 404:
                raise InvalidWebtoonIdError(
                    f"Webtoon ID {self.webtoon_id} is invalid for Kakao Webtoon."
                )
            webtoon_episodes_data += res.json()["data"]["episodes"]
            offset += limit
            is_last = res.json()["meta"]["pagination"]["last"]

        episode_ids: list[int] = []
        seo_ids: list[str] = []
        numbers: list[int] = []
        episode_titles: list[str] = []
        readablities: list[bool] = []
        is_adult: bool = False
        for informations in reversed(webtoon_episodes_data):
            episode_ids.append(informations["id"])
            seo_ids.append(informations["seoId"])
            numbers.append(informations["no"])
            episode_titles.append(informations["title"])
            readablities.append(informations["readable"])
            is_adult = informations["adult"]

        if is_adult:
            raise UnsupportedWebtoonRatingError("Adult webtoon is not supported.")

        try:
            inferred_webtoon_seo_id = seo_ids[0][:-4]
        except IndexError:
            logger.warning("SEO ID inferring may not work well.")
            inferred_webtoon_seo_id = "webtoon"
        if seo_ids[0][-4] != "-" or not inferred_webtoon_seo_id:
            logger.warning("SEO ID inferring may not work well.")
        self.webtoon_seo_id = inferred_webtoon_seo_id or "webtoon"

        self.episode_ids = episode_ids
        self.seo_ids = seo_ids
        self.episode_titles = episode_titles
        self.readablities = readablities
        self.is_adult = is_adult

    def get_episode_image_urls(
        self,
        episode_no,
    ) -> list[tuple[str, bytes, bytes]] | None:
        episode_id = self.episode_ids[episode_no]
        is_readable = self.readablities[episode_no]

        if not is_readable:
            return None

        payload = {
            "id": episode_id,
            "type": "AES_CBC_WEBP",
            "nonce": self.nonce,
            "timestamp": str(self.timestamp),
            "download": False,
            "webAppId": f"KP.{self.client_id}.{self.timestamp + 1}",
        }

        res = self.hxoptions.post(
            f"https://gateway-kw.kakao.com/episode/v1/views/viewer/episodes/{episode_id}/media-resources",
            headers=self.post_headers,
            json=payload,
        )
        data = res.json()["data"]

        aid = data["media"]["aid"]
        zid = data["media"]["zid"]
        key, iv = self._get_decrypt_infomations(episode_id, aid, zid)

        return [(i["url"], key, iv) for i in data["media"]["files"]]

    # async def async_download_webtoon(self, episode_no_range: EpisodeNoRange = None, merge_number: int | None = None, add_viewer: bool = True) -> None:
    #     self.fetch_all()
    #     unreadable_episodes = itertools.compress(self.episode_titles, (not is_readable for is_readable in self.readablities))
    #     logger.warning(f"Unreadable episodes will be skipped: {', '.join(unreadable_episodes)}")
    #     return await super().async_download_webtoon(episode_no_range, merge_number, add_viewer)

    @staticmethod
    def _decrypt(data: bytes, key: bytes, iv: bytes) -> bytes:
        cipher = AES.new(key, AES.MODE_CBC, iv)
        return cipher.decrypt(data)

    def _get_decrypt_infomations(
        self, episode_id, aid: str, zid: str
    ) -> tuple[bytes, bytes]:
        user_id = episode_id

        temp_key = hashlib.sha256(
            bytes(f"{user_id}{episode_id}{self.timestamp}", encoding="utf-8")
        ).digest()
        temp_iv = hashlib.sha256(
            bytes(f"{self.nonce}{self.timestamp}", encoding="utf-8")
        ).digest()[:16]
        encrypted_key = base64.b64decode(aid)
        encrypted_iv = base64.b64decode(zid)

        key = self._decrypt(encrypted_key, temp_key, temp_iv)[:16]
        iv = self._decrypt(encrypted_iv, temp_key, temp_iv)[:16]
        return key, iv

    async def _download_image(
        self,
        episode_directory: Path,
        url: tuple[str, bytes, bytes],
        image_no: int,
        client: AsyncClient,
        *,
        file_extension: str | None = None,
    ) -> None:
        """만약 기존 `_download_image`에 변화가 생길 경우 수정하는 것을 잊지 말 것."""
        real_url, key, iv = url
        file_extension = file_extension or self.DEFAULT_IMAGE_FILE_EXTENSION

        file_name = f"{image_no:03d}.{file_extension}"

        image_raw: bytes = (await client.get(real_url)).content

        file_directory = episode_directory / file_name
        file_directory.write_bytes(self._decrypt(image_raw, key, iv))

    def check_if_legitimate_webtoon_id(self) -> str | None:
        return super().check_if_legitimate_webtoon_id(
            (InvalidWebtoonIdError, UnsupportedWebtoonRatingError)
        )
