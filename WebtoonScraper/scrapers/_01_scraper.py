"""Abstract Class of all scrapers."""

from __future__ import annotations

import asyncio
import functools
import html
import json
import os
import re
import shutil
import textwrap
import time
from abc import abstractmethod
from collections import defaultdict
from collections.abc import Mapping
from contextlib import contextmanager, suppress
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    ClassVar,
    Generic,
    Iterable,
    Literal,
    NamedTuple,
    Sequence,
    TypedDict,
    TypeGuard,
    TypeVar,
)
from urllib import parse

import hxsoup
import pyfilename as pf
from tqdm import tqdm

from ..processing import BatchMode, add_viewer as add_viewer_, concat_webtoon
from ..processing.directory_merger import (
    DIRECTORY_PATTERNS,
    NORMAL_IMAGE,
    ContainerStates,
    ensure_normal,
    merge_webtoon,
)
from ..base import logger
from ..exceptions import (
    InvalidURLError,
    InvalidWebtoonIdError,
    NotImplementedCommentsDownloadOptionError,
    UseFetchEpisode,
)

if TYPE_CHECKING:
    from typing import Required, Self

WebtoonId = TypeVar("WebtoonId", int, str, tuple[int, int], tuple[str, int], tuple[str, str])


class EpisodeRange:
    def __init__(self, *ranges: slice | range | Iterable[int] | int):
        """range 인스턴스는 기본적으로 체크되지 않으며 나중에 오류가 발현될 수 있습니다."""

        if not ranges:
            self._ranges = []
            return

        new_ranges: list[slice | range | set[int]] = []
        indexes = set()
        for range_ in ranges:
            if isinstance(range_, slice | range):
                new_ranges.append(range_)
            elif isinstance(range_, Iterable):
                indexes.update(range_)
            else:
                indexes.add(range_)
        if indexes:
            new_ranges.append(indexes)
        self._ranges = new_ranges

    def __contains__(self, index: int):
        """잘못된 값을 지니는 slice 인스턴스를 가지고 있더라도 순서에 따라 오류 없이 값을 내보낼 수도 있습니다."""

        for range_ in self._ranges:
            match range_:
                case set():
                    if index in range_:
                        return True

                case slice(start=None, stop=int(stop), step=int() | None as step):
                    step = 1 if step is None else step
                    if index in range(1, stop, step):
                        return True

                case slice(start=int(start), stop=None, step=int() | None as step):
                    step = 1 if step is None else step
                    if start <= index and (start - index) % step == 0:
                        return True

                case slice(start=int(start), stop=int(stop), step=int() | None as step):
                    step = 1 if step is None else step
                    if index in range(start, stop, step):
                        return True

                case slice():
                    raise ValueError(f"Invalid slice value: {range_!r}")

                case _:
                    raise ValueError(f"Invalid range value: {range_!r}")

        return False

    def __repr__(self) -> str:
        return f"{type(self).__name__}({', '.join(repr(range_) for range_ in self._ranges)})"

    @classmethod
    def from_string(cls, episode_range: str, inclusive: bool = True) -> Self:
        """문자열로부터 EpisodeRange 인스턴스를 만듭니다.

        Args:
            episode_range (str):
                에피소드 범위가 될 문자열입니다. 규칙은 다음과 같습니다.
                여러 에피소드를 쉼표로 나누어 병렬하여 나타내면
                각각의 에피소드를 다운로드받습니다.
                예를 들어 `1,4,45`는 1화, 4화, 45화가 선택됩니다.
                에피소드 수를 모두 쓰는 대신 범위를 지정해줄 수 있습니다.
                예를 들어 `5~20`은 5화부터 20화까지(inclusive=True일때) 범위가 선택됩니다.
                이때 시작이나 끝을 생략할 수 있습니다.
                예를 들어 `7~`은 7화부터 끝날 때가지 범위를 선택하며
                `~31`은 시작부터 31화까지 범위를 선택하며 `1~31`과 같습니다.
                범위 선택과 에피소드 수 쓰기는 쉼표로 나누어 병렬할 수 있습니다.
                예를 들어 `2,15,5~10,45~`은 2화, 15화, 5~10화, 45화부터 끝까지 다운로드한다는 의미입니다.
            inclusive (bool, True):
                맨 마지막 인덱스를 포함할지 결정합니다. 기본값은 True입니다.
                예를 들어 `5~10`일때 inclusive=True라면 10회차를 포함하고,
                False라면 포함하지 않아 5회차부터 9회차까지만 포함합니다.
        """
        ranges = []
        for range_str in episode_range.split(","):
            start, tilde, end = range_str.partition("~")
            start = start.replace(" ", "")
            start = int(start) if start else None
            end = end.replace(" ", "")
            end = int(end) + inclusive if end else None

            if tilde:
                ranges.append(slice(start, end))
            elif start:
                ranges.append(start)

        return cls(*ranges)


class Comment(TypedDict, total=False):
    comments_id: int | str
    reply_count: int | None
    username: Required[str]
    user_id: object
    likes: int
    dislikes: int
    last_modified: str
    created: str
    comment: Required[str]
    replies: list[Comment]


class EpisodeComments(TypedDict, total=False):
    download_option: dict
    comments: list[Comment]
    comment_count: int
    author_comment: str


class CommentsDownloadOption(NamedTuple):
    """댓글을 다운로드할 때 어떤 방식으로 다운로드할지 결정합니다.

    Some option can be not supported by scraper.
    Default setting(top comments only, no reply) are always supported and strongly recommended.
    """

    top_comments_only: bool = True
    """Download top comments only. Download all comments if False."""

    reply: bool = False
    """Download replies of comments."""


def reload_manager(f):
    """함수의 결과값을 캐싱합니다. 단, reload 파라미터를 True로 둘 경우 다시 함수를 호출에 값을 받아옵니다.

    이 함수는 클래스의 메소드에만 적용시킬 수 있습니다.
    `__slots__`가 있다면 제대로 작동하지 않을 수 있는데, 그럴 경우 `__slots__`에 `_reload_cache`를 추가해 주세요.
    """

    # __slots__가 필요하다면 Scraper에 _return_cache를 구현하면 됨!
    @functools.wraps(f)
    def wrapper(self, *args, reload: bool = False, **kwargs):
        try:
            self._reload_cache
        except AttributeError:
            self._reload_cache = {}

        if f in self._reload_cache:
            if not reload:
                logger.debug(
                    f"{f} is already loaded, so loading is skipped. In order to reload, set `reload` parameter to True."
                )
                return self._reload_cache[f]
            logger.info("Refreshing webtoon_information")

        return_value = f(self, *args, reload=reload, **kwargs)
        self._reload_cache[f] = return_value
        return return_value

    return wrapper


def _shorten(text: str):
    shortened = textwrap.shorten(text, width=15, placeholder="...")
    return f"'{shortened}'"


class Scraper(Generic[WebtoonId]):  # MARK: SCRAPER
    """Abstract base class of all scrapers.

    전반적인 로직은 모두 이 페이지에서 관리하고, 썸네일을 받아오거나 한 회차의 이미지 URL을 불러오는 등의 방식은
    각자의 scraper들에서 구현합니다.
    """

    # 이 변수들은 웹툰 플랫폼에 종속적이기에 클래스 상수로 분류됨.
    BASE_URL: ClassVar[str]
    TEST_WEBTOON_ID: ClassVar
    TEST_WEBTOON_IDS: ClassVar[tuple] = ()
    DOWNLOAD_INTERVAL: ClassVar[int | float] = 0
    URL_REGEX: ClassVar[re.Pattern[str]]
    DEFAULT_IMAGE_FILE_EXTENSION: str | None = None
    PLATFORM: ClassVar[str]
    COMMENTS_DOWNLOAD_SUPPORTED: bool = False
    INFORMATION_VARS: ClassVar[dict[str, None | str | Callable[[Any, str], Any]]] = dict(
        title=None,
        platform="PLATFORM",
        webtoon_thumbnail_url=None,
        episode_ids=None,
        episode_titles=None,
        comments_data=None,
        author=None,
    )

    def __init__(self, webtoon_id: WebtoonId, /) -> None:
        self.hxoptions = hxsoup.MutableClientOptions(
            attempts=3,
            timeout=10,
            headers=dict(hxsoup.DEV_HEADERS),
            follow_redirects=True,
        )

        self.webtoon_id = webtoon_id
        self.base_directory = Path.cwd()
        self.use_tqdm_while_download = True
        self.does_store_information = True
        self.existing_episode_policy: Literal["skip", "raise", "download_again", "hard_check"] = "skip"
        self._end_downloading_when_error_occurred = False
        self.comments_option: CommentsDownloadOption | None = None
        self.comments_data: defaultdict[int, EpisodeComments] = defaultdict(dict)  # type: ignore
        self.author = None

    # MARK: PUBLIC METHODS

    @abstractmethod
    def get_episode_image_urls(self, episode_no: int) -> list[str] | None:
        """해당 회차를 구성하는 이미지들의 URL을 불러옵니다."""
        raise NotImplementedError

    @abstractmethod
    def get_episode_comments(self, episode_no: int) -> None:
        """해당 회차의 댓글을 모두 불러옵니다. 웹툰 플랫폼에 따라 지원하지 않을 수 있습니다."""
        raise NotImplementedCommentsDownloadOptionError("Downloading comments is not supported in this scraper.")

    @reload_manager
    @abstractmethod
    def fetch_webtoon_information(self, *, reload: bool = False) -> None:
        """웹툰 자체에 대한 정보(제목이나 썸네일 등)를 불러옵니다."""
        self.webtoon_thumbnail_url: str
        self.title: str
        self.author: str | None
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
        """Raw URL에서 자동으로 웹툰 ID를 추출합니다."""
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
        return self._safe_name(f"{self.title}({self.webtoon_id})")

    def fetch_all(self, reload: bool = False) -> None:
        """웹툰 다운로드에 필요한 모든 필수적인 정보를 불러옵니다."""
        with suppress(UseFetchEpisode):
            self.fetch_webtoon_information(reload=reload)
        self.fetch_episode_information(reload=reload)

    def download_webtoon(
        self,
        episode_no_range: EpisodeRange | None = None,
        merge_number: int | None = None,
        concat: BatchMode | None = None,
        add_viewer: bool = True,
    ) -> None:
        """웹툰을 다운로드합니다.

        Jupyter 등 async 환경에서는 제대로 동작하지 않을 수 있습니다. 그럴 경우 async_download_webtoon을 사용하세요.

        기본적으로는 별다른 인자를 필요로 하지 않으며 다운로드받을 범위와 웹툰 모아서 보기를 할 때는
        추가적인 파라미터를 이용할 수 있습니다.

        Args:
            episode_no_range: 다운로드할 회차의 범위를 정합니다.
                Scraper._episode_no_range_to_real_range의 문서를 참고하세요.
            merge_number: 웹툰을 모두 다운로드 받은 뒤 웹툰을 모아서 볼 수 있도록 합니다.
                None(기본값)이라면 웹툰을 모아서 볼 수 있도록 회차를 묶지 않습니다.
            add_viewer: 웹툰 뷰어인 webtoon.html을 추가합니다. 기본값은 True입니다.
        """
        try:
            asyncio.run(
                self.async_download_webtoon(
                    episode_no_range=episode_no_range,
                    merge_number=merge_number,
                    concat=concat,
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
        episode_no_range: EpisodeRange | None = None,
        merge_number: int | None = None,
        concat: BatchMode | None = None,
        add_viewer: bool = True,
        manual_container_state: ContainerStates | None = None,
    ) -> None:
        """download_webtoon의 async 버전입니다. 자세한 설명은 download_webtoon의 문서를 참조하세요.

        Example:
            ```python
            >>> scraper = NaverWebtoonScraper(819217)
            >>> await scraper.async_download_webtoon()
            ...
            ```
        """
        if not self.COMMENTS_DOWNLOAD_SUPPORTED and self.comments_option:
            logger.warning(
                "Comments downloading is not supported in this scraper. "
                "comments_option will be ignored and comments won't be downloaded."
            )

        with self._send_context_callback_message("setup"):
            self.fetch_all()

        webtoon_directory_name = self.get_webtoon_directory_name()
        webtoon_directory = self.base_directory / webtoon_directory_name

        ensure_normal(webtoon_directory, empty_ok=True, manual_container_state=manual_container_state)

        with self._send_context_callback_message("download_thumbnail"):
            thumbnail_name = self._download_webtoon_thumbnail(webtoon_directory)

        # 여기에서 1-based에서 0-based로 바뀜.
        if episode_no_range is None:
            episode_no_list = range(len(self.episode_ids))
        else:
            episode_no_list = tuple(i for i in range(len(self.episode_ids)) if i + 1 in episode_no_range)

        with self._send_context_callback_message("download_episode"):
            await self._download_episodes(episode_no_list, webtoon_directory)

        webtoon_directory = self._post_process_directory(webtoon_directory)

        if concat is not None:
            with self._send_context_callback_message(
                "concat_webtoon",
                batch=concat,
                webtoon_directory_prev=webtoon_directory,
            ) as ctx:
                webtoon_directory = concat_webtoon(webtoon_directory, None, concat, rebuild_webtoon_viewer=False, use_tqdm=self.use_tqdm_while_download)
                assert webtoon_directory is not None, "WORKING indicator exists. Program your code properly."
                ctx["webtoon_directory_after"] = webtoon_directory

        # 모아서 보기 적용
        if merge_number is not None:
            with self._send_context_callback_message(
                "merge_webtoon",
                merge_number=merge_number,
                webtoon_directory=webtoon_directory,
            ):
                merge_webtoon(webtoon_directory, None, merge_number)

        # information.json 추가
        if self.does_store_information:
            information_file = webtoon_directory / "information.json"
            if information_file.is_file():
                old_information = json.loads(information_file.read_text(encoding="utf-8"))
            else:
                old_information = {}

            information = self._get_information(old_information)
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
            information_file.write_text(json.dumps(information, ensure_ascii=False, indent=2), encoding="utf-8")

        # webtoon.html 추가
        if add_viewer:
            add_viewer_(webtoon_directory)

    def check_webtoon_id(
        self,
        exception_type: type[BaseException] | tuple[type[BaseException], ...] = Exception,
    ) -> str | None:
        """webtoon_id가 플랫폼에서 적합하다면 제목을 반환하고 아니라면 None을 반환합니다."""
        try:
            self.fetch_webtoon_information()
            return self.title
        except exception_type:
            return None

    def callback(self, situation: str, **context) -> None:
        """웹툰 다운로드의 중요한 순간들을 알림받습니다.

        주의: callback은 다운로드 과정을 멈추고 작업합니다.
        최대한 빨리 끝날 수 있도록 하는 것이 속도에 좋습니다.
        """
        match situation:
            case "download_episode_end":
                logger.info(f"The webtoon {self.title} download ended.")
            case "merge_webtoon_end":
                logger.info("Merging webtoon ended.")
            case "merge_webtoon_start":
                logger.info("Merging webtoon has started...")
            case "setup_end":
                logger.info("Webtoon data are fetched. Download has been started...")
            case "indicate" | "download_skipped" | "download_failed" | "downloading_image":
                match situation:
                    case "indicate":
                        description = context["description"]
                    case "skip_download":
                        episode_no = context["episode_no"]
                        description = f"{_shorten(self.episode_titles[episode_no])} skipped"
                    case "download_failed":
                        episode_no = context["episode_no"]
                        episode_title = self.episode_titles[episode_no]
                        description = f"{_shorten(episode_title)} download failed"
                        if context["warning"]:
                            logger.warning(f"Failed to download: {episode_no + 1}. {episode_title}")
                    case "downloading_image":
                        episode_no = context["episode_no"]
                        episode_title = self.episode_titles[episode_no]
                        description = f"{_shorten(episode_title)} download failed"
                    case "download_completed":
                        episode_no = context["episode_no"]
                        episode_title = self.episode_titles[episode_no]
                        description = f"{_shorten(episode_title)} download completed"

                if not self._progress_indication(description):
                    logger.info(description)
            case "description":
                logger.info(context["description"])
            case "episode_download_complete":
                is_download_successful = context["is_download_successful"]
                if is_download_successful:
                    episode_no = context["episode_no"]
                    episode_title = self.episode_titles[episode_no]
                    logger.info(f"Downloaded: #{episode_no} {_shorten(episode_title)}")
            case the_others:
                if context:
                    logger.debug(f"WebtoonScraper status: {the_others}, context: {context}")
                else:
                    logger.debug(f"WebtoonScraper status: {the_others}")

    # MARK: PROPERTIES

    @property
    def base_directory(self) -> Path:
        return self._base_directory

    @base_directory.setter
    def base_directory(self, base_directory: str | Path) -> None:
        """
        웹툰 폴더가 위치할 디렉토리입니다. str이나 Path로 값을 받아 Path를 저장합니다.

        많은 이 변수의 사용처에서는 Path를 필요로 합니다.
        이 property는 base_directory에 str을 넣어도 Path로 자동으로 변환해줍니다.
        """
        self._base_directory = Path(base_directory)

    @property
    def cookie(self) -> str | None:
        """브라우저에서 값을 확인할 수 있는 쿠키 값입니다. 로그인 등에서 이용됩니다."""
        try:
            return self.headers["Cookie"]
        except KeyError:
            return None

    @cookie.setter
    def cookie(self, value: str) -> None:
        self.headers.update(Cookie=value)

    @property
    def headers(self) -> dict[str, str]:
        """헤더 값입니다. self.hxoptions.headers을 직접 수정하는 방법으로도 사용 가능하지만 조금 더 편리하게 header를 접근할 수 있습니다."""
        headers = self.hxoptions.headers
        if TYPE_CHECKING:
            assert isinstance(headers, dict)
            headers = {k: v for k, v in headers.items() if isinstance(k, str) and isinstance(v, str)}
        return headers

    @headers.setter
    def headers(self, value) -> None:
        self.headers.clear()
        self.headers.update(value)

    # MARK: PRIVATE METHODS

    @classmethod
    def _from_string(cls, string: str, /, **kwargs):
        """webtoon_id가 int가 아니라면 반드시 구현해야 합니다."""
        return cls(int(string), **kwargs)  # type: ignore

    def _apply_options(self, options: dict[str, str], /) -> None:
        if options:
            raise ValueError("This scraper does not accept any options.")

    def _get_information(self, old_information: dict):
        """`information.json`에 탑재할 정보를 추가합니다.

        이 함수를 override하면 기본적으로 포함되어 있는 정보 외에 다양한 플랫폼에 한정적인 정보를 추가할 수 있습니다.
        None일 경우에는 1) dict일 경우 update가 사용됩니다. 2) 정보가 존재하지 않을 경우 오류가 나지 않고 스킵됩니다.
        """
        information = {}
        for name, value in self.INFORMATION_VARS.items():
            if value is None:
                _ABSENT = object()
                value = getattr(self, name, _ABSENT)
                old_value = old_information.get(name, _ABSENT)
                if value is _ABSENT:
                    if old_value is not _ABSENT:
                        continue
                    raise ValueError(f"{self}.{name} does not exist.")
                if isinstance(value, Mapping):
                    value = dict(value)
                    if old_value is not _ABSENT:
                        value.update(old_value)
                information[name] = value
            elif isinstance(value, str):
                information[name] = getattr(self, value)
            elif callable(value):
                information[name] = value(self, name)
            else:
                raise ValueError(f"Unexpected information value: {value!r}")
        return information

    @classmethod
    @abstractmethod
    def _get_webtoon_id_from_matched_url(cls, matched_url: re.Match) -> WebtoonId:
        return int(matched_url.group("webtoon_id"))

    @contextmanager
    def _send_context_callback_message(self, base_message: str, **contexts):
        self.callback(base_message + "_start", **contexts)
        end_contexts = {}
        yield end_contexts
        self.callback(base_message + "_end", is_successful=True, **end_contexts)

    async def _download_episodes(self, episode_no_list: Sequence[int], webtoon_directory: Path) -> None:
        """에피소드를 반복적으로 다운로드합니다.

        Args:
            episode_no_list: episode_no가 들어 있는 iterable입니다.
                iterable이므로 list 등으로 변환하는 과정이 필요할 수도 있습니다.
            webtoon_directory: 웹툰 디렉토리입니다.
        """
        if self.use_tqdm_while_download:
            episodes = self.pbar = tqdm(episode_no_list)
        else:
            episodes = episode_no_list
        async with self.hxoptions.build_async_client() as client:
            for i, episode_no in enumerate(episodes):
                is_download_successful = await self._download_episode(episode_no, webtoon_directory, client)
                if not is_download_successful and self._end_downloading_when_error_occurred:
                    logger.warning(
                        "Downloading is stopped since downloading previous episode was unsuccessful. "
                        "Set `self.end_downloading_when_error_occurred` to False if you want to "
                        "proceed download."
                    )
                    break

                if self.COMMENTS_DOWNLOAD_SUPPORTED and self.comments_option is not None:
                    try:
                        self.get_episode_comments(episode_no)
                    except NotImplementedError:
                        pass
                    except Exception as e:
                        logger.warning(
                            f"Failed to download comments of episode #{episode_no}.\n" f"{type(e).__name__}: {e}"
                        )

                if not self.use_tqdm_while_download:
                    self.callback(
                        "episode_download_complete",
                        index=i,
                        episode_no=episode_no,
                        episodes=episodes,
                        is_download_successful=is_download_successful,
                    )

    def _post_process_directory(self, webtoon_directory: Path) -> Path:
        """모아서 보기나 information.json, webtoon.html 등이 위치할 디렉토리를 재안내합니다.

        레진코믹스의 언셔플러 구현에서 유일하게 사용됩니다.
        """
        return webtoon_directory

    def _does_directory_intact(
        self,
        episode_directory: Path,
        image_urls: list,
    ) -> bool:
        """episode_directory를 생성하고 이미 있다면 해당 폴더 내 내용물이 적합한지 조사합니다.

        False를 return한다면 회차를 다운로드해야 한다는 의미입니다.
        True를 return하면 해당 회차가 이미 완전히 다운로드되어 있으며, 따라서 다운로드를 지속할 이유가 없음을 의미합니다.
        """

        directory_contents = os.listdir(episode_directory)
        normal_image_regex = DIRECTORY_PATTERNS[NORMAL_IMAGE]
        return len(image_urls) != len(directory_contents) and all(
            normal_image_regex.match(file) for file in directory_contents
        )

    async def _download_episode(self, episode_no: int, webtoon_directory: Path, client: hxsoup.AsyncClient) -> bool:
        """한 회차를 다운로드받습니다.

        이 함수는 일반적으로 사용됩니다. 각 스크래퍼의 구현이 궁금하다면 get_episode_image_urls을 대신 참고하세요.
        주의: 이 함수의 episode_no는 0부터 시작합니다.
        """
        episode_title = self.episode_titles[episode_no]
        directory_name = self._safe_name(f"{episode_no + 1:04d}. {episode_title}")
        episode_directory = webtoon_directory / directory_name

        if episode_directory.is_file():
            if self.existing_episode_policy == "skip":
                self.callback("download_skipped", episode_no=episode_no, file=True)
                return True
            raise FileExistsError(f"File at {episode_directory} already exists. Please delete the file.")

        try:
            if episode_directory.is_dir():
                match self.existing_episode_policy:
                    case "skip":
                        self.callback("download_skipped", episode_no=episode_no)
                        return True
                    case "raise":
                        raise FileExistsError(
                            f"Directory at {episode_directory} already exists. Please delete the directory."
                        )
                    case "download_again":
                        check_integrity = False
                    case "hard_check":
                        check_integrity = True
            else:
                episode_directory.mkdir()
                check_integrity = False

            time.sleep(self.DOWNLOAD_INTERVAL)  # 실제로 요청을 보내기 직전에 interval을 넣음.
            episode_images_url = self.get_episode_image_urls(episode_no)

            if not episode_images_url:
                self.callback("download_failed", episode_no=episode_no, warning=True)
                if not os.listdir(episode_directory):
                    episode_directory.rmdir()
                return False

            if check_integrity:
                if self._does_directory_intact(episode_directory, episode_images_url):
                    self.callback("download_skipped", episode_no=episode_no, intact=True)
                    return True

                shutil.rmtree(episode_directory)
                episode_directory.mkdir()

            self.callback("downloading_image", episode_no=episode_no)
        except BaseException:
            if not os.listdir(episode_directory):
                episode_directory.rmdir()
            raise

        try:
            tasks = (
                self._download_image(episode_directory, element, i, client)
                for i, element in enumerate(episode_images_url)
            )
            await asyncio.gather(*tasks)
        except BaseException:
            shutil.rmtree(episode_directory)
            raise

        self.callback("download_completed", episode_no=episode_no)
        return True

    async def _download_image(
        self,
        image_directory: Path,
        url: str,
        image_no: int,
        client: hxsoup.AsyncClient,
        *,
        file_extension: str | None = None,
    ) -> None:
        """url에서 이미지를 다운로드받아 image_directory에 저장합니다.

        Args:
            image_directory: 다운로드할 이미지가 위치할 디렉토리입니다.
            url: 이미지를 다운로드할 URL입니다.
            image_no: 이미지의 이름을 결정할 때 사용할 정보 중 하나입니다. 이미지의 이름이 됩니다.
            client: 사용할 AsyncClient입니다.
            file_extension: 만약 None이라면(기본값) 파일 확장자를 자동으로 알아내고, 아니라면 해당 값을 파일 확장자로 사용합니다.
        """
        file_extension = file_extension or self._get_file_extension(url)
        file_name = f"{image_no:03d}.{file_extension}"
        image_raw: bytes = (await client.get(url)).content

        file_directory = image_directory / file_name
        file_directory.write_bytes(image_raw)

    def _download_webtoon_thumbnail(self, webtoon_directory: Path, file_extension: str | None = None) -> str:
        """self.webtoon_thumbnail_url에 정의되어 있는 웹툰의 썸네일의 정보로부터 다운로드해 webtoon_directory에 저장합니다.

        Args:
            webtoon_directory (Path): 썸네일을 저장할 디렉토리입니다.
            file_extension (str | None): 파일 확장자입니다. 만약 None이라면(기본값) 자동으로 값을 확인합니다.
        """
        file_extension = file_extension or self._get_file_extension(self.webtoon_thumbnail_url)
        image_raw = self.hxoptions.get(self.webtoon_thumbnail_url).content
        thumbnail_name = self._safe_name(f"{self.title}.{file_extension}")
        (webtoon_directory / thumbnail_name).write_bytes(image_raw)
        return thumbnail_name

    @classmethod
    def _get_file_extension(cls, filename_or_url: str) -> str:
        """Get file extension from filename or URL.

        Args:
            filename_or_url: 파일 확장자가 궁금한 파일명이나 URL. 이때 URL 쿼리는 무시됩니다.

        Returns:
            파일 확장자를 반환합니다.
        """
        url_path = parse.urlparse(filename_or_url).path  # 놀랍게도 일반 filename(file.jpg 등)에서도 동작함.
        extension_name = re.search(r"(?<=[.])\w+?$", url_path, flags=re.IGNORECASE)
        if extension_name is not None:
            return extension_name.group(0).lower()

        # 만약 파일 확장자를 파일 이름에서 찾는 것에 실패하였을 경우 DEFAULT_IMAGE_FILE_EXTENSION를 사용함.
        if cls.DEFAULT_IMAGE_FILE_EXTENSION is not None:
            return cls.DEFAULT_IMAGE_FILE_EXTENSION

        raise ValueError(f"The file extension is not detected: `{filename_or_url}`")

    @staticmethod
    def _safe_name(name: str) -> str:
        """일반 문자열을 파일명으로 사용 가능한 문자열로 변경합니다.

        Caution: Do NOT put a directory path(e.g. webtoon/ep1/001.jpg) here.
        Otherwise this function will smash slashes and backslashes.
        """
        return pf.convert(html.unescape(name))

    def _progress_indication(self, message: str, fallback: bool = True) -> bool:
        if self.use_tqdm_while_download:
            with suppress(AttributeError):
                self.pbar.set_description(message)
                return True
        return False
