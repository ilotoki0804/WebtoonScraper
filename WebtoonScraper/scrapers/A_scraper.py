"""Abstract Class of all scrapers."""

from __future__ import annotations

import asyncio
import functools
import json
import os
import re
import shutil
import time
from abc import abstractmethod
from contextlib import contextmanager, suppress
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar, Generic, Iterable, NamedTuple, TypeVar

if TYPE_CHECKING:
    from typing import Self
from urllib import parse

import hxsoup
import pyfilename as pf
from rich.console import Console
from rich.table import Table
from tqdm import tqdm

from ..directory_merger import (
    MERGED_WEBTOON_DIRECTORY,
    NORMAL_IMAGE,
    NORMAL_WEBTOON_DIRECTORY,
    ContainerStates,
    check_container_state,
    merge_webtoon,
    restore_webtoon,
    webtoon_regexes,
)
from ..exceptions import DirectoryStateUnmatchedError, InvalidURLError, UseFetchEpisode
from ..miscs import EpisodeNoRange
from ..miscs import __version__ as version
from ..miscs import logger
from ..webtoon_viewer import add_html_webtoon_viewer

WebtoonId = TypeVar("WebtoonId", int, str, tuple[int, int], tuple[str, int], tuple[str, str])


class CommentsDownloadOption(NamedTuple):
    """Some option can be not supported by scaper.

    Default setting(top comments only, no reply, not hard) are always supported and strongly recommended.
    """

    top_comments_only: bool = True
    """Download top comments only. Download all comments if False."""

    reply: bool = False
    """Download replies of comments."""

    hard: bool = False
    """Stop when failed to download comments."""

def reload_manager(f):
    """
    reload를 인자로 가지는 어떤 함수를 받아 reload가 True라면 cache가 있다면 제거하고
    다시 정보를 불러오도록 하는 decorator.
    """

    # __slots__가 필요하다면 Scraper에 _return_cache를 구현하면 됨!
    @functools.wraps(f)
    def wrapper(self, *args, reload: bool = False, **kwargs):
        try:
            self._return_cache
        except AttributeError:
            self._return_cache = {}

        if f in self._return_cache:
            if not reload:
                logger.debug(
                    f"{f} is already loaded, so loading is skipped. In order to reload, set parameter by reload=True."
                )
                return self._return_cache[f]
            logger.warning("Refreshing webtoon_information")

        try:
            return_value = f(self, *args, reload=reload, **kwargs)
        except Exception:
            logger.info("Exception is occured while function is executed. " "So function is not marked as loaded.")
            raise

        self._return_cache[f] = return_value
        return return_value

    return wrapper


class ExistingEpisodePolicy(Enum):
    """다운로드받을 에피소드와 이름이 같은 폴더가 존재할 때의 대처법입니다."""

    SKIP = "skip"
    """폴더가 이미 존재한다면 스킵합니다(기본값)."""

    HARD_CHECK = "hard_check"
    """해당 에피소드의 이미지 개수가 일치하지 않을 때 다시 다운로드받습니다."""

    INTERRUPT = "interrupt"
    """폴처가 이미 존재한다면 예외를 발생시킵니다."""

    REDOWNLOAD = "redownload"
    """항상 해당 폴더를 지우고 다시 다운로드합니다."""


class Scraper(Generic[WebtoonId]):
    """Abstract base class of all scrapers.

    전반적인 로직은 모두 이 페이지에서 관리하고, 썸네일을 받아오거나 한 회차의 이미지 URL을 불러오는 등의 방식은
    각자 scraper들에 구현합니다.
    """

    # 이 변수들은 웹툰 플랫폼에 종속적이기에 클래스 상수로 분류됨.
    BASE_URL: ClassVar[str]
    IS_CONNECTION_STABLE: ClassVar[bool]
    TEST_WEBTOON_ID: ClassVar
    TEST_WEBTOON_IDS: ClassVar[tuple] = ()
    INTERVAL_BETWEEN_EPISODE_DOWNLOAD_SECONDS: ClassVar[int | float] = 0
    URL_REGEX: ClassVar[re.Pattern[str]]
    DEFAULT_IMAGE_FILE_EXTENSION: str | None = None
    PLATFORM: ClassVar[str]
    COMMENTS_DOWNLOAD_SUPPORTED: bool = False

    def __init__(self, webtoon_id: WebtoonId) -> None:
        """
        webtoon_id를 전달하고, 만약 cookie가 bearer와 같은 추가 인증이 필요하다면
        그 또한 인자로 전달하세요.
        """
        self.hxoptions = hxsoup.MutableClientOptions(
            attempts=3,
            timeout=10,
            headers=dict(hxsoup.DEV_HEADERS),
            follow_redirects=True,
        )

        self.webtoon_id = webtoon_id
        self.base_directory = "webtoon"
        self.use_tqdm_while_download = True
        self.does_store_information = True
        self.existing_episode_policy: ExistingEpisodePolicy = ExistingEpisodePolicy.SKIP
        self._end_downloading_when_error_occured = False
        self.comments_option: CommentsDownloadOption | None = None
        self.comments = {}
        self.comment_counts = {}

    # PUBLIC METHODS

    @abstractmethod
    def get_episode_image_urls(self, episode_no: int) -> list[str] | None:
        """해당 회차를 구성하는 이미지들의 URL을 불러옵니다."""
        raise NotImplementedError

    @abstractmethod
    def get_episode_comments(self, episode_no: int) -> None:
        """해당 회차의 댓글을 모두 불러옵니다. 웹툰 플랫폼에 따라 지원하지 않을 수 있습니다."""
        raise NotImplementedError("Downloading comments is not supported in this scraper.")

    @reload_manager
    @abstractmethod
    def fetch_webtoon_information(self, *, reload: bool = False) -> None:
        """웹툰 자체에 대한 정보(제목이나 썸네일 등)를 불러옵니다."""
        self.webtoon_thumbnail_url: str
        self.title: str
        raise NotImplementedError

    @reload_manager
    @abstractmethod
    def fetch_episode_information(self, *, reload: bool = False) -> None:
        """웹툰의 에피소드에 대한 정보(에피소드 목록이나 ID 등)를 불러옵니다."""
        self.episode_titles: list[str]
        self.episode_ids: list[int]
        raise NotImplementedError

    @classmethod
    def from_url(
        cls,
        url: str,
        *args,  # cookie나 bearer같은 optional parameter를 잡기 위해 필요.
        **kwargs,
    ) -> Self:
        matched = cls.URL_REGEX.match(url)
        if matched is None:
            raise InvalidURLError.from_url(url, cls)

        try:
            webtoon_id: WebtoonId = cls._get_webtoon_id_from_matched_url(matched)
        except Exception as e:
            raise InvalidURLError.from_url(url, cls) from e

        return cls(webtoon_id, *args, **kwargs)

    def get_webtoon_directory_name(self) -> str:
        """웹툰 디렉토리를 만드는 데에 사용되는 string을 반환합니다."""
        return self._get_safe_file_name(f"{self.title}({self.webtoon_id})")

    def fetch_all(self, reload: bool = False) -> None:
        """웹툰에 관련한 정보를 불러옵니다.

        Args:
            reload (bool, False): 만약 참이라면 기존에 이미 불러와진 값을 무시하고 다시 값을 불러옵니다.
        """
        with suppress(UseFetchEpisode):
            self.fetch_webtoon_information(reload=reload)
        self.fetch_episode_information(reload=reload)

    def download_webtoon(
        self,
        episode_no_range: EpisodeNoRange = None,
        merge_number: int | None = None,
        add_viewer: bool = True,
    ) -> None:
        """웹툰 전체를 다운로드합니다.
        기본적으로는 별다른 인자를 필요로 하지 않으며 다운로드받을 범위와 웹툰 모아서 보기를 할 때는
        추가적인 파라미터를 이용할 수 있습니다.

        Args:
            episode_no_range: 다운로드할 회차의 범위를 정합니다.
                Scraper._episode_no_range_to_real_range의 문서를 참고하세요.
            merge_number: 웹툰을 모두 다운로드 받은 뒤 웹툰을 모아서 볼 수 있도록 합니다.
                None(기본값)이라면 웹툰을 모아서 볼 수 있도록 회차를 묶지 않습니다.
        """
        try:
            asyncio.run(
                self.async_download_webtoon(
                    episode_no_range=episode_no_range,
                    merge_number=merge_number,
                    add_viewer=add_viewer,
                )
            )
        except RuntimeError as e:
            try:
                e.add_note("Use `async_download_webtoon` in Jupyter or asyncio environment.")
            except AttributeError:
                logger.error("Use `async_download_webtoon` in Jupyter or asyncio environment.")
            raise

    async def async_download_webtoon(
        self,
        episode_no_range: EpisodeNoRange = None,
        merge_number: int | None = None,
        add_viewer: bool = True,
        manual_container_state: ContainerStates | None = None,
    ) -> None:
        """download_webtoon의 문서를 참조하세요."""
        if not self.COMMENTS_DOWNLOAD_SUPPORTED and self.comments_option:
            logger.warning("Comments downloading is not supported in this scraper. "
                           "comments_option will be ignored and comments won't be downloaded.")

        with self._send_context_callback_message("setup"):
            self.fetch_all()

        webtoon_directory_name = self.get_webtoon_directory_name()
        webtoon_directory = self.base_directory / webtoon_directory_name

        if webtoon_directory.exists() and os.listdir(webtoon_directory):
            if manual_container_state is None:
                container_state = check_container_state(webtoon_directory)
            else:
                container_state = manual_container_state

            if container_state == MERGED_WEBTOON_DIRECTORY:
                logger.warning("Webtoon directory was merged. Restoring...")
                restore_webtoon(webtoon_directory, None)
            elif container_state != NORMAL_WEBTOON_DIRECTORY:
                raise DirectoryStateUnmatchedError(
                    f"State of directory is {container_state}, which cannot be downloaded."
                )
        else:
            webtoon_directory.mkdir(parents=True, exist_ok=True)

        with self._send_context_callback_message("download_thubnail"):
            thumbnail_name = self._download_webtoon_thumbnail(webtoon_directory)

        episode_no_list = self._episode_no_range_to_real_range(episode_no_range)

        with self._send_context_callback_message("download_episode"):
            await self._download_episodes(episode_no_list, webtoon_directory)

        webtoon_directory = self._set_directory_to_merge(webtoon_directory)

        if merge_number is not None:
            with self._send_context_callback_message(
                "merge_webtoon",
                merge_number=merge_number,
                webtoon_directory=webtoon_directory,
            ):
                merge_webtoon(webtoon_directory, None, merge_number)

        if self.does_store_information:
            information = self.get_information()
            information.update(
                thumbnail_name=thumbnail_name,
                information_name="information.json",
                original_webtoon_directory_name=webtoon_directory_name,
                merge_number=merge_number,
                contents=["thumbnail", "information"],
            )
            if add_viewer:
                information.update(
                    webtoon_viewer_name="webtoon.html",
                )
                information["contents"].append("webtoon_viewer")
            (webtoon_directory / "information.json").write_text(
                json.dumps(information, ensure_ascii=False, indent=2), encoding="utf-8"
            )

        if add_viewer:
            add_html_webtoon_viewer(webtoon_directory)

    def list_episodes(self) -> None:
        """웹툰 에피소드 목록을 프린트합니다."""
        self.fetch_all()
        table = Table(show_header=True, header_style="bold blue", box=None)
        table.add_column("Episode number [dim](ID)[/dim]", width=12)
        table.add_column("Episode Title", style="bold")
        for i, (episode_id, episode_title) in enumerate(zip(self.episode_ids, self.episode_titles), 1):
            table.add_row(
                f"[red][bold]{i:04d}[/bold][/red] [dim]({episode_id})[/dim]",
                str(episode_title),
            )
        Console().print(table)

    def check_if_legitimate_webtoon_id(
        self,
        exception_type: type[BaseException] | tuple[type[BaseException], ...] = Exception,
    ) -> str | None:
        """webtoon_id가 플랫폼에서 적합하다면 제목을 반환하고 아니라면 None을 반환합니다."""
        try:
            self.fetch_webtoon_information()
            return self.title
        except exception_type:
            return None

    def callback(self, situation: str, **contexts) -> None:
        """웹툰 다운로드의 중요한 순간들을 알림받습니다.

        주의: callback은 다운로드 과정을 멈추고 작업합니다.
        최대한 빨리 끝날 수 있도록 하는 것이 속도에 좋습니다.
        """
        match situation:
            case "download_episode_end":
                print(f"The webtoon {self.title} download ended.")
            case "merge_webtoon_end":
                print("Merging webtoon ended.")
            case "merge_webtoon_start":
                print("Merging webtoon has started...")
            case "setup_end":
                if contexts.get("is_successful", True):
                    print("Webtoon data are fetched. Download has been started...")
            case "description":
                print(contexts["description"])
            case "episode_download_complete":
                # index = contexts["index"]
                is_download_sucessful = contexts["is_download_sucessful"]
                if is_download_sucessful:
                    episode_no = contexts["episode_no"]
                    episode_title = self.episode_titles[episode_no]
                    print(f"Episode {episode_no} `{episode_title}` sucessfully downloaded.")
            case the_others:
                if contexts:
                    logger.debug(f"WebtoonScraper status: {the_others}, context: {contexts}")
                else:
                    logger.debug(f"WebtoonScraper status: {the_others}")

    def get_information(self):
        return {
            "version": version,
            "title": self.title,
            "platform": self.PLATFORM,
            "webtoon_thumbnail_url": self.webtoon_thumbnail_url,
            "episode_ids": self.episode_ids,
            "episode_titles": self.episode_titles,
            "comments": self.comments,
            "comment_counts": self.comment_counts,
        }

    # PROPERTIES

    @property
    def base_directory(self) -> Path:
        return self._base_directory

    @base_directory.setter
    def base_directory(self, base_directory: str | Path) -> None:
        """
        웹툰을 다운로드할 디렉토리입니다. str이나 Path로 값을 받아 Path를 저장합니다.

        많은 이 변수의 사용처에서는 pathlib.Path를 필요로 합니다.
        이 property는 base_directory에 str을 넣어도 Path로 자동으로 변환해줍니다.
        이것을 이용하기 전에 안전한 파일명으로 바꾸는 것을 잊지 마세요!
        """
        self._base_directory = Path(base_directory)

    @property
    def cookie(self) -> str:
        """브라우저에서 값을 확인할 수 있는 쿠키 값입니다. 로그인 등에서 이용됩니다."""
        return self._cookie

    @cookie.setter
    def cookie(self, value: str) -> None:
        self._cookie = value
        self.headers.update(Cookie=value)

    @property
    def headers(self) -> dict[str, str]:
        """헤더 값입니다. self.hxoptions.headers을 직접 수정하는 방법으로도 가능하지만 조금 더 편리하게 header를 접근할 수 있습니다."""
        headers = self.hxoptions.headers
        assert isinstance(headers, dict), "Invalid subclassing could cause this error. Content developer."
        if TYPE_CHECKING:
            headers = {k: v for k, v in headers.items() if isinstance(k, str) and isinstance(v, str)}
        return headers

    @headers.setter
    def headers(self, value) -> None:
        self.headers.clear()
        self.headers.update(value)

    # PRIVATE METHODS

    @classmethod
    @abstractmethod
    def _get_webtoon_id_from_matched_url(cls, matched_url: re.Match) -> WebtoonId:
        return int(matched_url.group("webtoon_id"))

    @contextmanager
    def _send_context_callback_message(self, base_message: str, **contexts):
        self.callback(base_message + "_start", **contexts)
        end_contexts = {}
        try:
            yield end_contexts
        except Exception:
            if not self.callback(base_message + "_end", is_successful=False, **end_contexts):
                raise
        else:
            self.callback(base_message + "_end", is_successful=True)

    def _episode_no_range_to_real_range(self, episode_no_range: EpisodeNoRange) -> Iterable[int]:
        """
        Args:
            episode_no_range:
                None인 경우(기본값): 웹툰의 모든 회차를 다운로드 받습니다.
                tuple인 경우: `(처음, 끝)`의 튜플로 값을 받습니다. 이때 1부터 시작하고 끝 숫자를 포함합니다.
                        두 값 중 None인 것이 있다면 처음이나 끝으로 평가됩니다.
                    예1) (1, 10): 1회차부터 10회차까지를 다운로드함.
                    예2) (None, 20): 1회차부터 20회차까지를 다운로드함.
                    예2) (3, None): 3회차부터 끝까지 다운로드함.
                int인 경우: 해당 회차 하나만 다운로드 받습니다.
                slice인 경우: slice객체인 경우 해당 회차만큼 다운로드됩니다.
                    예) slice(None, None, 5): 5화, 10화, 15화 등 5의 배수 만큼 다운로드
                tuple이 아닌 iterable(예: 리스트)인 경우:
                    tuple이 아닌 iterable이 값으로 들어왔다면 해당 iterable에 있는 회차를 다운로드받습니다.
                    이때 회차 범위를 넘어서는 경우 무시됩니다.
                        예) [3, 5, 7, 8]: 3화, 5화, 7화, 8화를 다운로드함.
        """
        episode_length = len(self.episode_ids)

        if episode_no_range is None:
            return range(episode_length)

        if isinstance(episode_no_range, int):
            # 사용자용 숫자는 1이 더해진 상태라 1을 빼는 과정이 필요하다.
            return (episode_no_range - 1,)

        if isinstance(episode_no_range, tuple):
            start, end = episode_no_range

            if start is None:
                start = 1
            if end is None:
                end = episode_length

            # 사용자용 숫자는 1이 더해진 상태라 1을 빼는 과정이 필요하다.
            return range(start - 1, end)

        if isinstance(episode_no_range, slice):
            return (i - 1 for i in range(1, episode_length + 1)[episode_no_range])

        if isinstance(episode_no_range, Iterable):
            return sorted(i - 1 for i in episode_no_range if i <= episode_length)

        raise TypeError(f"Unknown type for episode_no_range({type(episode_no_range)}). Please check again.")

    async def _download_episodes(self, episode_no_list: Iterable[int], webtoon_directory: Path) -> None:
        """에피소드를 반복적으로 다운로드합니다.

        Args:
            episode_no_list: episode_no가 들어 있는 iterable입니다.
                iterable이므로 list 등으로 변환하는 과정이 필요할 수도 있습니다.
            webtoon_directory: 웹툰 디렉토리입니다.
        """
        if self.use_tqdm_while_download:
            episodes = self.pbar = tqdm(episode_no_list)
        else:
            episodes = tuple(episode_no_list)
        async with self.hxoptions.build_async_client() as client:
            for i, episode_no in enumerate(episodes):
                if self.INTERVAL_BETWEEN_EPISODE_DOWNLOAD_SECONDS:
                    # if를 붙이는 게 interval이 0인 경우 빨라짐.
                    time.sleep(self.INTERVAL_BETWEEN_EPISODE_DOWNLOAD_SECONDS)

                is_download_sucessful = await self._download_episode(episode_no, webtoon_directory, client)
                if not is_download_sucessful and self._end_downloading_when_error_occured:
                    logger.warning(
                        "Downloading is stopped since downloading prevous episode was unsuccessful. "
                        "Set `self.end_downloading_when_error_occured` to False if you want to "
                        "proceed download."
                    )
                    break

                if self.COMMENTS_DOWNLOAD_SUPPORTED and self.comments_option is not None:
                    try:
                        self.get_episode_comments(episode_no)
                    except NotImplementedError:
                        pass
                    except Exception as e:
                        if self.comments_option.hard:
                            raise

                        logger.warning(f"Failed to download comments of episode #{episode_no}.\n"
                                       f"{type(e).__name__}: {e}")

                if not self.use_tqdm_while_download:
                    self.callback(
                        "episode_download_complete",
                        index=i,
                        episode_no=episode_no,
                        episodes=episodes,
                        is_download_sucessful=is_download_sucessful,
                    )

    def _set_directory_to_merge(self, webtoon_directory: Path) -> Path:
        """다운로드할 디렉토리를 재안내합니다.

        레진코믹스의 언셔플러 구현에서 유일하게 사용됩니다.
        """
        return webtoon_directory

    def _check_directory_integrity(
        self,
        episode_directory: Path,
        image_urls: list,
    ) -> bool:
        """episode_directory를 생성하고 이미 있다면 해당 폴더 내 내용물이 적합한지 조사합니다.
        episode_no는 사용되지 않지만 혹시 모를 경우를 위해 남겨져 있습니다. 필요한 경우 제거하셔도 됩니다.

        False를 return한다면 회차를 다운로드해야 한다는 의미입니다.
        True를 return하면 해당 회차가 이미 완전히 다운로드되어 있으며, 따라서 다운로드를 지속할 이유가 없음을 의미합니다.
        """

        does_filename_inappropriate = any(
            not webtoon_regexes[NORMAL_IMAGE].match(file) for file in os.listdir(episode_directory)
        )
        does_file_count_inappropriate = len(image_urls) != len(os.listdir(episode_directory))
        return does_filename_inappropriate or does_file_count_inappropriate

    async def _download_episode(self, episode_no: int, webtoon_directory: Path, client: hxsoup.AsyncClient) -> bool:
        """한 회차를 다운로드받습니다. 주의: 이 함수의 episode_no는 0부터 시작합니다."""
        episode_title = self.episode_titles[episode_no]
        safe_episode_title = self._get_safe_file_name(episode_title)
        episode_directory = webtoon_directory / f"{episode_no + 1:04d}. {safe_episode_title}"

        if episode_directory.is_file():
            raise FileExistsError(f"File at {episode_directory} already exists. Please delete the file.")

        try:
            if episode_directory.is_dir():
                match self.existing_episode_policy:
                    case ExistingEpisodePolicy.SKIP:
                        self._set_progress_indication(f"downloading {episode_title} is skipped")
                        return True
                    case ExistingEpisodePolicy.INTERRUPT:
                        raise FileExistsError(
                            f"Directory at {episode_directory} already exists. Please delete the directory."
                        )
                    case ExistingEpisodePolicy.REDOWNLOAD:
                        check_integrity = False
                    case ExistingEpisodePolicy.HARD_CHECK:
                        check_integrity = True
            else:
                episode_directory.mkdir()
                check_integrity = False

            episode_images_url = self.get_episode_image_urls(episode_no)

            if not episode_images_url:
                logger.warning(
                    f"this episode is not free or not yet created. This episode won't be loaded. {episode_no=}"
                )
                self._set_progress_indication(f"Failed to download {episode_title}")
                if not os.listdir(episode_directory):
                    episode_directory.rmdir()
                return False

            if check_integrity:
                if not self._check_directory_integrity(episode_directory, episode_images_url):
                    self._set_progress_indication(f"Downloading {episode_title} is skipped after integrity check")
                    return True

                shutil.rmtree(episode_directory)
                episode_directory.mkdir()

            self._set_progress_indication(f"downloading {safe_episode_title}")
        except BaseException:
            if not os.listdir(episode_directory):
                episode_directory.rmdir()
            raise

        try:
            await asyncio.gather(
                *(
                    self._download_image(episode_directory, element, i, client)
                    for i, element in enumerate(episode_images_url)
                )
            )
        except BaseException:  # KeyboardInterrupt 등 원초적 오류들도 잡아야 해서 필요.
            shutil.rmtree(episode_directory)
            raise

        return True

    async def _download_image(
        self,
        episode_directory: Path,
        url: str,
        image_no: int,
        client: hxsoup.AsyncClient,
        *,
        file_extension: str | None = None,
    ) -> None:
        """
        Download image from url and returns to {episode_directory}/{file_name(translated to accactable name)}.

        Args:
            file_extension: 만약 None이라면(기본값) 파일 확장자를 자동으로 알아내고, 아니라면 해당 값을 파일 확장자로 사용합니다.
        """
        file_extension = file_extension or self._get_file_extension(url)

        file_name = f"{image_no:03d}.{file_extension}"

        image_raw: bytes = (await client.get(url)).content

        file_directory = episode_directory / file_name
        file_directory.write_bytes(image_raw)

    def _download_webtoon_thumbnail(self, webtoon_directory: Path, file_extension: str | None = None) -> str:
        """
        웹툰의 썸네일을 불러오고 thumbnail_directory에 저장합니다.
        Args:
            webtoon_directory (Path): 썸네일을 저장할 디렉토리입니다.
            file_extionsion (str | None): 파일 확장자입니다. 만약 None이라면(기본값) 자동으로 값을 확인합니다.
        """
        file_extension = file_extension or self._get_file_extension(self.webtoon_thumbnail_url)
        image_raw = self.hxoptions.get(self.webtoon_thumbnail_url).content
        thumbnail_name = self._get_safe_file_name(f"{self.title}.{file_extension}")
        (webtoon_directory / thumbnail_name).write_bytes(image_raw)
        return thumbnail_name

    def _set_progress_indication(self, description: str) -> None:
        """진행사항을 표시할 곳을 tqdm의 description과 print 중 어떤 것을 사용할지 결정합니다.

        self.use_tqdm_while_download가 False라면 print를 사용하고, True라면 pbar를 이용합니다.
        이는 self.use_tqdm_while_download 설정을 변경해 사용할 수 있습니다. 기본값은 True입니다.
        만약 사용자에게 꼭 알려야 하는 중요한 것이 있다면 이 함수가 아닌 직접 print나 logging을 사용하는 것을 권장합니다.
        단, 만약 self.pbar가 없어 AttributeError가 난다면 무조건 print를 사용합니다.

        Args:
            description: 에피소드를 다운로드할 때 내보낼 메시지.
        """
        if self.use_tqdm_while_download:
            with suppress(AttributeError):
                self.pbar.set_description(description)
                return

        self.callback("description", description=description)

    @classmethod
    def _get_file_extension(cls, filename_or_url: str) -> str:
        """Get file extionsion from filename or URL.

        Args:
            filename_or_url: 파일 확장자가 궁금한 파일명이나 URL. 이때 URL 쿼리는 무시됩니다.

        Returns:
            파일 확장자를 반환합니다.
        """
        url_path = parse.urlparse(filename_or_url).path  # 놀랍게도 일반 filename(file.jpg 등)에서도 동작함.
        extension_name = re.search(r"(?<=[.])\w+?$", url_path)
        if extension_name is not None:
            return extension_name.group(0)

        if cls.DEFAULT_IMAGE_FILE_EXTENSION is not None:
            return cls.DEFAULT_IMAGE_FILE_EXTENSION

        raise ValueError(f"File extension not detected of {filename_or_url}(path: {url_path}).")

    @staticmethod
    def _get_safe_file_name(file_or_diretory_name: str) -> str:
        """Convert file or diretory "name" to accaptable name.

        Caution: Do NOT put a diretory path(e.g. webtoon/ep1/001.jpg) here.
        Otherwise this will smash slashes and backslashes.
        """
        return pf.to_safe_name(file_or_diretory_name)
