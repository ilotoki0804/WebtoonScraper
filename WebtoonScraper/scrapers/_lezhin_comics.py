from __future__ import annotations

import json
import os
import random
import re
import shutil
from contextlib import suppress
import urllib.parse
from pathlib import Path

from httpx import HTTPStatusError

from ..base import logger
from ..exceptions import (
    InvalidAuthenticationError,
    InvalidWebtoonIdError,
    UnsupportedRatingError,
    UseFetchEpisode,
)
from ._scraper import Scraper, async_reload_manager


class LezhinComicsScraper(Scraper[str]):
    """Scrape webtoons from Lezhin Comics.

    ## 추가적인 속성(attribute) 설명
        self.do_not_unshuffle (bool): True일 경우 unshuffle을 하지 **않습니다.** 기본값은 False입니다.
        self.delete_shuffled_file (bool): unshuffling이 끝난 후 unshuffle된 파일을 제거합니다. 기본값은 False입니다.
        self.get_paid_episode (bool): True일 경우 자신이 소장하고 있는 유료 회차도 다운로드받습니다.
            True로 설정할 경우 다량의 경고 메시지가 나올 수 있으나 무시하시면 됩니다. 기본값은 False입니다.
        self.is_fhd_downloaded (bool | None): None이면 HD 다운로드가 된 에피소드가 있어도 `HD`가 붙지 않습니다.
    """

    PLATFORM = "lezhin_comics"
    information_vars = Scraper.information_vars | Scraper._build_information_dict(
        "is_shuffled",
        "webtoon_int_id",
        "episode_int_ids",
        "is_adult",
        shuffled_directory="_shuffled_directory",
        unshuffled_directory="_unshuffled_directory",
    ) | Scraper._build_information_dict(
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
    ) | Scraper._build_information_dict(
        "bearer",
        "user_int_id",
        subcategory="credentials",
    )
    DEFAULT_COOKIE = "x-lz-locale=ko_KR"

    def __init__(self, webtoon_id: str, /, *, bearer: str | None = None, cookie: str | None = None, user_int_id: int | None = None) -> None:
        """
        * 에피소드를 리스팅만 하고 싶은 경우: webtoon_id만 필요
        * 웹툰을 다운로드하고 싶은 경우: webtoon_id와 bearer가 필요
        * 사용자 정보를 다운로드하고 싶은 경우: webtoon_id와 bearer가 필요
        * 성인 웹툰을 리스팅/다운로드/웹툰의 사용자 정보를 다운로드하고 싶은 경우: 각자 필요한 값에 cookie가 추가로 필요

        bearer와 cookie를 어떻게 얻는지는 문서를 참고하세요.
        """
        # cspell: ignore allowadult
        super().__init__(webtoon_id)
        self.headers.update(
            {
                "Referer": "https://www.lezhin.com/ko/comic/dr_hearthstone/1",
                "X-Lz-Adult": "0",
                "X-Lz-Allowadult": "false",
                "X-Lz-Country": "kr",
                "X-Lz-Locale": "ko-KR",
            }
        )
        # 레진은 매우 느린 플랫폼이기에 시간을 넉넉하게 잡아야 한다.
        self.client.timeout = 50
        self.cookie = cookie or self.DEFAULT_COOKIE
        self.bearer = bearer or os.environ.get("LEZHIN_BEARER", None)
        self.user_int_id = user_int_id

        # 레진코믹스의 설정들
        self.unshuffle: bool = True
        self.delete_shuffled: bool = False
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
        with suppress(InvalidAuthenticationError):
            await self.fetch_user_information(reload=reload)

    def get_webtoon_directory_name(self) -> str:
        directory_name = self._safe_name(f"{self.title}({self.webtoon_id}")
        if self.is_shuffled:
            directory_name += ", shuffled"

        if self.is_fhd_downloaded:
            directory_name += ", HD"

        directory_name += ")"

        return directory_name

    @async_reload_manager
    async def fetch_webtoon_information(self, *, reload: bool = False) -> None:
        raise UseFetchEpisode

    @async_reload_manager
    async def fetch_episode_information(self, *, reload: bool = False) -> None:
        with InvalidWebtoonIdError.redirect_error(self):
            try:
                res = await self.client.get(f"https://www.lezhin.com/ko/comic/{self.webtoon_id}")
            except HTTPStatusError as exc:
                if not exc.response.status_code == 307:
                    raise  # InvalidWebtoonIdError로 넘어가게 함.
                if self.cookie == self.DEFAULT_COOKIE or self.cookie is None:
                    raise UnsupportedRatingError(
                        "Adult webtoon is not available since you don't set cookie. Check docs to how to download."
                    ) from exc
                else:
                    raise UnsupportedRatingError(
                        "The account is not adult authenticated. Thus can not download adult webtoons."
                    ) from exc

        title = res.match("h2").pop().text()

        thumbnail_url = res.single('meta[property="og:image"]').attrs.get("content")
        assert thumbnail_url is not None
        script_string = res.match("script")[-1].text()
        try:
            raw_data = re.match(r"self\.__next_.\.push\(\[\d,(.*)\]\)$", script_string)[1]  # type: ignore
            data_raw = json.loads(json.loads(raw_data)[2:])
            data = data_raw[1][3]["entity"]
        except Exception as exc:
            raise InvalidWebtoonIdError.from_webtoon_id(self.webtoon_id, LezhinComicsScraper) from exc

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
            self.open_free_episode = True

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

        user_int_id = self.user_int_id or random.Random(self.webtoon_id).randrange(5000000000000000, 6000000000000000)
        url = f"https://www.lezhin.com/lz-api/v2/users/{user_int_id}/contents/{self.webtoon_int_id}"
        try:
            res = await self.client.get(url)
        except HTTPStatusError:
            raise InvalidAuthenticationError("Bearer is invalid. Failed to fetch user information.") from None
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

        self.information_vars = self.information_vars | Scraper._build_information_dict(  # type: ignore
            "purchased_episodes",
        ) | Scraper._build_information_dict(
            "is_subscribed",
            "does_get_notifications",
            "is_preferred",
            "viewed_episodes",
            subcategory="extra",
        )

    async def _open_free_episode(self, episode_id_str: str) -> None:
        # 아직 작동하지 않는 관계로 스킵.
        return

        # await asyncio.sleep(1)
        res = await self.client.get(f"https://www.lezhin.com/lz-api/contents/v3/{self.webtoon_id}/episodes/{episode_id_str}?referrerViewType=NORMAL&objectType=comic")
        episode_data = res.json()["data"]
        # 뭔지는 모르지만 항상 False였음
        assert not episode_data["episode"]["isCollected"]
        # N다무 남은 시간. 이 함수에 들어올 때는 0이여야 함.
        remaining_time = episode_data["episode"]["remainingTime"]
        if remaining_time != 0:
            raise ValueError(f"Episode {episode_id_str} is not available yet. Remaining time: {remaining_time}.")

        # expire 시간 등 확인
        await self.client.post("https://www.lezhin.com/lz-api/v2/contents/313/episodes/5933612038356992/timer")
        await self.client.get(f"https://www.lezhin.com/ko/comic/munyeo/{episode_id_str}?_rsc=1fohy")

    async def get_episode_image_urls(self, episode_no, retry: int = 3) -> list[tuple[str, str]] | None:
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
            f"https://www.lezhin.com/lz-api/v2/cloudfront/signed-url/generate?"
            f"q={30}&contentId={self.webtoon_int_id}&episodeId={episode_id_int}&firstCheckType={'T'}&purchased={purchased}"
        )

        keys_response = await self.client.get(keygen_url, raise_for_status=False)
        if keys_response.status_code == 403:
            if self.bearer:
                logger.warning(
                    f"Can't retrieve data from {self.episode_titles[episode_no]}. "
                    "It's probably because Episode is not available or not for free episode. "
                )
            else:
                logger.warning(
                    f"Can't retrieve data from {self.episode_titles[episode_no]}. SET BEARER TO DOWNLOAD PROPERLY."
                )
            return None

        response_data = keys_response.json()["data"]
        policy: str = response_data["Policy"]
        signature: str = response_data["Signature"]
        key_pair_id: str = response_data["Key-Pair-Id"]

        images_retrieve_url = (
            "https://www.lezhin.com/lz-api/v2/inventory_groups/comic_viewer_k?"
            f"platform=web&store=web&alias={self.webtoon_id}&name={episode_id_str}&preload=false"
            "&type=comic_episode"
        )
        for i in range(retry):
            try:
                res = await self.client.get(images_retrieve_url)
                images_data = res.json()
            except json.JSONDecodeError:
                if retry == i + 1:
                    raise
                logger.warning("Retrying...")
            else:
                break

        image_urls: list[tuple[str, str]] = []
        episode_info = images_data["data"]["extra"]["episode"]
        updated_at = episode_info["updatedAt"]
        for image_url_data in episode_info["scrollsInfo"]:
            # .replace("~", "%7E")
            image_url = (
                f'https://rcdn.lezhin.com/v2{image_url_data["path"]}'
                f".webp?purchased={purchased}&q={30}&updated={updated_at}"
                f"&Policy={policy}&Signature={signature}&Key-Pair-Id={key_pair_id}"
            )
            media_type = image_url_data["mediaType"]
            # 경고 이미지 무시 (https://ccdn.lezhin.com/v2/comics/notice_contents/ko_warn_white.webp)
            if "notice_contents" in image_url:
                continue
            image_urls.append((image_url, media_type))

        return image_urls

    # MARK: PROPERTIES

    @property
    def bearer(self) -> str | None:
        return self._bearer

    @bearer.setter
    def bearer(self, value: str | None) -> None:
        """구현상의 이유로 header는 bearer보다 더 먼저 구현되어야 합니다."""
        if value is not None and value and (not value.startswith("Bearer") or value == "Bearer ..."):
            raise InvalidAuthenticationError("Invalid bearer. Please provide valid bearer.")
        self._bearer = value
        if value is not None:
            self.headers.update({"Authorization": value})

    # MARK: PRIVATE METHODS

    @classmethod
    def _from_string(cls, string: str, /, **kwargs):
        return cls(string, **kwargs)

    def _apply_options(self, options: dict[str, str], /) -> None:
        def raw_string_to_boolean(raw_string: str) -> bool:
            """boolean으로 변경합니다.

            `true`나 `false`면 각각 True와 False로 처리하고,
            정수라면 0이면 False, 나머지는 True로 처리합니다.

            그 외의 값은 ValueError를 일으킵니다.
            """
            if raw_string.lower() == "true":
                value = True
            elif raw_string.lower() == "false":
                value = False
            else:
                try:
                    value = bool(int(raw_string))
                except ValueError:
                    raise ValueError(f"Invalid value for boolean: {raw_string}") from None
            return value

        for option, raw_value in options.items():
            option = option.upper().replace("-", "_").strip()
            if option == "UNSHUFFLE":
                self.unshuffle = raw_string_to_boolean(raw_value)
            elif option == "DELETE_SHUFFLED":
                self.delete_shuffled = raw_string_to_boolean(raw_value)
            elif option == "DOWNLOAD_PAID":
                self.download_paid_episode = raw_string_to_boolean(raw_value)
            elif option == "BEARER":
                self.bearer = raw_value
            elif option == "THREAD_NUMBER":
                if self.thread_number:
                    logger.warning(
                        f"Thread number has already been set as {self.thread_number}, "
                        f"but thread_number option overriding that value to {raw_value}."
                    )
                if raw_value.lower() == "default":
                    self.thread_number = None
                else:
                    self.thread_number = int(raw_value)
            elif option == "OPEN_FREE_EPISODE":
                self.open_free_episode = raw_string_to_boolean(raw_value)
            else:
                logger.warning(f"Unknown option for {type(self).__name__}: {option!r}. value: {raw_value!r}")

    @classmethod
    def _extract_webtoon_id(cls, url) -> str | None:
        match url.host, url.parts:
            case "www.lezhin.com", ("/", "ko", "comic", webtoon_id):
                return webtoon_id

    async def _download_image(
        self,
        url_tuple: tuple[str, str],
        /,
        directory: Path,
        name: str,
    ) -> Path:
        if isinstance(url_tuple, str):
            return await super()._download_image(url_tuple, directory, name)

        url, media_type = url_tuple
        if media_type not in ("image/jpeg", "image/gif"):
            logger.warning(f"Unknown media type: {media_type}")
        if media_type.startswith("image"):
            file_extension = media_type.removeprefix("image/")  # TODO: 이거 없이도 잘 작동하는지 확인하고 아니라면 변경하기
        return await super()._download_image(url, directory, name)

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
            (download_unusable_episode or not is_unusable) and (get_paid_episode or is_free)
            for is_unusable, is_free in zip(unusable_episodes, free_episodes, strict=True)
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
        if not self.is_shuffled or not self.unshuffle:
            if self.is_shuffled:
                logger.warning(
                    "This webtoon is shuffled, but since self.unshuffle is set to True, webtoon won't be unshuffled."
                )

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
