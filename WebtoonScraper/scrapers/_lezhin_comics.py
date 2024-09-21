from __future__ import annotations

import ast
import itertools
import json
import os
import random
import re
import shutil
from contextlib import suppress
import urllib.parse
from json import JSONDecodeError
from pathlib import Path

from hxsoup.client import AsyncClient
from hxsoup.exceptions import EmptyResultError

from ..base import logger
from ..exceptions import (
    InvalidAuthenticationError,
    InvalidWebtoonIdError,
    Unreachable,
    UnsupportedRatingError,
    UseFetchEpisode,
)
from ._scraper import Scraper, reload_manager


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
    DEFAULT_IMAGE_FILE_EXTENSION = "jpg"
    INFORMATION_VARS = Scraper.INFORMATION_VARS | dict(
        is_shuffled=None,
        webtoon_int_id=None,
        episode_int_ids=None,
        information_chars=None,
        free_episodes=None,
        shuffled_webtoon_directory_name=(
            lambda self, _: None
            if self._unshuffled_webtoon_directory is None
            else self._unshuffled_webtoon_directory.name
        ),
        is_adult=None,
        free_dates=None,
        published_dates=None,
        updated_dates=None,
    )
    thread_number: int | None = None
    DEFAULT_COOKIE = "x-lz-locale=ko_KR"
    _unshuffled_webtoon_directory: Path | None = None

    def __init__(self, webtoon_id: str, /, *, bearer: str | None = None, cookie: str | None = None) -> None:
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
        self.hxoptions.update(
            timeout=50,
            attempts=3,
        )
        self.cookie = cookie or self.DEFAULT_COOKIE  # 수정 시에는 중복된 부분도 수정하기
        self.bearer = bearer or os.environ.get("LEZHIN_BEARER", None)
        if self.bearer is not None and bearer and (not bearer.startswith("Bearer") or bearer == "Bearer ..."):
            raise InvalidAuthenticationError("Invalid bearer. Please provide valid bearer.")

        self.unshuffle: bool = True
        self.delete_shuffled: bool = False
        self.download_paid_episode: bool = False
        self.is_fhd_downloaded: bool | None = False
        self.thread_number: int | None = None

    async def async_download_webtoon(self, *args, **kwargs):
        await super().async_download_webtoon(*args, **kwargs)
        if self._unshuffled_webtoon_directory:
            shutil.copy(
                self._unshuffled_webtoon_directory / "information.json",
                self._webtoon_directory / "information.json",
            )

    def fetch_all(self, reload: bool = False) -> None:
        super().fetch_all(reload)
        with suppress(InvalidAuthenticationError):
            self.fetch_user_information(reload=reload)

    def get_webtoon_directory_name(self) -> str:
        directory_name = self._safe_name(f"{self.title}({self.webtoon_id}")
        if self.is_shuffled:
            directory_name += ", shuffled"

        if self.is_fhd_downloaded:
            directory_name += ", HD"

        directory_name += ")"

        return directory_name

    @reload_manager
    def fetch_webtoon_information(self, *, reload: bool = False) -> None:
        raise UseFetchEpisode()

    @reload_manager
    def fetch_episode_information(self, *, reload: bool = False) -> None:
        res = self.hxoptions.get(f"https://www.lezhin.com/ko/comic/{self.webtoon_id}")
        if res.status_code == 404:
            raise InvalidWebtoonIdError.from_webtoon_id(self.webtoon_id, type(self))

        try:
            title = res.soup_select("h2")[-1].text
        except EmptyResultError:
            if self.cookie == self.DEFAULT_COOKIE or self.cookie is None:
                raise UnsupportedRatingError(
                    "Adult webtoon is not available since you don't set cookie. " "Check docs to how to download"
                ) from None
            if "adult" in res.url.path:
                raise UnsupportedRatingError(
                    "The account is not adult authenticated. Thus can not download adult webtoons."
                ) from None

        thumbnail_url = res.soup_select_one('meta[property="og:image"]', no_empty_result=True).get("content")
        assert isinstance(thumbnail_url, str), f"Invalid {thumbnail_url=}."

        script_string = res.soup_select("script")[-1].text
        try:
            raw_data = re.match(r"self\.__next_.\.push\(\[\d,(.*)\]\)$", script_string)[1]  # type: ignore
            data_raw = json.loads(ast.literal_eval(raw_data)[2:])
            data = data_raw[1][3]["entity"]
        except Exception as exc:
            raise InvalidWebtoonIdError.from_webtoon_id(self.webtoon_id, LezhinComicsScraper) from exc

        # webtoon 정보를 받아옴.
        title = data["meta"]["content"]["display"]["title"]
        # webtoon_id_str = product["alias"]  # webtoon_id가 바로 이것이라 필요없음.
        webtoon_int_id = data["meta"]["content"]["id"]
        is_adult = data["meta"]["content"]["isAdult"]
        is_shuffled = data["meta"]["content"].get("metadata", {}).get("imageShuffle", False)
        author = ", ".join(author["name"] for author in data["meta"]["content"]["artists"])

        self._parse_episode_information(data["meta"]["episodes"])

        self.webtoon_thumbnail_url = thumbnail_url
        self.title = title
        self.is_shuffled = is_shuffled
        self.webtoon_int_id = webtoon_int_id
        self.is_adult: bool = is_adult
        self.author: str = author

    @reload_manager
    def fetch_user_information(self, user_int_id: int | None = None, *, reload: bool = False) -> None:
        user_int_id = user_int_id or random.randrange(5000000000000000, 6000000000000000)
        url = f"https://www.lezhin.com/lz-api/v2/users/{user_int_id}/contents/{self.webtoon_int_id}"
        try:
            data = self.hxoptions.get(url).json()
        except JSONDecodeError:
            raise InvalidAuthenticationError("Bearer is invalid. Failed to `fetch_user_infos`.") from None
        if "error" in data:
            raise InvalidAuthenticationError("Bearer is invalid. Failed to `fetch_user_infos`.")
        data: dict = data["data"]
        view_episodes_set = {int(episode_int_id) for episode_int_id in data["history"] or []}
        purchased_episodes_set = {int(episode_int_id) for episode_int_id in data["purchased"] or []}

        raw_last_viewed_episode = data.get("latestViewedEpisode", 0)
        self.last_viewed_episode_int_id: int | None = int(raw_last_viewed_episode) if raw_last_viewed_episode else None

        self.is_subscribed = data["subscribed"]
        self.does_get_notifications = data["notification"]
        self.is_preferred: bool | None = data["preferred"] if data["preferred"] != "none" else None

        self.purchased_episodes = [episode_id in purchased_episodes_set for episode_id in self.episode_int_ids]
        self.viewed_episodes = [episode_id in view_episodes_set for episode_id in self.episode_int_ids]

    def get_episode_image_urls(self, episode_no, attempts: int = 3) -> list[tuple[str, str]] | None:
        # cspell: ignore keygen
        is_purchased = self.purchased_episodes[episode_no] if hasattr(self, "purchased_episodes") else False

        if is_purchased and self.is_fhd_downloaded is not None:
            self.is_fhd_downloaded = True

        purchased = "true" if is_purchased else "false"
        # 스페셜 캐릭터를 포함하고 있는 이상한 웹툰이 있음
        episode_id_str = urllib.parse.quote(self.episode_ids[episode_no])
        episode_id_int = self.episode_int_ids[episode_no]

        keygen_url = (
            f"https://www.lezhin.com/lz-api/v2/cloudfront/signed-url/generate?"
            f"contentId={self.webtoon_int_id}&episodeId={episode_id_int}&purchased={purchased}&q={30}&firstCheckType={'P'}"
        )

        keys_response = self.hxoptions.get(keygen_url)
        if keys_response.status_code == 403:
            if self.bearer:
                logger.warning(
                    f"can't retrieve data from {self.episode_titles[episode_no]}. "
                    "It's probably because Episode is not available or not for free episode. "
                )
            else:
                logger.warning(
                    f"can't retrieve data from {self.episode_titles[episode_no]}. "
                    "It's almost certainly because you don't have bearer. Set bearer to get data."
                )
            return None

        response_data = keys_response.json()["data"]
        policy = response_data["Policy"]
        signature = response_data["Signature"]
        key_pair_id = response_data["Key-Pair-Id"]

        images_retrieve_url = (
            "https://www.lezhin.com/lz-api/v2/inventory_groups/comic_viewer_k?"
            f"platform=web&store=web&alias={self.webtoon_id}&name={episode_id_str}&preload=false"
            "&type=comic_episode"
        )
        try:
            images_data = self.hxoptions.get(images_retrieve_url).json()
        except json.JSONDecodeError:
            if attempts <= 1:
                raise
            logger.warning("Retrying json decode...")
            return self.get_episode_image_urls(episode_no, attempts=attempts - 1)

        # created_at = images_data["data"]["createdAt"]
        image_urls: list[tuple[str, str]] = []
        for image_url_data in images_data["data"]["extra"]["episode"]["scrollsInfo"]:
            image_url = (
                f'https://rcdn.lezhin.com/v2{image_url_data["path"]}'
                f".webp?purchased={purchased}&q={30}&updated={1587628135437}"
                f"&Policy={policy}&Signature={signature}&Key-Pair-Id={key_pair_id}"
            )
            media_type = image_url_data["mediaType"]
            image_urls.append((image_url, media_type))

        return image_urls

    def check_webtoon_id(self) -> str | None:
        try:
            title = self.hxoptions.get(f"https://www.lezhin.com/ko/comic/{self.webtoon_id}").soup_select_one(
                "h2.comicInfo__title"
            )
        except Exception:
            return None
        return title.text if title else None

    # PROPERTIES

    @property
    def bearer(self) -> str | None:
        return self._bearer

    @bearer.setter
    def bearer(self, value: str | None) -> None:
        """구현상의 이유로 header는 bearer보다 더 먼저 구현되어야 합니다."""
        self._bearer = value
        if value is not None:
            self.headers.update(Authorization=value)

    # PRIVATE METHODS

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
            else:
                logger.warning(f"Unknown option for {type(self).__name__}: {option!r}. value: {raw_value!r}")

    @classmethod
    def _extract_webtoon_id(cls, url) -> str | None:
        match url.host, url.parts:
            case "www.lezhin.com", ("/", "ko", "comic", webtoon_id):
                return webtoon_id

    def _download_image(
        self,
        image_directory: Path,
        url_and_media_type: tuple[str, str],
        image_no: int,
        client: AsyncClient,
        *,
        file_extension: str | None = None,
    ):
        url, media_type = url_and_media_type
        if media_type not in ("image/jpeg", "image/gif"):
            logger.warning(f"Unknown media type: {media_type}")
        if media_type.startswith("image"):
            file_extension = media_type.removeprefix("image/")
        return super()._download_image(image_directory, url, image_no, client, file_extension=file_extension)

    def _parse_episode_information(
        self,
        episode_information_raw: list[dict],
        get_paid_episode: bool | None = None,
        get_unusable_episode: bool = False,
    ) -> None:
        get_paid_episode = get_paid_episode if get_paid_episode is not None else self.download_paid_episode
        episode_int_ids: list[int] = []
        episode_str_ids: list[str] = []
        episode_titles: list[str] = []
        episode_type_chars: list[str] = []
        display_names: list[str] = []
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
            episode_type_chars.append(episode["display"]["type"])
            # episode_id_strs와 거의 같지만 특별편인 경우 'x1' 등으로 표시되는 episode_id_strs과는 달리
            # '공지'와 같은 글자로 나타나며 에피소드 위 작은 글씨를 의미한다. 스크래핑과는 큰 관련이 없는 자료이다.
            display_names.append(episode["display"]["displayName"])
            unusable_episodes.append(is_episode_unusable)
            free_episodes.append(is_episode_free)

            free_dates.append(episode.get("freedAt"))
            published_dates.append(episode["publishedAt"])
            updated_dates.append(episode["updatedAt"])

        lists_to_filter = (
            episode_int_ids,
            episode_str_ids,
            episode_titles,
            episode_type_chars,
            display_names,
            unusable_episodes,
            free_episodes,
            free_dates,
            published_dates,
            updated_dates,
        )

        to_downloads = [
            (get_unusable_episode or not is_unusable) and (get_paid_episode or is_free)
            for is_unusable, is_free in zip(unusable_episodes, free_episodes, strict=True)
        ]

        if len(episode_titles) - sum(to_downloads):
            match get_unusable_episode, get_paid_episode:
                case False, False:
                    warning_message = "Unusable or not for free episode will be skipped."
                case True, False:
                    warning_message = "Unusable episode will be skipped."
                case False, True:
                    warning_message = "Not for free episode will be skipped."
                case _:
                    raise Unreachable

            warning_message += " Following episodes will be skipped: "
            warning_message += ", ".join(
                subtitle for to_download, subtitle in zip(to_downloads, episode_titles, strict=True) if not to_download
            )
            logger.warning(warning_message)

        for list_to_filter in lists_to_filter:
            list_to_filter[:] = itertools.compress(list_to_filter, to_downloads)  # type: ignore

        self.episode_titles = episode_titles
        self.episode_ids: list[str] = episode_str_ids
        self.episode_int_ids = episode_int_ids
        self.free_episodes = free_episodes
        self.information_chars = episode_type_chars
        self.free_dates = free_dates
        self.published_dates = published_dates
        self.updated_dates = updated_dates

    def _post_process_directory(self, base_webtoon_directory: Path) -> Path:
        """For lezhin's shuffle process. This function changes webtoon_directory to unshuffled webtoon's directory."""
        from ._lezhin_unshuffler import unshuffle_typical_webtoon

        if not self.is_shuffled or not self.unshuffle:
            if self.is_shuffled:
                logger.warning(
                    "This webtoon is shuffled, but because self.unshuffle is set to True, webtoon won't be shuffled."
                )

            self._webtoon_directory = base_webtoon_directory
            self._unshuffled_webtoon_directory = None

            return base_webtoon_directory

        target_webtoon_directory = unshuffle_typical_webtoon(
            base_webtoon_directory,
            self.episode_int_ids,
            use_progress_bar=self.use_progress_bar,
            thread_number=self.thread_number,
        )
        if self.delete_shuffled:
            shutil.rmtree(base_webtoon_directory)
            logger.info("Shuffled webtoon directory is deleted.")

        self._webtoon_directory = base_webtoon_directory
        self._unshuffled_webtoon_directory = target_webtoon_directory

        return target_webtoon_directory
