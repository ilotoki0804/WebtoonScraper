"""Download Webtoons from Kakaopage."""

from __future__ import annotations

import base64
import hashlib
import json
import random
import re
import time
from pathlib import Path
from typing import TYPE_CHECKING
from urllib import parse

from hxsoup import AsyncClient
from hxsoup.exceptions import EmptyResultError

from ..base import logger
from ..exceptions import InvalidURLError, InvalidWebtoonIdError, MissingOptionalDependencyError, UnsupportedRatingError
from ._01_scraper import Scraper, reload_manager

if TYPE_CHECKING:
    from typing import Self

    from Cryptodome.Cipher import AES
else:
    AES = None


def _load_cryptodome():
    global AES
    if AES is None:
        with MissingOptionalDependencyError.importing("pycryptodomex", "kakao_webtoon"):
            from Cryptodome.Cipher import AES
    return AES


class KakaoWebtoonScraper(Scraper[int]):
    """Scrape webtoons from Kakaopage."""

    BASE_URL = "https://webtoon.kakao.com"
    TEST_WEBTOON_ID = 2343  # 부기
    URL_REGEX = re.compile(r"(?:https?:\/\/)?webtoon[.]kakao[.]com\/content\/(?P<seo_id>[^\/]+)\/(?P<webtoon_id>\d+)")
    DEFAULT_IMAGE_FILE_EXTENSION = "webp"
    DOWNLOAD_INTERVAL = 0.5
    PLATFORM = "kakao_webtoon"
    INFORMATION_VARS = Scraper.INFORMATION_VARS | dict(
        seo_ids=None,
        readabilities=None,
        is_adult=None,
    )

    def __init__(self, webtoon_id: int, cookie: str | None = None):
        super().__init__(webtoon_id)

        self._client_id = int(random.random() * 2**32)
        self._timestamp = int(time.time() * 1000)
        chars = [*range(0x30, 0x3A), *range(0x61, 0x7B)]
        self._nonce = "".join(chr(i) for i in random.choices(chars, k=10))
        self._app_id = f"KP.{self._client_id}.{self._timestamp + 1}"

        self.episode_headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "ko",
            "Cache-Control": "no-cache",
            "Cookie": f"theme=dark; _kp_collector={self._app_id}",
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
        self.post_headers = self.episode_headers | {"Content-Type": "application/json;charset=UTF-8"}

        if cookie:
            self.cookie = cookie

    @reload_manager
    def fetch_webtoon_information(self, *, reload: bool = False) -> None:
        self.fetch_episode_information()

        res = self.hxoptions.get(f"https://webtoon.kakao.com/content/{self.webtoon_seo_id}/{self.webtoon_id}")

        try:
            title = res.soup_select_one("#root > main > div > div > div > div > p", True).text
        except EmptyResultError:
            try:
                title = res.soup_select_one('meta[property="og:title"]', True).text.removeprefix(" | 카카오웹툰")
            except EmptyResultError:
                try:
                    json_data = res.soup_select_one("script#__NEXT_DATA__", True).text
                    title = json.loads(json_data)["props"]["initialState"]["content"]["contentMap"].popitem()[1]["title"]
                except Exception as e:
                    logger.error(f"Cannot retrieve webtoon title ({type(e).__name__}). Set webtoon title as `webtoon` and proceed...")
                    title = "webtoon"

        thumbnail_url = res.soup_select_one('meta[property="og:image"]', True).get("content")
        assert isinstance(thumbnail_url, str)

        if self.cookie:
            # 대신 /auth/v1/auth/user/detail?access_token= 도 사용 가능
            res = self.hxoptions.get(
                f"https://gateway-kw.kakao.com/popularity/v1/my-review?episodeId={self.webtoon_id}",
                headers=self.episode_headers,
            )
            self.user_id = res.json()["data"]["userId"]
        else:
            self.user_id = None

        self.title = title
        self.webtoon_thumbnail_url = thumbnail_url

    @reload_manager
    def fetch_episode_information(self, *, reload: bool = False) -> None:
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
                raise InvalidWebtoonIdError(f"Webtoon ID {self.webtoon_id} is invalid for Kakao Webtoon.")
            json_data = res.json()
            webtoon_episodes_data += json_data["data"]["episodes"]
            offset += limit
            is_last = json_data["meta"]["pagination"]["last"]

        episode_ids: list[int] = []
        seo_ids: list[str] = []
        numbers: list[int] = []
        episode_titles: list[str] = []
        readabilities: list[bool] = []
        is_adult: bool = False
        for information in reversed(webtoon_episodes_data):
            episode_ids.append(information["id"])
            seo_ids.append(information["seoId"])
            numbers.append(information["no"])
            episode_titles.append(information["title"])
            readabilities.append(information["readable"])
            is_adult = information["adult"]

        if is_adult and not self.cookie:
            raise UnsupportedRatingError("To download ADULT Kakao webtoon, you need cookie value.") from None

        # `webtoon_seo_id`가 존재하지 않을 경우에만 webtoon_seo_id를 override함.
        # hasattr보다 더 리팩토링하기 좋아 try-except를 사용.
        try:
            self.webtoon_seo_id
        except AttributeError:
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
        self.readabilities = readabilities
        self.is_adult = is_adult

    def get_episode_image_urls(
        self,
        episode_no,
    ) -> list[tuple[str, bytes, bytes]] | None:
        _load_cryptodome()

        episode_id = self.episode_ids[episode_no]
        is_readable = self.readabilities[episode_no]

        if not is_readable:
            return None

        payload = {
            "id": episode_id,
            "type": "AES_CBC_WEBP",
            "nonce": self._nonce,
            "timestamp": str(self._timestamp),
            "download": False,
            "webAppId": self._app_id,
        }

        res = self.hxoptions.post(
            f"https://gateway-kw.kakao.com/episode/v1/views/viewer/episodes/{episode_id}/media-resources",
            headers=self.post_headers,
            json=payload,
        )
        data = res.json()["data"]

        aid = data["media"]["aid"]
        zid = data["media"]["zid"]
        key, iv = self._get_decrypt_information(episode_id, aid, zid)

        return [(i["url"], key, iv) for i in data["media"]["files"]]

    @classmethod
    def _decrypt(cls, data: bytes, key: bytes, iv: bytes) -> bytes:
        cipher = AES.new(key, AES.MODE_CBC, iv)
        return cipher.decrypt(data)

    def _get_decrypt_information(self, episode_id, aid: str, zid: str) -> tuple[bytes, bytes]:
        user_id = self.user_id or episode_id

        temp_key = hashlib.sha256(f"{user_id}{episode_id}{self._timestamp}".encode()).digest()
        temp_iv = hashlib.sha256(f"{self._nonce}{self._timestamp}".encode()).digest()[:16]
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
        return super().check_if_legitimate_webtoon_id((InvalidWebtoonIdError, UnsupportedRatingError))

    @classmethod
    def from_url(cls, url: str, cookie: str | None = None) -> Self:
        matched = cls.URL_REGEX.match(url)
        if matched is None:
            raise InvalidURLError.from_url(url, cls)

        try:
            webtoon_id: int = cls._get_webtoon_id_from_matched_url(matched)
            seo_id: str = matched.group("seo_id")
        except Exception as e:
            raise InvalidURLError.from_url(url, cls) from e

        self = cls(webtoon_id, cookie)
        self.webtoon_seo_id = parse.unquote(seo_id)
        return self

    @property
    def cookie(self) -> str | None:
        """브라우저에서 값을 확인할 수 있는 쿠키 값입니다. 로그인 등에서 이용됩니다."""
        try:
            return self.headers["Cookie"]
        except KeyError:
            return None

    @cookie.setter
    def cookie(self, cookie: str) -> None:
        app_id = re.search(r"(?<=_kp_collector=)KP\.\d+\.\d+(?=;)", cookie)
        if app_id is None:
            raise ValueError("Not appropriate cookie. Cookie should have _kp_collector.")
        self._app_id = app_id[0]
        post_cookie = re.sub(r"__T_=[^;]*|; *__T_=[^;]*|__T_=[^;]*;", "", cookie)
        self.headers.update(Cookie=cookie)
        self.post_headers.update(Cookie=post_cookie)
        self.episode_headers.update(Cookie=post_cookie)
