from __future__ import annotations

import json
import os
import random
import re
import shutil
import typing
import urllib.parse
from contextlib import suppress
from pathlib import Path

from httpx import HTTPStatusError

from ..base import logger
from ..exceptions import (
    AuthenticationError,
    RatingError,
    UseFetchEpisode,
    WebtoonIdError,
)
from ._helpers import BearerMixin
from ._scraper import Scraper, async_reload_manager

if not typing.TYPE_CHECKING:
    unshuffle = get_image_order = None


def _load_unshuffler():
    global unshuffle, get_image_order
    if unshuffle is None:
        from ._lezhin_unshuffler import unshuffle_from_image as unshuffle, get_image_order


class LezhinComicsScraper(BearerMixin, Scraper[str]):
    PLATFORM = "lezhin_comics"
    download_interval = 0
    information_vars = (
        Scraper.information_vars
        | Scraper._build_information_dict(
            "is_shuffled",
            "webtoon_int_id",
            "episode_int_ids",
            "is_adult",
            "language_code",
            shuffled_directory="_shuffled_directory",
            unshuffled_directory="_unshuffled_directory",
        )
        | Scraper._build_information_dict(
            "free_episodes",
            "free_dates",
            "published_dates",
            "updated_dates",
            "raw_data",
            "availability",
            "unusable_episodes",
            "episode_dates",
            "episode_states",
            subcategory="extra",
        )
        | Scraper._build_information_dict(
            "bearer",
            "user_int_id",
            subcategory="credentials",
        )
    )
    BASE_URLS = dict(
        ko="https://www.lezhin.com",
        en="https://www.lezhinus.com",
        ja="https://www.lezhin.jp",
    )
    LOCALES = dict(
        ko="ko-KR",
        en="en-US",
        ja="ja-JP",
    )

    def __init__(self, webtoon_id: str | tuple[str, str], /, *, bearer: str | None = None, cookie: str | None = None, user_int_id: int | None = None) -> None:
        """
        * 에피소드를 리스팅만 하고 싶은 경우: webtoon_id만 필요
        * 웹툰을 다운로드하고 싶은 경우: webtoon_id와 bearer가 필요
        * 사용자 정보를 다운로드하고 싶은 경우: webtoon_id와 bearer가 필요
        * 성인 웹툰을 리스팅/다운로드/웹툰의 사용자 정보를 다운로드하고 싶은 경우: 각자 필요한 값에 cookie가 추가로 필요

        bearer와 cookie를 어떻게 얻는지는 문서를 참고하세요.
        """
        # cspell: ignore allowadult

        # webtoon_id가 tuple로 주어질 경우 tuple을 해체해서 language code를 때어냄
        if isinstance(webtoon_id, str):
            language_code = "ko"
        else:
            language_code, webtoon_id = webtoon_id

        self._shuffled_directory = None
        self._unshuffled_directory = None
        self.language_code = language_code
        self.base_url = self.BASE_URLS[language_code]
        referrer = f"{self.base_url}/{self.language_code}/comic/{webtoon_id}"

        super().__init__(webtoon_id)
        extra_headers = {
            "Referer": referrer,
            "X-Lz-Adult": "0",
            "X-Lz-Allowadult": "false",
            "X-Lz-Country": "kr",
            "X-Lz-Locale": self.LOCALES[language_code],
        }
        self.headers.update(extra_headers)
        self.json_headers.update(extra_headers)

        # 레진은 매우 느린 플랫폼이기에 시간을 넉넉하게 잡아야 한다.
        self.client.timeout = 50
        if cookie:
            self.cookie = cookie
        else:
            self.cookie = self.default_cookie
            self._cookie_set = False
        self.bearer = bearer
        self.user_int_id = user_int_id

        # 레진코믹스의 설정들
        self.unshuffle: bool = True
        self.delete_shuffled: bool = False
        self.unshuffle_immediately: bool = True
        self.download_paid_episode: bool = True
        self.download_unusable_episode: bool = False
        # None일 경우 상황에 따라 적절한 값으로 변경될 수 있는 값들
        self.thread_number: int | None = None
        self.is_fhd_downloaded: bool | None = None
        self.open_free_episode: bool | None = None

    async def async_download_webtoon(self, *args, **kwargs):
        await super().async_download_webtoon(*args, **kwargs)
        if self._unshuffled_directory and self._shuffled_directory:
            shutil.copy(
                self._unshuffled_directory / "information.json",
                self._shuffled_directory / "information.json",
            )

    async def fetch_all(self, reload: bool = False) -> None:
        await super().fetch_all(reload)
        with suppress(AuthenticationError):
            await self.fetch_user_information(reload=reload)

    async def _download_episodes(self, download_range, webtoon_directory: Path) -> None:
        if self.is_shuffled and self.unshuffle_immediately:
            _load_unshuffler()
        return await super()._download_episodes(download_range, webtoon_directory)

    def _get_identifier(self) -> str:
        identifier = ""

        if self.language_code == "ko":
            identifier += self.webtoon_id
        else:
            identifier += f"{self.language_code}, {self.webtoon_id}"

        if self.is_shuffled and not self.unshuffle_immediately:
            identifier += ", shuffled"

        if self.is_fhd_downloaded:
            identifier += ", HD"

        return identifier

    @async_reload_manager
    async def fetch_webtoon_information(self, *, reload: bool = False) -> None:
        raise UseFetchEpisode

    @async_reload_manager
    async def fetch_episode_information(self, *, reload: bool = False) -> None:
        with WebtoonIdError.redirect_error(self):
            try:
                res = await self.client.get(f"{self.base_url}/{self.language_code}/comic/{self.webtoon_id}")
            except HTTPStatusError as exc:
                if not exc.response.status_code == 307:
                    raise  # InvalidWebtoonIdError이거나 기타 위로 전파해야 할 오류들

                # 이 아래는 모두 307 Redirect인 경우임
                location = exc.response.headers["Location"]
                if location.startswith("/404"):
                    raise  # InvalidWebtoonIdError로 넘어가게 함.
                elif location.startswith("/ko/content-mode"):
                    if self._cookie_set:
                        raise RatingError("The account is not adult authenticated. Thus can not download adult webtoons.") from exc
                    else:
                        raise RatingError("Adult webtoon is not available since you don't set cookie. Check docs to how to download.") from exc
                elif location.startswith("/api/authentication/refresh-token"):
                    res = await self.client.get(f"{self.base_url}{location}", raise_for_status=False)
                    assert res.has_redirect_location
                    new_location = res.headers["Location"]
                    # https://www.lezhin.com/ko/logout?reason=TOKEN_EXPIRED
                    if "/logout" in new_location:
                        raise AuthenticationError("Cookie have been expired. Please update them.") from exc
                    else:
                        cookie_raw = "; ".join(f"{name}={value}" for name, value in res.cookies.items())
                        logger.warning(f"Cookie have been refreshed. New cookie: {cookie_raw!r}")
                        return await self.fetch_episode_information(reload=True)  # 다시 시도함.
                else:
                    raise  # 그 외의 경우. InvalidWebtoonIdError로 넘어가지만 그 외 알 수 없는 오류일 가능성도 있음.

        title = res.match("h2").pop().text()

        thumbnail_url = res.single('meta[property="og:image"]').attrs.get("content")
        assert thumbnail_url is not None
        script_string = res.match("script")[-1].text()
        try:
            raw_data = re.match(r"self\.__next_.\.push\(\[\d,(.*)\]\)$", script_string)[1]  # type: ignore
            data_raw = json.loads(json.loads(raw_data)[2:])
            data = data_raw[1][3]["entity"]
        except Exception as exc:
            raise WebtoonIdError.from_webtoon_id(self.webtoon_id, LezhinComicsScraper) from exc

        selector = "body > div.lzCntnr > div > div > ul > li > a"  # cspell: ignore Cntnr
        episode_dates: list[str] = []
        episode_states: list[str] = []
        for episode in res.match(selector):
            # *_: 'N시간 후 무료' 요소의 경우 개수가 3개임
            date_element, state_element, *_ = episode.css("a > div > div > div > div")
            episode_dates.append(date_element.text())
            episode_states.append(state_element.text())

        self.episode_dates: list[str] = episode_dates
        self.episode_states: list[str] = episode_states
        if self.open_free_episode is None:
            self.open_free_episode = False

        # webtoon 정보를 받아옴.
        title = data["meta"]["content"]["display"]["title"]
        # webtoon_id_str = product["alias"]  # webtoon_id가 바로 이것이라 필요없음.
        webtoon_int_id = data["meta"]["content"]["id"]
        is_adult = data["meta"]["content"]["isAdult"]
        is_shuffled = data["meta"]["content"].get("metadata", {}).get("imageShuffle", False)
        authors = [author["name"] for author in data["meta"]["content"]["artists"]]
        author = ", ".join(authors)

        self.raw_data = data
        self.webtoon_thumbnail_url = thumbnail_url
        self.title = title
        self.is_shuffled = is_shuffled
        self.webtoon_int_id = webtoon_int_id
        self.is_adult: bool = is_adult
        self.authors: list[str] = authors
        self.author: str = author

        self._parse_episode_information(data["meta"]["episodes"])

    @async_reload_manager
    async def fetch_user_information(self, *, reload: bool = False) -> None:
        await self.fetch_episode_information()
        self.purchased_episodes = [False] * len(self.episode_int_ids)
        return  # FIXME: 현재 작동하지 않는 관계로 스킵

        user_int_id = self.user_int_id or random.Random(self.webtoon_id).randrange(5000000000000000, 6000000000000000)
        url = f"https://www.lezhin.com/lz-api/v2/users/{user_int_id}/contents/{self.webtoon_int_id}"
        try:
            res = await self.client.get(url)
        except HTTPStatusError:
            raise AuthenticationError("Cookie is invalid. Failed to fetch user information.") from None
        data: dict = res.json()["data"]
        view_episodes_set = {int(episode_int_id) for episode_int_id in data["history"] or []}
        purchased_episodes_set = {int(episode_int_id) for episode_int_id in data["purchased"] or []}

        raw_last_viewed_episode = data.get("latestViewedEpisode", 0)
        self.last_viewed_episode_int_id: int | None = int(raw_last_viewed_episode) if raw_last_viewed_episode else None

        # 계정 상태
        self.is_subscribed = data["subscribed"]
        self.does_get_notifications = data["notification"]
        self.is_preferred: bool | None = data["preferred"] if data["preferred"] != "none" else None
        # 에피소드 관련
        self.purchased_episodes = [episode_id in purchased_episodes_set for episode_id in self.episode_int_ids]
        self.viewed_episodes = [episode_id in view_episodes_set for episode_id in self.episode_int_ids]
        if self.is_fhd_downloaded is None:
            self.is_fhd_downloaded = any(self.purchased_episodes)

        self.information_vars = (
            self.information_vars
            | Scraper._build_information_dict(  # type: ignore
                "purchased_episodes",
            )
            | Scraper._build_information_dict(
                "is_subscribed",
                "does_get_notifications",
                "is_preferred",
                "viewed_episodes",
                subcategory="extra",
            )
        )

    async def get_episode_image_urls(self, episode_no: int, retry: int = 3) -> list[tuple[int, str, str]] | None:
        if not self.availability[episode_no]:
            return None

        # cspell: ignore keygen
        is_purchased = self.purchased_episodes[episode_no] if hasattr(self, "purchased_episodes") else False

        purchased = "true" if is_purchased else "false"
        # 스페셜 캐릭터를 포함하고 있는 이상한 웹툰이 있음.  # TODO: 테스트에 포함하기!
        episode_id_str = urllib.parse.quote(self.episode_ids[episode_no])
        episode_id_int = self.episode_int_ids[episode_no]

        if self.open_free_episode and self.episode_states[episode_no] == "무료 공개":
            await self._open_free_episode(episode_id_str)

        keygen_url = (
            f"{self.base_url}/lz-api/v2/cloudfront/signed-url/generate?"
            f"q={30}&contentId={self.webtoon_int_id}&episodeId={episode_id_int}&firstCheckType={'T' if self.language_code == 'ko' else 'F'}&purchased={purchased}"
        )

        keys_response = await self.client.get(keygen_url, raise_for_status=False)
        if keys_response.status_code == 403:
            if self.bearer:
                logger.warning(f"Can't retrieve data from {self.episode_titles[episode_no]}. It's probably because Episode is not available or not for free episode. ")
            else:
                logger.warning(f"Can't retrieve data from {self.episode_titles[episode_no]}. SET COOKIE TO DOWNLOAD PROPERLY.")
            return None

        response_data = keys_response.json()["data"]
        policy: str = response_data["Policy"]
        signature: str = response_data["Signature"]
        key_pair_id: str = response_data["Key-Pair-Id"]

        images_retrieve_url = (
            f"{self.base_url}/lz-api/v2/inventory_groups/{'comic_viewer' if self.language_code == 'ja' else 'comic_viewer_k'}?"
            f"platform=web&store=web&alias={self.webtoon_id}&name={episode_id_str}&preload=false"
            "&type=comic_episode"
        )
        for i in range(retry):
            try:
                res = await self.client.get(images_retrieve_url, headers=self.json_headers)
                images_data = res.json()
            except json.JSONDecodeError:
                if retry == i + 1:
                    raise
                logger.warning("Retrying...")
            else:
                break

        image_urls: list[tuple[int, str, str]] = []
        episode_info = images_data["data"]["extra"]["episode"]
        updated_at = episode_info["updatedAt"]
        # 페이지형 만화는 pagesInfo에 데이터가 있음
        for image_url_data in episode_info.get("scrollsInfo") or episode_info.get("pagesInfo") or []:
            # .replace("~", "%7E")
            image_url = (
                f"https://rcdn.lezhin.com/v2{image_url_data['path']}"
                f".webp?purchased={purchased}&q={30}&updated={updated_at}"
                f"&Policy={policy}&Signature={signature}&Key-Pair-Id={key_pair_id}"
            )
            media_type: str = image_url_data["mediaType"]
            # 경고 이미지 무시 (https://ccdn.lezhin.com/v2/comics/notice_contents/ko_warn_white.webp)
            if "notice_contents" in image_url:
                continue
            image_urls.append((episode_no, image_url, media_type))

        return image_urls

    # MARK: PROPERTIES

    @property
    def default_cookie(self) -> str:
        return f"x-lz-locale={self.LOCALES[self.language_code].replace('-', '_')}"

    # MARK: PRIVATE METHODS

    def _set_cookie(self, value: str) -> None:
        bearer = self._cookie_get(value, "_LZ_AT")
        # _LZ_AT에서 직접 bearer를 추출함
        if bearer is not None:
            self.bearer = f"Bearer {bearer}"
        super()._set_cookie(value)

    @classmethod
    def _from_string(cls, string: str, /, **kwargs):
        return cls(string, **kwargs)

    def _apply_option(self, option: str, value: str) -> None:
        match option:
            case "unshuffle":
                self.unshuffle = self._as_boolean(value)
            case "delete-shuffled":
                self.delete_shuffled = self._as_boolean(value)
            case "unshuffle-immediately":
                self.unshuffle_immediately = self._as_boolean(value)
            case "download-paid":
                self.download_paid_episode = self._as_boolean(value)
            case "bearer":
                self.bearer = value.strip()
            case "open-free-episode":
                self.open_free_episode = self._as_boolean(value)
            case "thread-number":
                if self.thread_number:
                    logger.warning(f"Thread number has already been set as {self.thread_number}, but thread_number option overriding it to {value!r}.")
                if value.strip().lower() == "default":
                    self.thread_number = None
                else:
                    self.thread_number = int(value.strip())
            case _:
                super()._apply_option(option, value)

    @classmethod
    def _extract_webtoon_id(cls, url) -> str | tuple[str, str] | None:
        match url.host, url.parts:
            case "www.lezhin.com" | "www.lezhinus.com" | "www.lezhin.jp", ("/", language_code, "comic", webtoon_id):
                return language_code, webtoon_id

    async def _download_image(
        self,
        url_tuple: tuple[int, str, str],
        /,
        directory: Path,
        name: str,
        episode_no: int | None = None,  # TODO: 이 episode_no를 바탕으로 다른 정보들을 가져오기
    ) -> Path:
        if isinstance(url_tuple, str):
            return await super()._download_image(url_tuple, directory, name)

        episode_no, url, media_type = url_tuple
        if media_type not in ("image/jpeg", "image/gif", "image/png"):
            logger.warning(f"Unknown media type: {media_type}")
        if media_type.startswith("image"):
            file_extension = media_type.removeprefix("image/")  # TODO: 이거 없이도 잘 작동하는지 확인하고 아니라면 변경하기

        if not self.is_shuffled or not self.unshuffle_immediately:
            return await super()._download_image(url, directory, name)

        try:
            response = await self.client.get(url)
            image_raw: bytes = response.content
            image_path = directory / self._safe_name(f"{name}.{file_extension}")
            episode_id_int = self.episode_int_ids[episode_no]
            image_order = get_image_order(episode_id_int)
            unshuffle(image_raw, image_order, image_path, file_extension)
            return image_path
        except Exception as exc:
            exc.add_note(f"Exception occurred when downloading image from {url!r}")
            raise

    def _parse_episode_information(self, episode_information_raw: list[dict]) -> None:
        get_paid_episode = self.download_paid_episode
        download_unusable_episode = self.download_unusable_episode
        episode_int_ids: list[int] = []
        episode_str_ids: list[str] = []
        episode_titles: list[str] = []
        unusable_episodes: list[bool] = []
        free_episodes: list[bool] = []
        free_dates: list[int | None] = []
        published_dates: list[int] = []
        updated_dates: list[int] = []
        for episode in reversed(episode_information_raw):
            is_episode_expired = episode["properties"]["expired"]
            is_episode_not_for_sale = episode["properties"]["notForSale"]
            is_episode_unusable = is_episode_expired or is_episode_not_for_sale
            is_episode_free = "freedAt" in episode

            episode_int_ids.append(episode["id"])
            episode_str_ids.append(episode["name"])
            episode_titles.append(episode["display"]["title"])
            unusable_episodes.append(is_episode_unusable)
            free_episodes.append(is_episode_free)

            free_dates.append(episode.get("freedAt"))
            published_dates.append(episode["publishedAt"])
            updated_dates.append(episode["updatedAt"])

        to_downloads = [
            (download_unusable_episode or not is_unusable) and (get_paid_episode or is_free) for is_unusable, is_free in zip(unusable_episodes, free_episodes, strict=True)
        ]

        self.availability = to_downloads
        self.episode_titles = episode_titles
        self.episode_ids: list[str] = episode_str_ids
        self.episode_int_ids = episode_int_ids
        self.free_episodes = free_episodes
        self.unusable_episodes = unusable_episodes
        self.free_dates = free_dates
        self.published_dates = published_dates
        self.updated_dates = updated_dates

    def _post_process_directory(self, base_webtoon_directory: Path) -> Path:
        if not self.is_shuffled or not self.unshuffle or self.unshuffle_immediately:
            if self.is_shuffled and not self.unshuffle_immediately:
                logger.warning("This webtoon is shuffled, but since self.unshuffle is set to True, webtoon won't be unshuffled.")

            self._shuffled_directory = base_webtoon_directory
            self._unshuffled_directory = None

            return base_webtoon_directory

        from ._lezhin_unshuffler import unshuffle_typical_webtoon

        target_webtoon_directory = unshuffle_typical_webtoon(
            base_webtoon_directory,
            self.episode_int_ids,
            progress=self.progress if self.use_progress_bar else None,
            thread_number=self.thread_number,
        )

        if self.delete_shuffled:
            shutil.rmtree(base_webtoon_directory)
            logger.info("Shuffled webtoon directory is deleted.")
            self._shuffled_directory = None
        else:
            self._shuffled_directory = base_webtoon_directory
        self._unshuffled_directory = target_webtoon_directory

        return target_webtoon_directory

    async def _open_free_episode(self, episode_id_str: str) -> None:
        pass
