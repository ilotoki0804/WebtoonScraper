from __future__ import annotations

import asyncio
from datetime import datetime
import html
from http.cookies import SimpleCookie
import json
import os
import shutil
import ssl
import time
import warnings
from abc import abstractmethod
from collections.abc import Callable, Container, Mapping
from contextlib import suppress
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    ClassVar,
    Generic,
    Literal,
    Self,
    TypeVar,
)

import httpc
import httpx
import pyfilename as pf
from rich import progress
from yarl import URL

from ..base import console, logger, platforms
from ..directory_state import (
    DirectoryState,
    load_information_json,
)
from ..exceptions import (
    URLError,
    Unreachable,
    UseFetchEpisode,
)
from ._helpers import (
    EpisodeRange,
    ExtraInfoScraper,
    async_reload_manager,
    infer_filetype,
)
from ._callback_manager import (
    Callback,
    CallbackManager,
    LogLevel,
)
from ._helpers import shorten as _shorten

WebtoonId = TypeVar("WebtoonId")
CallableT = TypeVar("CallableT", bound=Callable)
RangeType = EpisodeRange | Container[WebtoonId] | None
DownloadStatus = Literal["failed", "downloaded", "already_exist", "skipped_by_snapshot", "not_downloadable", "skipped_by_skip_download", "skipped_by_range"]


class Scraper(Generic[WebtoonId]):  # MARK: SCRAPER
    """Abstract base class of scrapers.

    WebtoonScraper는 ABC인 이 Scraper 클래스와 이 클래스를 상속한 여러 다른 클래스들로 구성됩니다.

    Scraper 클래스에는 여러 속성이 있어 작동 방식을 tweak하거나 다운로드와 관련한 정보를 확인할 수 있습니다.

    Attributes:
        existing_episode_policy (Literal["skip", "raise", "download_again", "hard_check"], "skip"):
            다운로드받을 에피소드와 동일한 이름의 디렉토리가 이미 존재할 때 어떤 작업을 취할 지를 결정합니다.
            * skip: 조건 없이 다운로드를 건너뜁니다.
            * raise: 예외를 발생시킵니다.
            * download_again: 해당 디렉토리를 삭제하고 다시 다운로드합니다.
            * hard_check: 이미지를 완전히 다시 다운로드하지는 않고, 만약 이미지의 개수가
                예상한 것과 같은 경우 다운로드를 건너뜁니다. skip에 비해 훨씬 느립니다.

            WebtoonScraper는 기본적으로 예상되지 않은 예외가 발생하는 상황에서도 에피소드 디렉토리의 완전성을 보장하기 때문에
            skip(기본값)을 그대로 사용하는 것을 추천합니다.

        use_progress_bar (bool, True):
            진행 표시줄을 사용할지 하지 않을지 결정합니다.
            터미널이 진행 표시줄을 제대로 표시하지 못하거나
            진핸 표시줄보다 logger로 진행 상황을 남기는 것이
            유용한 경우 False로 설정해 logger를 사용하는 것으로
            변경할 수 있습니다.

        ignore_snapshot (bool, False):
            `webtoon snap ...` 명령어로 생성된 파일 스냅샷을 무시합니다.
            스냅샷이 무엇이고 어떤 역할을 하는지 모른다면 굳이 건드릴 필요가 없습니다.
            스냅샷에 대한 더욱 자세한 정보는 문서를 참고해 주세요.

        skip_thumbnail_download (bool, False):
            썸네일을 다운로드하지 않습니다.
            썸네일이 다운로드되어있는 것을 확신하거나 썸네일 다운로드가 필요 없을 경우 사용합니다.

        이 아래는 데이터 속성들입니다. 기본값이 설정되어 있으나 사용자가 선호에 따라 변경될 수 있도록 디자인되어 있습니다.

        base_directory (Path | str, Path.cwd()):
            웹툰 디렉토리가 위치할 *베이스 디렉토리*를 결정합니다.
            기본값은 current working directory로 설정되어 있습니다.
            웹툰 디렉토리 자체를 변경하고 싶다면 `Scraper.get_webtoon_directory_name()` override해야 합니다.

        extra_info_scraper (ExtraInfoScraper):
            이미지 이외의 정보(댓글, 작가의 말, 별점 등)나 기타 프로세싱이 요구될 때 사용됩니다.
            Scraper.__init__()은 extra_info_scraper가 구현되어 있지 않았을 때
            자동으로 EXTRA_INFO_SCRAPER_FACTORY을 통해 extra_info_scraper를 구현하도록 되어 있습니다.

        이 아래는 `Scraper.fetch_all()`을 실행할 경우 할당되는 속성입니다.

        webtoon_thumbnail_url (str):
            웹툰의 썸네일을 다운로드할 때 사용되는 URL입니다.
            일반 사용자가 조작할 이유는 없습니다.

        title (str):
            웹툰의 제목입니다.

        author (str):
            웹툰의 저자입니다.

        episode_titles (list[str | None]):
            웹툰의 각 에피소드에 따른 제목을 열거입니다.
            해당 에피소드가 다운로드 가능하지 않은 경우 값은 None이 됩니다.

        episode_ids (list[int | None]):
            웹툰의 각 에피소드를 구분할 수 있는 id입니다.
            기본 타입은 int로 되어 있지만 구현에 따라 어떤 타입이던 될 수 있습니다.
            해당 에피소드가 다운로드 가능하지 않은 경우 값은 None이 됩니다.

        이 아래는 프로퍼티나 기본으로 할당되는 값입니다.

        client (httpc.AsyncClient):
            Scraper에서 (거의) 모든 네트워크가 오가는 것을 총괄하는 HTTP 클라이언트입니다.
            모든 네트워크가 이 클라이언트를 통해야 하지만 일부 구현은 이를 무시하고 다른
            방법으로 네트워크로 통신할 수 있습니다.

        headers (httpx.Headers):
            통신에 사용될 헤더입니다. `self.client.headers`의 간단한 지름길입니다.

        cookie (str | None, property):
            header에 쿠키를 설정하는 프로퍼티입니다. 일부 구현은 쿠키를 이 프로퍼티를 거치는 것을
            전제하므로 만약 쿠키 문자열을 설정할 일이 있다면 반드시 이 프로퍼티를 거쳐야 합니다.

        이 아래는 클래스 속성입니다. 새로운 스크래퍼를 디자인할 때 값을 설정해주어야 합니다.

        PLATFORM (str):
            스크래퍼가 다운로드하는 플랫폼을 표현하는 문자열입니다.
            이 값은 CLI에서 `--platform` 플래그와 함께 사용되며
            스크래퍼 구현들을 저장할 때 기준으로 사용됩니다.
            이 사양은 구현되어 있지 않으니 직접 지정해야 합니다.
            스크래퍼를 구현하면 자동으로 등록됩니다.
            따라서 만약 이미 있는 스크래퍼와 이름이 중복될 경우
            경고가 발생하니 이를 방지하려면 PLATFORM 값을 새로 지정하거나
            서브클래스 파라미터를 override=True로 두어야 합니다.
            스크래퍼 자동 등록을 회피하려면 register=False로 두세요.

        download_interval (int):
            각 다운로드 사이에 쉬는 시간을 정합니다.

        EXTRA_INFO_SCRAPER_FACTORY (type[ExtraInfoScraper]):
            self.extra_info_scraper가 설정되어 있지 않았을 때 초기화할 때 사용할
            함수나 클래스를 저장합니다. 자세한 설명은 extra_info_scraper을 참고해 주세요.
    """

    # MARK: CLASS VARIABLES
    PLATFORM: ClassVar[str]
    download_interval: int | float = 0.5
    EXTRA_INFO_SCRAPER_FACTORY: type[ExtraInfoScraper] = ExtraInfoScraper
    LOGIN_URL: str
    information_vars: dict[str, None | str | Path | Callable] = dict(
        title=None,
        platform="PLATFORM",
        webtoon_thumbnail_url=None,
        episode_ids=None,
        episode_titles=None,
        author=None,
        download_status="download_status",
        webtoon_dir_name="_webtoon_directory_format",
        episode_dir_name="_episode_directory_format",
        episode_dir_names=None,
    )
    information_to_exclude: tuple[str, ...] = "extra/", "credentials/"

    def __init__(self, webtoon_id: WebtoonId) -> None:
        """스크래퍼를 웹툰 id를 받아 초기화합니다.

        Args:
            webtoon_id (WebtoonId):
                해당하는 플랫폼에서 웹툰을 식별할 수 있는 id입니다.
                자세한 설명은 실제 구현을 참고하세요.
                URL이 **아닌** 웹툰 id가 인자라는 점을 주의하세요.
                URL을 이용하고 싶다면 `Scraper.from_url(URL)`을 사용하셔야 합니다.
        """
        # network settings
        self.client = httpc.AsyncClient(
            retry=3,
            timeout=10,
            raise_for_status=True,
            follow_redirects=False,
            # 어차피 업스트림에서 복사되기에 복사 없이 보내도 괜찮음.
            headers=httpc.HEADERS,
            verify=ssl.create_default_context(),
        )
        self.json_headers = httpc.HEADERS | {
            "accept": "application/json, text/plain, */*",
            "content-type": "application/json",
        }

        # settings attributes
        self.existing_episode_policy: Literal["skip", "raise", "download_again", "hard_check"] = "skip"
        self.use_progress_bar: bool = True
        self.ignore_snapshot: bool = False
        self.skip_thumbnail_download: bool = False
        self.previous_status_to_skip: list[DownloadStatus] = []

        # data attributes
        self.author: str | None = None  # 스크래퍼들이 모두 author 필드를 구현하면 제거하기
        self.webtoon_id: WebtoonId = webtoon_id
        self.base_directory: Path | str = Path.cwd()
        self.skip_download: list[int] = []
        """0-based index를 사용해 다운로드를 생략할 웹툰을 결정합니다."""
        self._download_status: Literal["downloading", "nothing", "canceling"] = "nothing"
        self._tasks: asyncio.Queue[asyncio.Future] = asyncio.Queue()
        """_tasks에 값을 등록해 두면 스크래퍼가 종료될 때 해당 task들을 완료하거나 취소합니다."""
        self._cookie_set = False
        """쿠키가 사용자에 의해 변경되었는지를 검사합니다."""
        self._webtoon_directory_format: str = "{title}({identifier})"
        self._episode_directory_format: str = "{no:04d}. {episode_title}"

        self.callbacks = CallbackManager(dict(scraper=self))
        # initialize extra info scraper
        self.extra_info_scraper

    def __init_subclass__(cls, register: bool = True, override: bool = False) -> None:
        if not register:
            return
        platform_name = getattr(cls, "PLATFORM", None)
        if platform_name is None:
            return
        if not override and (registered_scraper := platforms.get(platform_name)):
            warnings.warn(
                f"Platform code {platform_name!r} has been already registered as Scraper {registered_scraper}.To suppress this warning, set class parameter `override` to True.",
                UserWarning,
                stacklevel=2,
            )
        platforms[platform_name] = cls

    # MARK: ABSTRACT METHODS

    @property
    def extra_info_scraper(self) -> ExtraInfoScraper:
        try:
            return self._extra_info_scraper
        except AttributeError:
            self.extra_info_scraper = self.EXTRA_INFO_SCRAPER_FACTORY()
            return self._extra_info_scraper

    @extra_info_scraper.setter
    def extra_info_scraper(self, extra: ExtraInfoScraper | None) -> None:
        try:
            prev_extra = self._extra_info_scraper
        except AttributeError:
            pass
        else:
            prev_extra.unregister(self)

        if extra is None:
            extra = self.EXTRA_INFO_SCRAPER_FACTORY()

        self._extra_info_scraper = extra
        extra.register(self)

    @abstractmethod
    async def get_episode_image_urls(self, episode_no: int) -> list[str] | None | Callback:
        """해당 회차를 구성하는 이미지들의 URL을 불러옵니다."""
        raise NotImplementedError

    @async_reload_manager
    @abstractmethod
    async def fetch_webtoon_information(self, *, reload: bool = False) -> None:
        """
        웹툰 자체에 대한 정보를 불러옵니다.

        Note:
            이 함수를 실행했을 때 반드시 webtoon_thumbnail_url과 title, author가 할당되어야 합니다.

        Args:
            reload (bool, False):
                이 값이 True라면 이미 한 번 이상 이 동일한 함수가 실행되었다라도 무시하고 실행합니다.
                함수 실행을 관리하는 코드는 reload_manager가 관리합니다.
                따라서 함수는 반드시 `@reload_manager` 데코레이터를 통해 감싸져야 하며, reload 파라미터를 사용하지 않더라도 구현해야 합니다.

        Raises:
            만약 에피소드를 분리하는 기능과 분리하기 어렵다면 UseFetchEpisode를 발생시킬 수도 있습니다. 이는 오류라기보다는 안내입니다.
            만약에 웹툰 id가 유효하지 않다면 InvalidWebtoonIdError를, 허용되지 않는 rating이라면 UnsupportedRatingError를,
            잘못된 인증 정보라면 InvalidAuthenticationError을 발생시킬 수 있지만 이외에도 저 많은 예외를 발생시킬 수 있으며 이는
            완전히 구현에 달려 있습니다.
        """
        self.webtoon_thumbnail_url: str
        self.title: str
        self.author: str | None
        raise NotImplementedError

    @async_reload_manager
    @abstractmethod
    async def fetch_episode_information(self, *, reload: bool = False) -> None:
        """웹툰의 에피소드에 대한 정보를 불러옵니다.

        Note:
            이 함수를 실행했을 때 반드시 episode_titles과 episode_ids가 할당되어야 합니다.
        """
        # list is invariant!
        self.episode_titles: list[str | None] | list[str]
        self.episode_ids: list[int | None] | list[int]
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def _extract_webtoon_id(cls, url: URL) -> WebtoonId | None:
        raise NotImplementedError

    @classmethod
    def _from_string(cls, string: str, /, **kwargs):
        """webtoon_id가 int가 아니라면 반드시 구현해야 합니다."""
        return cls(int(string), **kwargs)  # type: ignore

    # MARK: PUBLIC METHODS

    def download_webtoon(self, download_range: RangeType = None) -> None:
        """웹툰을 다운로드합니다.

        Jupyter 등 async 환경에서는 제대로 동작하지 않을 수 있습니다. 그럴 경우 async_download_webtoon을 사용하세요.

        기본적으로는 별다른 인자를 필요로 하지 않으며 다운로드받을 범위와 웹툰 모아서 보기를 할 때는
        추가적인 파라미터를 이용할 수 있습니다.

        Args:
            download_range: 다운로드할 회차의 범위를 정합니다.
        """
        try:
            asyncio.run(self.async_download_webtoon(download_range=download_range))
        except RuntimeError as exc:
            # 부가적인 기능이니 문제가 생기더라도 무시하고 진행함.
            with suppress(Exception):
                if "event loop" in exc.args[0]:
                    exc.add_note("Use `scraper.async_download_webtoon` in Jupyter or asyncio environment.")
            raise

    def _apply_skip_previously_failed(self) -> None:
        if to_skip := self.previous_status_to_skip:
            prev_episode_ids = self.directory_manager._old_information.get("episode_ids", [])
            download_status = self.directory_manager._old_information.get("download_status", [])
            id_status = dict(zip(prev_episode_ids, download_status, strict=True))
            self.skip_download.extend(i for i, episode_id in enumerate(self.episode_ids) if id_status.get(episode_id) in to_skip)

    async def async_download_webtoon(self, download_range: RangeType = None) -> None:
        """download_webtoon의 async 버전입니다. 자세한 설명은 download_webtoon의 문서를 참조하세요.

        Example:
            ```python
            $ python -m asyncio
            >>> from WebtoonScraper.scrapers import NaverWebtoonScraper
            >>> scraper = NaverWebtoonScraper(819217)
            >>> await scraper.async_download_webtoon()
            ...
            ```
        """
        if not self._cookie_set:
            logger.debug("Cookie is not set")
        if not getattr(self, "bearer", True):  # bearer가 있는데 None인 경우
            logger.debug("Bearer is not set")

        async with self.callbacks.context("setup", start_default=self.callbacks.default("Gathering data...")):
            await self.fetch_all()

        webtoon_directory = self._prepare_directory()
        await self.callbacks.async_callback("download_started", webtoon_directory=webtoon_directory)
        self.directory_manager = WebtoonDirectory(webtoon_directory, ignore_snapshot=self.ignore_snapshot)
        self.directory_manager.load()
        thumbnail_task = await self._download_thumbnail(webtoon_directory)

        self._apply_skip_previously_failed()

        try:
            if self._download_status != "nothing":
                logger.warning(f"Program status is not usual: {self._download_status!r}")
            self._download_status = "downloading"
            async with self.callbacks.context("download_episode", end_default=self.callbacks.default("The webtoon {scraper.title} download ended.")):
                await self._download_episodes(download_range, webtoon_directory)
            webtoon_directory = self._post_process_directory(webtoon_directory)

        except BaseException as exc:
            async with self.callbacks.context("download_ended") as context:
                # cancelling all tasks
                canceled_tasks = 0
                tasks = self._tasks
                while not tasks.empty():
                    task = tasks.get_nowait()
                    canceled_tasks += task.cancel()

                extras = dict(webtoon_directory=webtoon_directory, download_range=download_range)
                if thumbnail_task and not self.skip_thumbnail_download and not thumbnail_task.cancel():
                    extras["thumbnail_path"] = await thumbnail_task
                self._download_status = "nothing"
                context.update(exc=exc, extras=extras, canceled=canceled_tasks, is_successful=False)
            raise

        else:
            async with self.callbacks.context("download_ended") as context:
                await self._tasks.join()
                self._download_status = "nothing"
                extras = dict(webtoon_directory=webtoon_directory, download_range=download_range)
                if thumbnail_task and not self.skip_thumbnail_download:
                    extras["thumbnail_path"] = await thumbnail_task
                context.update(exc=None, extras=extras)

    async def fetch_all(self, reload: bool = False) -> None:
        """웹툰과 에피소드에 대한 정보를 모두 불러옵니다.

        Args:
            reload (bool, False):
                이 값이 False(기본값)라면 이 함수를 여러 번 실행하더라도 이미 한 번 실행되었었다면 다시 실행되지 않습니다.
                따라서 만약 정보를 불러왔는지 정확하게 알 수 없는 경우라면 느리거나 여러 번 요청이 갈 일이 걱정 없이 안심하고 실행할 수 있습니다.
                반대로 True일 때는 이전에 정보를 불러온 적이 있다라도 무시하고 함수를 다시 실행시킵니다.
        """
        with suppress(UseFetchEpisode):
            await self.fetch_webtoon_information(reload=reload)
        await self.fetch_episode_information(reload=reload)

    @classmethod
    def from_url(cls, url: str) -> Self:
        # NaverWebtoonScraper와 KakaoWebtoonScraper에 복사된 코드가 있음.
        """URL을 통해 스크래퍼를 초기화합니다."""
        try:
            webtoon_id: WebtoonId | None = cls._extract_webtoon_id(URL(url))
        except Exception as exc:
            raise URLError.from_url(url, cls) from exc

        if webtoon_id is None:
            raise URLError.from_url(url, cls)

        return cls(webtoon_id)

    def get_webtoon_directory_name(self) -> str:
        """웹툰 디렉토리의 이름을 결정합니다."""
        now = datetime.now()
        directory_name = self._webtoon_directory_format.format(
            title=self.title,
            identifier=self._get_identifier(),
            webtoon_id=self.webtoon_id,
            author=self.author or "",
            platform=self.PLATFORM,
            datetime=now,
            date=now.strftime("%Y-%m-%d"),
            time=now.strftime("%H:%M:%S"),
        )
        return self._safe_name(directory_name)

    def _get_identifier(self) -> str:
        webtoon_id = self.webtoon_id
        if isinstance(webtoon_id, tuple | list):  # 흔한 sequence들. 다른 사례가 있으면 추가가 필요할 수도 있음.
            return ", ".join(map(str, webtoon_id))
        else:  # 보통 문자열이나 정수
            return f"{webtoon_id}"

    async def aclose(self) -> None:
        """스크래퍼를 닫습니다. `Scraper.stop()` 메서드를 사용하기에 상당히 불안정합니다."""
        self.stop()
        if self.use_progress_bar:
            self.progress.stop()
        await self.client.aclose()
        if getattr(self, "_progress", None):
            self._progress.stop()
            if not TYPE_CHECKING:
                self._progress = None

    def stop(self) -> None:
        """웹툰의 에피소드 다운로드를 '정중하게' 종료합니다.

        다른 스레드에서 웹툰 다운로드를 종료하고 싶은 경우 유용합니다.
        다만 이는 예외 등의 다른 방법에 비해 매우 느리고 함수가 종료되었더라도
        다운로드가 완전히 종료되었다고 확정할 수 없고 잘못 작동할 우려가 있으니
        예외를 사용할 수 있다면 예외를 사용하는 것을 강력히 주천합니다.
        """
        if self._download_status == "downloading":
            self._download_status = "canceling"
            while self._download_status == "canceling":
                time.sleep(0.1)
            time.sleep(0.1)

    # MARK: PROPERTIES

    @property
    def progress(self) -> progress.Progress:
        if getattr(self, "_progress", None):
            return self._progress
        self._progress = progress.Progress(
            progress.SpinnerColumn(spinner_name="aesthetic"),
            progress.TextColumn("[progress.description]{task.description}"),
            progress.BarColumn(bar_width=None),
            progress.TaskProgressColumn(),
            progress.TimeRemainingColumn(),
            progress.TextColumn("[progress.remaining]ETA"),
            progress.TimeElapsedColumn(),
            console=console,
            transient=False,
            expand=True,
        )
        self._progress.start()
        return self._progress

    @property
    def cookie(self) -> str | None:
        headers = self.headers
        return headers.get("Cookie", headers.get("cookie"))

    @cookie.setter
    def cookie(self, value: str) -> None:
        self._cookie_set = True
        self._set_cookie(value)

    @property
    def headers(self) -> httpx.Headers:
        return self.client.headers

    @headers.setter
    def headers(self, value) -> None:
        self.headers.clear()
        self.headers.update(value)
        self.json_headers.clear()
        self.json_headers.update(value)

    # MARK: PRIVATE METHODS

    def _set_cookie(self, value: str) -> None:
        self.headers.update({"Cookie": value})
        self.json_headers.update({"Cookie": value})

    def _apply_options(self, options: dict[str, str], /) -> None:
        if options:
            for option, value in options.items():
                self._apply_option(option.strip().lower().replace("_", "-"), value)

    def _apply_option(self, option: str, value: str) -> None:
        logger.warning(f"Unknown option {option!r} for {self.PLATFORM} scraper with value: {value!r}")

    @staticmethod
    def _as_boolean(value: str) -> bool:
        # sqlite에서 boolean pragma statement를 처리하는 방식을 참고함
        # https://www.sqlite.org/pragma.html
        match value.strip().lower():
            case "1" | "yes" | "true" | "on":
                return True
            case "0" | "no" | "false" | "off":
                return False
            case other:
                raise ValueError(f"{other!r} can't be represented as boolean.")

    async def _download_episodes(self, download_range: RangeType, webtoon_directory: Path) -> None:
        total_episodes = len(self.episode_ids)
        self.download_status: list[DownloadStatus | None] = [None] * total_episodes
        self.episode_dir_names: list[str | None] = [None] * total_episodes
        if self.use_progress_bar:
            task = self.progress.add_task("Setting up...", total=total_episodes)
            self.progress_task_id = task

        try:
            for episode_no in range(total_episodes):
                if self._download_status == "canceling":
                    raise KeyboardInterrupt

                if self.use_progress_bar:
                    self.progress.advance(task)

                episode_title = self.episode_titles[episode_no]
                context: dict = dict(episode_no=episode_no, episode_no1=episode_no + 1, short_ep_title=episode_title and _shorten(episode_title), total_ep=len(self.episode_ids))

                if episode_no in self.skip_download:
                    reason = "skipped_by_skip_download"
                    description = "because the episode is included in skip_download"
                    await self._episode_skipped(reason, description, level="debug", **context)
                    continue
                # download_range는 1-based indexing이니 조정이 필요함
                if download_range is not None and episode_no + 1 not in download_range:
                    reason = "skipped_by_range"
                    description = "because of the set range"
                    await self._episode_skipped(reason, description, level="debug", **context)
                    continue

                await self._download_episode(episode_no, context)
        finally:
            if self.use_progress_bar:
                self.progress.remove_task(task)
                if self.progress.tasks:
                    logger.warning("Can't stop progress since it's in use.")
                else:
                    self.progress.stop()

    async def _episode_skipped(self, reason: DownloadStatus, description: str, *, no_progress: bool = False, episode_no, level: LogLevel = "info", **context):
        """에피소드 다운로드를 건너뛸 때 사용하는 콜백입니다."""
        if (ep_title := self.episode_titles[episode_no]) is None:
            short_ep_title = f"#{episode_no + 1}"
            msg_format = "[{total_ep}/{episode_no1}] The episode is skipped {description}"
        else:
            short_ep_title = _shorten(ep_title)
            msg_format = "[{total_ep}/{episode_no1}] The episode '{short_ep_title}' is skipped {description}"

        # 원래대로면 context를 더럽히면 안 되지만 어차피 skip이 끝나면 context는 더 이상 사용되지 않으니 괜찮음
        # 이 방식이 아리나 직접 async_callback에 넣으면 "got multiple values for keyword argument 'short_ep_title'"
        # 하고 오류가 발생함
        context.update(
            description=description,
            reason=reason,
            short_ep_title=short_ep_title,
            episode_no=episode_no,
            episode_no1=episode_no + 1,
        )

        self.download_status[episode_no] = reason

        if no_progress:
            await self.callbacks.async_callback(
                "download_skipped",
                self.callbacks.default(
                    msg_format,
                    level=level,
                ),
                **context,
            )
        else:
            await self.callbacks.async_callback(
                "download_skipped",
                self.callbacks.default(
                    msg_format,
                    progress_update="{short_ep_title} skipped",
                    level=level,
                ),
                **context,
            )

    async def _download_episode(self, episode_no: int, context: dict) -> None:
        episode_title = self.episode_titles[episode_no]
        if episode_title is None:
            return await self._episode_skipped("not_downloadable", "because the episode has empty title", level="debug", no_progress=True, **context)
        now = datetime.now()
        directory_name = self._safe_name(
            self._episode_directory_format.format(
                no=episode_no + 1,
                no0=episode_no,
                episode_title=episode_title,
                title=self.title,
                webtoon_id=self.webtoon_id,
                author=self.author,
                platform=self.PLATFORM,
                datetime=now,
                date=now.strftime("%Y-%m-%d"),
                time=now.strftime("%H:%M:%S"),
            )
        )
        self.episode_dir_names[episode_no] = directory_name

        match await self.directory_manager.check_episode_directory(
            self,
            episode_no,
            directory_name,
            context,
        ):
            case None:
                return
            case episode_directory, image_urls:
                pass
            case _:
                raise Unreachable

        # download images from urls
        try:
            episode_directory.mkdir(exist_ok=True)
            await self._download_episode_images(episode_no, image_urls, episode_directory)
        except BaseException as exc:
            exc.add_note(f"Exception occurred when downloading images of {episode_no + 1}. {episode_title!r}")
            await self.callbacks.async_callback("cancelling", **context)
            shutil.rmtree(episode_directory)
            raise

        # send done callback message
        self.download_status[episode_no] = "downloaded"
        await self.callbacks.async_callback("download_completed", self.callbacks.default("[{total_ep}/{episode_no1}] {short_ep_title!r} downloaded", progress_update="{short_ep_title} downloaded"), **context)

    async def _download_episode_images(self, episode_no: int, image_urls: list[str], episode_directory: Path) -> None:
        async with asyncio.TaskGroup() as group:
            for index, url in enumerate(image_urls, 1):
                download_task = self._download_image(
                    url,
                    episode_directory,
                    f"{index:03d}",
                    episode_no=episode_no,
                )
                group.create_task(download_task)

    def _get_information(self):
        """information.json에 탑재할 정보를 갈무리합니다.

        Note:
            information_vars에 설정된 값을 바탕으로 탑재할 정보를 결정하는데, 그 규칙은 아래와 같습니다.
            * information_vars의 키는 `information.json`의 디렉토리에서의 위치를 결정하고, 서브카테고리는 `/`으로 분리됩니다.
                즉, `spam`이 키라면 `information.json`에서 `spam` 키에 값이 저장되며, `ham/hello`이라면 `information.json`의
                `ham`이라는 딕셔너리의 `hello` 키에 값이 저장됩니다.
            * information_vars의 값은 None이거나 문자열, callable일 수 있습니다.
        """
        _ABSENT = object()
        to_exclude = set(self.information_to_exclude)
        information = {}
        for original_name, to_fetch in self.information_vars.items():
            subcategory, sep, remains = original_name.partition("/")

            # Exclude patterns
            if subcategory + "/" in to_exclude:
                continue
            if original_name in to_exclude:
                continue
            if not subcategory and "/" + remains in to_exclude:
                continue
            if remains in to_exclude:
                continue

            if sep:
                to_store = information[subcategory] = information.get(subcategory, {})
                name = remains
            else:
                to_store = information
                name = original_name

            old_information = self.directory_manager._old_information
            fetch_failed = []
            match to_fetch:
                case None:
                    value = getattr(self, name, _ABSENT)
                    old_value = old_information.get(name, _ABSENT)
                    if value is _ABSENT:
                        if old_value is _ABSENT:
                            fetch_failed.append(original_name)
                            logger.warning(f"{type(self).__name__}.{name} does not exist, and it'll be excluded from information.json.")
                        continue

                    value = self._normalize_information(value)
                    if isinstance(old_value, dict) and isinstance(value, dict):
                        # old_value가 value에 덮어씌어져야 하니 `.update()`나 `|=`를 사용하면 안 됨!
                        value = old_value | value
                    to_store[name] = value

                case str(to_fetch):
                    value = getattr(self, to_fetch, _ABSENT)
                    if value is _ABSENT:
                        fetch_failed.append(original_name)
                        logger.warning(f"{type(self).__name__}.{name} does not exist, and it'll be excluded from information.json.")
                    else:
                        to_store[name] = self._normalize_information(value)

                case to_fetch if callable(to_fetch):
                    old_value = old_information.get(name, _ABSENT)
                    if old_value is _ABSENT:
                        to_store[name] = self._normalize_information(to_fetch(self, name))
                    else:
                        to_store[name] = self._normalize_information(to_fetch(self, name, old_value))

                case other:
                    raise ValueError(f"Unexpected information value: {other!r}")

        return information

    def _normalize_information(self, information):
        match information:
            case int() | str() | float() | None as value:
                return value

            case Mapping() as mapping:
                return {str(key): self._normalize_information(value) for key, value in mapping.items()}

            case list(seq):
                return [self._normalize_information(item) for item in seq]

            case Path() as path:
                return str(path)  # absolute path로 변환해야 할까?

            case other:
                logger.warning(f"Unexpected type: {type(other).__name__} of {other!r}")
                return other

    async def _download_image(self, url: str, directory: Path, name: str, episode_no: int | None = None) -> Path:
        try:
            response = await self.client.get(url)
            image_raw: bytes = response.content
            file_extension = infer_filetype(response.headers.get("content-type"), image_raw)
            image_path = directory / self._safe_name(f"{name}.{file_extension}")
            image_path.write_bytes(image_raw)
            return image_path
        except Exception as exc:
            exc.add_note(f"Exception occurred when downloading image from {url!r}")
            raise

    def _prepare_directory(self) -> Path:
        webtoon_directory_name = self.get_webtoon_directory_name()
        webtoon_directory = Path(self.base_directory, webtoon_directory_name)
        webtoon_directory.mkdir(parents=True, exist_ok=True)
        return webtoon_directory

    def _post_process_directory(self, webtoon_directory: Path) -> Path:
        """모아서 보기나 information.json, webtoon.html 등이 위치할 디렉토리를 재안내합니다.

        레진코믹스의 언셔플러 구현에서 유일하게 사용됩니다.
        """
        return webtoon_directory

    @staticmethod
    def _safe_name(name: str) -> str:
        """일반 문자열을 파일명으로 사용 가능한 문자열로 변경합니다.

        이 함수는 파일 '경로'를 처리하도록 설계되지 않았기에
        경로가 파일 이름을 받는다는 점을 유의하세요.
        """
        return pf.convert(html.unescape(name))

    @staticmethod
    def _build_information_dict(*auto_keys, subcategory: str | None = None, **manual_keys) -> dict:
        if not subcategory:
            return dict.fromkeys(auto_keys) | manual_keys

        return {f"{subcategory}/{key}": None for key in auto_keys} | {f"{subcategory}/{key}": value for key, value in manual_keys.items()}

    @staticmethod
    def _cookie_get(cookie: str | None, key: str) -> str | None:
        if cookie is None:
            return None
        parsed = SimpleCookie(cookie)
        result = parsed.get(key, None)
        return result if result is None else result.value
        # return {key: morsel.value for key, morsel in parsed.items()}

    async def _download_thumbnail(self, webtoon_directory: Path) -> None | asyncio.Task[Path]:
        if self.skip_thumbnail_download:
            return None

        try:
            contents = os.listdir(webtoon_directory)
        except Exception:
            snapshot_contents = self.directory_manager._get_snapshot_contents(webtoon_directory)
            contents = list(snapshot_contents) if isinstance(snapshot_contents, dict) else []
        else:
            snapshot_contents = self.directory_manager._get_snapshot_contents(webtoon_directory)
            if isinstance(snapshot_contents, dict):
                # 중복된 컨텐츠가 나타날 수도 있지만 상관없음
                contents += snapshot_contents

        if any(content.startswith("thumbnail.") for content in contents):
            return None

        async with self.callbacks.context("download_thumbnail"):
            return asyncio.create_task(self._download_image(self.webtoon_thumbnail_url, webtoon_directory, "thumbnail"))


class WebtoonDirectory:
    """웹툰 디렉토리를 관리하는 클래스입니다.

    이 클래스는 웹툰 디렉토리의 생성, 정보 불러오기, 스냅샷 관리 등을 담당합니다.
    """

    def __init__(self, webtoon_directory: Path, ignore_snapshot: bool = False) -> None:
        self.webtoon_directory = webtoon_directory
        self.ignore_snapshot = ignore_snapshot

    def load(self) -> None:
        self._load_snapshot(self.webtoon_directory)
        self._load_information(self.webtoon_directory)

    def _get_snapshot_contents(self, path: Path) -> str | dict | None:
        result = self._snapshot_data.get("contents")
        if not result:
            return None
        parts = path.relative_to(self.webtoon_directory).parts
        for part in parts:
            match result:
                case str():
                    return None
                case dict(result):
                    try:
                        result = result[part]
                    except KeyError:
                        return None
        return result

    def _load_snapshot(self, webtoon_directory: Path) -> None:
        """스냅샷 정보를 불러옵니다. self.ignore_snapshot이 True이거나 스냅샷이 없거나 훼손되었다면 라면 값을 불러오지 않습니다."""
        self._snapshot_data: dict
        if self.ignore_snapshot:
            self._snapshot_data = {}
            return

        snapshot_path = webtoon_directory.parent / f"{webtoon_directory.name}.snapshots"
        try:
            self._snapshot_data = json.loads(snapshot_path.read_text("utf-8"))
        except Exception:
            self._snapshot_data = {}

    def _snapshot_contents_info(self, path: Path) -> Literal["file", "directory"] | None:
        match self._get_snapshot_contents(path):
            case None:
                return None
            case dict():
                return "directory"
            case "exists":
                return "file"
            case other:
                raise TypeError(f"Unexpected type: {type(other).__name__}")

    def _load_information(self, webtoon_directory: Path) -> None:
        old_information = load_information_json(webtoon_directory)
        if not old_information:
            old_information = {}
        self._old_information = old_information

    def _check_directory(
        self,
        episode_directory: Path,
        image_urls: list,
    ) -> bool:
        """해당 폴더 내 내용물이 에피소드 디렉토리로 적합한지 조사합니다.

        Returns:
            False를 return한다면 회차를 다운로드해야 한다는 의미입니다.
            True를 return하면 해당 회차가 이미 완전히 다운로드되어 있으며, 따라서 다운로드를 지속할 이유가 없음을 의미합니다.
        """

        try:
            real_contents = os.listdir(episode_directory)
        except Exception:
            real_contents = []
        snapshot_contents = self._get_snapshot_contents(episode_directory) or ()
        directory_contents = {*real_contents, *snapshot_contents}

        normal_image_regex = DirectoryState.Image(is_merged=False).pattern()
        return len(image_urls) == len(directory_contents) and all(normal_image_regex.match(file) for file in directory_contents)

    async def check_episode_directory(
        self,
        scraper: Scraper,
        episode_no: int,
        directory_name: str,
        context: dict,
    ):
        episode_directory = self.webtoon_directory / directory_name
        episode_at_snapshot = self._snapshot_contents_info(episode_directory)

        # 동명의 파일이 있는지 확인
        is_file_exists = episode_directory.is_file()
        is_file_exists_in_snapshot = episode_at_snapshot == "file"
        if is_file_exists or is_file_exists_in_snapshot:
            context.update(is_file=is_file_exists, is_snapshot=is_file_exists_in_snapshot)
            if scraper.existing_episode_policy != "skip":
                raise FileExistsError(f"A file named {episode_directory!r} exists on webtoon directory.")
        if is_file_exists:
            return await scraper._episode_skipped("already_exist", "because of existing file", **context)
        elif is_file_exists_in_snapshot:
            return await scraper._episode_skipped("skipped_by_snapshot", "because of existing file in the snapshot", **context)

        # 디렉토리가 존재하고 비어있지 않는지 확인
        if episode_at_snapshot == "directory" and self._get_snapshot_contents(episode_directory):
            if scraper.existing_episode_policy == "raise":
                raise FileExistsError(f"Directory at {episode_directory} already exists. Please delete the directory.")
            elif scraper.existing_episode_policy == "skip":
                return await scraper._episode_skipped("skipped_by_snapshot", "because it's downloaded already in snapshot", by_file=False, **context)
            else:
                not_empty_dir = True
        elif episode_directory.is_dir() and os.listdir(episode_directory):
            if scraper.existing_episode_policy == "raise":
                raise FileExistsError(f"Directory at {episode_directory} already exists. Please delete the directory.")
            elif scraper.existing_episode_policy == "skip":
                return await scraper._episode_skipped("already_exist", "because it's downloaded already", by_file=True, **context)
            else:
                not_empty_dir = True
        else:
            not_empty_dir = False

        # 다운로드 직전에 메시지를 보냄
        await scraper.callbacks.async_callback("downloading", scraper.callbacks.default(progress_update="downloading {short_ep_title}"), **context)

        # fetch image urls
        time.sleep(scraper.download_interval)  # 실질적인 외부 요청을 보내기 직전에만 interval을 넣음.
        try:
            image_urls = await scraper.get_episode_image_urls(episode_no)
        # 기본적으로 get_episode_image_urls는 실패해서는 안 된다.
        # 그런 상황이 있을 경우 warning을 내부적으로 내보내며 None을 리턴해야 한다.
        # 따라서 다른 경우들과 달리 raise를 하는 것이다.
        except BaseException as exc:
            exc.add_note(f"Exception occurred when gathering images of {episode_no + 1}. {scraper.episode_titles[episode_no]!r}")
            await scraper.callbacks.async_callback("get_episode_images_failed", **context)
            raise

        if isinstance(image_urls, Callback) or not image_urls:
            callback = image_urls if isinstance(image_urls, Callback) else None
            with suppress(Exception):
                episode_directory.rmdir()
            scraper.download_status[episode_no] = "failed"
            await scraper.callbacks.async_callback(
                "download_failed",
                callback or scraper.callbacks.default(
                    "[{total_ep}/{episode_no1}] The episode '{short_ep_title}' is failed {description}",
                    progress_update="{short_ep_title} skipped",
                    level="warning",
                    log_with_progress=True,
                ),
                reason="gathering_images_failed",
                description="because no images are found",
                **context,
            )
            return

        # check integrity if specified
        if not_empty_dir and scraper.existing_episode_policy == "hard_check":
            if self._check_directory(episode_directory, image_urls):
                with suppress(Exception):
                    episode_directory.rmdir()
                return await scraper._episode_skipped("already_exist", "because of intact existing directory", intact=True, **context)

            shutil.rmtree(episode_directory)
            episode_directory.mkdir()

        return episode_directory, image_urls
