from __future__ import annotations

import asyncio
from collections import defaultdict
import html
import json
import os
import shutil
import ssl
import time
from abc import abstractmethod
from collections.abc import Callable, Container, Mapping
from contextlib import contextmanager, suppress
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    ClassVar,
    Generic,
    Literal,
    TypeVar,
    Self,
    overload,
)
import warnings

import filetype
import httpc
import httpx
import pyfilename as pf
from filetype.types import IMAGE
from rich import progress
from yarl import URL

from ..base import console, logger, platforms
from ..directory_state import (
    DIRECTORY_PATTERNS,
    NORMAL_IMAGE,
)
from ..exceptions import (
    InvalidURLError,
    UseFetchEpisode,
)
from ._helpers import EpisodeRange, ExtraInfoScraper, async_reload_manager
from ._helpers import shorten as _shorten

WebtoonId = TypeVar("WebtoonId")
CallableT = TypeVar("CallableT", bound=Callable)
RangeType = EpisodeRange | Container[WebtoonId] | None
DownloadStatus = Literal["failed", "downloaded", "already_exist", "skipped_by_snapshot", "not_downloadable"]


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

            -----
            이 아래는 데이터 속성들입니다. 기본값이 설정되어 있으나 사용자가 선호에 따라 변경될 수 있도록 디자인되어 있습니다.

        base_directory (Path | str, Path.cwd()):
            웹툰 디렉토리가 위치할 *베이스 디렉토리*를 결정합니다.
            기본값은 current working directory로 설정되어 있습니다.
            웹툰 디렉토리 자체를 변경하고 싶다면 `Scraper.get_webtoon_directory_name()` override해야 합니다.

        extra_info_scraper (ExtraInfoScraper):
            이미지 이외의 정보(댓글, 작가의 말, 별점 등)나 기타 프로세싱이 요구될 때 사용됩니다.
            Scraper.__init__()은 extra_info_scraper가 구현되어 있지 않았을 때
            자동으로 EXTRA_INFO_SCRAPER_FACTORY을 통해 extra_info_scraper를 구현하도록 되어 있습니다.

            -----
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

            -----
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

            -----
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

        DOWNLOAD_INTERVAL (int):
            각 다운로드 사이에 쉬는 시간을 정합니다.

        EXTRA_INFO_SCRAPER_FACTORY (type[ExtraInfoScraper]):
            self.extra_info_scraper가 설정되어 있지 않았을 때 초기화할 때 사용할
            함수나 클래스를 저장합니다. 자세한 설명은 extra_info_scraper을 참고해 주세요.
    """

    # MARK: CLASS VARIABLES

    # 이 변수들은 웹툰 플랫폼에 종속적이기에 클래스 상수로 분류됨.
    PLATFORM: ClassVar[str]
    DOWNLOAD_INTERVAL: ClassVar[int | float] = 0
    INFORMATION_VARS: ClassVar[dict[str, None | str | Path | Callable]] = dict(
        title=None,
        platform="PLATFORM",
        webtoon_thumbnail_url=None,
        episode_ids=None,
        episode_titles=None,
        author=None,
        download_status="download_status",
    )
    EXTRA_INFO_SCRAPER_FACTORY: type[ExtraInfoScraper] = ExtraInfoScraper
    TASK_QUEUE_FACTORY: Callable = asyncio.Queue

    def __init__(self, webtoon_id: WebtoonId, *, register_extra: bool = True) -> None:
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
            headers=dict(httpc.HEADERS),
            verify=ssl.create_default_context(),
        )

        # settings attributes
        self.existing_episode_policy: Literal["skip", "raise", "download_again", "hard_check"] = "skip"
        self.use_progress_bar: bool = True
        self.ignore_snapshot: bool = False
        self.save_extra_information: bool = False
        self.skip_thumbnail_download: bool = False

        # data attributes
        self.author: str | None = None  # 스크래퍼들이 모두 author 필드를 구현하면 제거하기
        self.webtoon_id: WebtoonId = webtoon_id
        self.base_directory: Path | str = Path.cwd()
        self._download_status: Literal["downloading", "nothing", "canceling"] = "nothing"
        self._triggers: defaultdict[str, list[Callable]] = defaultdict(list)
        self._tasks: asyncio.Queue[asyncio.Future] = self.TASK_QUEUE_FACTORY()
        """_tasks에 값을 등록해 두면 스크래퍼가 종료될 때 해당 task들을 완료하거나 취소합니다."""

        # initialize extra info scraper
        if not getattr(self, "extra_info_scraper", None):
            self.extra_info_scraper = self.EXTRA_INFO_SCRAPER_FACTORY()

        if register_extra:
            self.extra_info_scraper.register(self)

    def __init_subclass__(cls, register: bool = True, override: bool = False) -> None:
        if not register:
            return
        platform_name = getattr(cls, "PLATFORM", None)
        if platform_name is None:
            return
        if not override and (registered_scraper := platforms.get(platform_name)):
            warnings.warn(
                f"Platform code {platform_name!r} has been already registered as Scraper {registered_scraper}."
                f"To suppress this warning, set class parameter `override` to True.",
                UserWarning,
                stacklevel=2,
            )
        platforms[platform_name] = cls

    # MARK: ABSTRACT METHODS

    @abstractmethod
    async def get_episode_image_urls(self, episode_no: int) -> list[str] | None:
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
            exc.add_note("Use `scraper.async_download_webtoon` in Jupyter or asyncio environment.")
            raise

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
        with self._context_message("setup"):
            await self.fetch_all()

        webtoon_directory = self._prepare_directory()
        self.callback("initialize", webtoon_directory=webtoon_directory)

        if not self.skip_thumbnail_download or TYPE_CHECKING:
            try:
                contents = os.listdir(webtoon_directory)
            except Exception:
                pass
            else:
                if any(content.startswith("thumbnail.") for content in contents):
                    thumbnail_task = None
                else:
                    with self._context_message("download_thumbnail"):
                        thumbnail_task = asyncio.create_task(self._download_image(self.webtoon_thumbnail_url, webtoon_directory, "thumbnail"))

        try:
            if self._download_status != "nothing":
                logger.warning(f"Program status is not usual: {self._download_status!r}")
            self._download_status = "downloading"
            self._load_snapshot(webtoon_directory)
            with self._context_message("download_episode"):
                await self._download_episodes(download_range, webtoon_directory)
            webtoon_directory = self._post_process_directory(webtoon_directory)

        except BaseException as exc:
            with self._context_message("finalize") as context:
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
                context.update(exc=exc, extras=extras, canceled=canceled_tasks)
            raise

        else:
            with self._context_message("finalize") as context:
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

    @overload
    def register_callback(self, trigger: str, func: CallableT) -> CallableT: ...

    @overload
    def register_callback(self, trigger: str) -> Callable[[CallableT], CallableT]: ...

    def register_callback(self, trigger: str, func: Callable | None = None):
        """특정 callback 트리거가 발생했을 때 실행할 컬백을 등록합니다.

        Example:
            ```python
            scraper = Scraper.from_url(...)
            @scraper.register_callback("setup"):
            def startup_message(scraper: Scraper, finishing: bool, **context):
                if not finishing:
                    print("Download has been started!")
            scraper.download_webtoon()

            # output:
            # ...
            # Download has been started!
            # ...
            ```

        Note:
            이 메서드는 메서드로도 데코레이터로도 사용될 수 있습니다.
            callback과 마찬가지로 등록된 함수들도 진행을 멈추고 호출되니 지연되지 않도록 주의해야 합니다.

        Args:
            trigger (str):
                callback을 실행할 명령어를 결정합니다.
            func (Callable, optional):
                이 인자는 빠질 수 있으며, 빠질 경우 데코레이터로서 사용할 수 있습니다.
            함수는 func(**context)
        """
        if func is None:
            return lambda func: self.register_callback(trigger, func)

        self._triggers[trigger].append(func)
        return func

    def callback(self, situation: str, **context) -> None:
        """웹툰 다운로드의 중요한 순간들을 알림받습니다.

        Note:
            callback은 진행을 멈추고 호출되기 때문에 최대한 빨리 끝날 수 있도록 하는 것이 속도에 좋습니다.
        """
        match situation, context:
            case "setup", {"finishing": False}:
                logger.info("Fetching metadata...")
            case "download_thumbnail", {"finishing": True}:
                logger.info(f"Downloading {_shorten(self.title)}...")
            case "download_episode", {"finishing": True}:
                logger.info(f"The webtoon {self.title} download ended.")
            case ("indicate" | "download_skipped" | "download_failed" | "downloading_image" | "download_completed"), context:
                match situation:
                    case "indicate":
                        episode_no = None
                        description = context["description"]
                    case "download_skipped":
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
                        description = f"downloading {_shorten(episode_title)}"
                    case "download_completed":
                        episode_no = context["episode_no"]
                        episode_title = self.episode_titles[episode_no]
                        description = f"{_shorten(episode_title)} download completed"

                if self.use_progress_bar:
                    task_id = context["task_id"]
                    self.progress.update(task_id, description=description)
                else:
                    if episode_no is not None:
                        description = f"[{episode_no:02d}/{len(self.episode_titles):02d}] {description}"
                    logger.info(description)

            case "description", _:
                logger.info(context["description"])
            case "download_complete", _:
                is_download_successful = context["is_download_successful"]
                if is_download_successful:
                    episode_no = context["episode_no"]
                    episode_title = self.episode_titles[episode_no]
                    logger.info(f"Downloaded: #{episode_no} {_shorten(episode_title)}")
            case "finalize", {"finishing": False, "exc": exc}:
                logger.error("Aborting..." if isinstance(exc, KeyboardInterrupt) else "Finalizing...")
            case the_others, context if context:
                logger.debug(f"WebtoonScraper status: {the_others}, context: {context}")
            case the_others, _:
                logger.debug(f"WebtoonScraper status: {the_others}")

        if callbacks := self._triggers.get(situation):
            for callback in callbacks:
                callback(scraper=self, **context)

    @classmethod
    def from_url(cls, url: str) -> Self:
        """URL을 통해 스크래퍼를 초기화합니다."""
        try:
            webtoon_id: WebtoonId | None = cls._extract_webtoon_id(URL(url))
        except Exception as exc:
            raise InvalidURLError.from_url(url, cls) from exc

        if webtoon_id is None:
            raise InvalidURLError.from_url(url, cls)

        return cls(webtoon_id)

    def get_webtoon_directory_name(self) -> str:
        """웹툰 디렉토리의 이름을 결정합니다."""
        webtoon_id = self.webtoon_id
        if isinstance(webtoon_id, tuple | list):  # 흔한 sequence들. 다른 사례가 있으면 추가가 필요할 수도 있음.
            return self._safe_name(f"{self.title}({', '.join(map(str, webtoon_id))})")
        else:  # 보통 문자열이나 정수
            return self._safe_name(f"{self.title}({webtoon_id})")

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
            progress.SpinnerColumn(),
            *progress.Progress.get_default_columns(),
            progress.TimeElapsedColumn(),
            console=console,
            transient=False,
        )
        self._progress.start()
        return self._progress

    @property
    def cookie(self) -> str | None:
        headers = self.headers
        return headers.get("Cookie", headers.get("cookie"))

    @cookie.setter
    def cookie(self, value: str) -> None:
        self._set_cookie(value)

    @property
    def headers(self) -> httpx.Headers:
        return self.client.headers

    @headers.setter
    def headers(self, value) -> None:
        self.headers.clear()
        self.headers.update(value)

    # MARK: PRIVATE METHODS

    def _set_cookie(self, value: str) -> None:
        self.headers.update({"Cookie": value})

    def _apply_options(self, options: dict[str, str], /) -> None:
        if options:
            for option, raw_value in options.items():
                logger.warning(
                    f"Unknown option for {type(self).__name__}; {type(self).__name__} does not accept any option"
                    f": {option!r}. value: {raw_value!r}"
                )

    async def _download_episodes(self, download_range: RangeType, webtoon_directory: Path) -> None:
        total_episodes = len(self.episode_ids)
        self.download_status: list[DownloadStatus | None] = [None] * total_episodes
        if self.use_progress_bar:
            task = self.progress.add_task("Setting up...", total=total_episodes)

        try:
            for episode_no in range(total_episodes):
                context = dict(
                    episode_no=episode_no,
                )
                if self.use_progress_bar:
                    self.progress.advance(task)
                    context.update(task_id=task)

                # download_range는 1-based indexing이니 조정이 필요함
                if download_range is not None and episode_no + 1 not in download_range:
                    self.callback("download_skipped", by_range=True, **context)
                    continue
                if self._download_status == "canceling":
                    raise KeyboardInterrupt
                await self._download_episode(episode_no, webtoon_directory, context)
        finally:
            if self.use_progress_bar:
                self.progress.remove_task(task)

    async def _download_episode(self, episode_no: int, webtoon_directory: Path, context: dict | None = None) -> None:
        context = context or {}
        episode_title = self.episode_titles[episode_no]
        if episode_title is None:
            self.download_status[episode_no] = "not_downloadable"
            self.callback("download_skipped", by_empty_title=True)
            return
        directory_name = self._safe_name(f"{episode_no + 1:04d}. {episode_title}")
        episode_directory = webtoon_directory / directory_name
        episode_at_snapshot = self._snapshot_contents_info(episode_directory)

        # handle file existing situation
        as_file = episode_directory.is_file()
        as_file_snapshot = episode_at_snapshot == "file"
        if as_file or as_file_snapshot:
            if self.existing_episode_policy != "skip":
                raise FileExistsError(f"File at {episode_directory} already exists. Please delete the file.")
            self.download_status[episode_no] = "already_exist" if as_file else "skipped_by_snapshot"
            self.callback("download_skipped", is_file=as_file, is_snapshot=as_file_snapshot, **context)
            return

        # handle directory existing situation
        as_folder = episode_directory.is_dir()
        as_folder_snapshot = episode_at_snapshot == "directory"
        if as_folder or as_folder_snapshot:
            match self.existing_episode_policy:
                case "skip":
                    self.download_status[episode_no] = "already_exist" if as_folder else "skipped_by_snapshot"
                    self.callback("download_skipped", is_file=as_folder, is_snapshot=as_folder_snapshot, **context)
                    return

                case "raise":
                    raise FileExistsError(
                        f"Directory at {episode_directory} already exists. Please delete the directory."
                    )

        # fetch image urls
        time.sleep(self.DOWNLOAD_INTERVAL)  # 실제로 요청을 보내기 직전에 interval을 넣음.
        image_urls = await self.get_episode_image_urls(episode_no)
        if not image_urls:
            self.download_status[episode_no] = "failed"
            self.callback("download_failed", warning=True, **context)
            if not os.listdir(episode_directory):
                episode_directory.rmdir()
            return

        # check integrity if specified
        if (as_folder or as_folder_snapshot) and self.existing_episode_policy == "hard_check":
            if self._check_directory(episode_directory, image_urls):
                self.download_status[episode_no] = "already_exist"
                self.callback("download_skipped", intact=True, **context)
                if not as_folder:
                    episode_directory.rmdir()
                return

            shutil.rmtree(episode_directory)
            episode_directory.mkdir()

        # download images from urls
        try:
            if not as_folder:
                episode_directory.mkdir()

            async with asyncio.TaskGroup() as group:
                for index, url in enumerate(image_urls, 1):
                    group.create_task(self._download_image(
                        url,
                        episode_directory,
                        f"{index:03d}",
                    ))
        except BaseException:
            self.callback("cancelling", episode_no=episode_no, **context)
            shutil.rmtree(episode_directory)
            raise

        # send done callback message
        self.download_status[episode_no] = "downloaded"
        self.callback("download_completed", **context)
        return

    def _get_information(self, old_information: dict):
        """information.json에 탑재할 정보를 갈무리합니다.

        Note:
            INFORMATION_VARS에 설정된 값을 바탕으로 탑재할 정보를 결정하는데, 그 규칙은 아래와 같습니다.
            * INFORMATION_VARS의 키는 `information.json`의 디렉토리에서의 위치를 결정하고, 서브카테고리는 `/`으로 분리됩니다.
                즉, `spam`이 키라면 `information.json`에서 `spam` 키에 값이 저장되며, `ham/hello`이라면 `information.json`의
                `ham`이라는 딕셔너리의 `hello` 키에 값이 저장됩니다.
            * INFORMATION_VARS의 값은 None이거나 문자열, callable일 수 있습니다.
        """
        _ABSENT = object()
        information = {}
        for original_name, to_fetch in self.INFORMATION_VARS.items():
            subcategory, sep, remains = original_name.partition("/")
            if sep:
                to_store = information[subcategory] = information.get(subcategory, {})
                name = remains
            else:
                to_store = information
                name = original_name

            fetch_failed = []
            match to_fetch:
                case None:
                    value = getattr(self, name, _ABSENT)
                    old_value = old_information.get(name, _ABSENT)
                    if value is _ABSENT:
                        if old_value is _ABSENT:
                            fetch_failed.append(original_name)
                            logger.warning(
                                f"{type(self).__name__}.{name} does not exist, and it'll be excluded from information.json."
                            )
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
                        logger.warning(
                            f"{type(self).__name__}.{name} does not exist, and it'll be excluded from information.json."
                        )
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
                return {
                    str(key): self._normalize_information(value)
                    for key, value in mapping.items()
                }

            case list(seq):
                return [self._normalize_information(item) for item in seq]

            case Path() as path:
                return str(path)  # absolute path로 변환해야 할까?

            case other:
                logger.warning(f"Unexpected type: {type(other).__name__} of {other!r}")
                return other

    async def _download_image(self, url: str, directory: Path, name: str) -> Path:
        try:
            response = await self.client.get(url)
            image_raw: bytes = response.content
            file_extension = self._infer_filetype(response.headers.get("content-type"), image_raw)

            image_path = directory / self._safe_name(f"{name}.{file_extension}")
            image_path.write_bytes(image_raw)
            return image_path
        except Exception as exc:
            exc.add_note(f"Exception occurred when downloading image from {url!r}")
            raise

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

    def _get_snapshot_contents(self, path: Path) -> str | dict | None:
        result = self._snapshot_data.get("contents")
        if not result:
            return None
        parts = path.relative_to(self.base_directory).parts
        for part in parts[1:]:  # 웹툰 디렉토리에서 시작하기 위해 맨 첫 번째 웹툰 디렉토리 파트를 버림
            match result:
                case str():
                    return None
                case dict(result):
                    try:
                        result = result[part]
                    except KeyError:
                        return None
        return result

    def _snapshot_contents_info(self, path: Path) -> Literal["file", "directory"] | None:
        match self._get_snapshot_contents(path):
            case None:
                return None
            case dict():
                return "directory"
            case str():
                return "file"
            case other:
                raise TypeError(f"Unexpected type: {type(other).__name__}")

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

        normal_image_regex = DIRECTORY_PATTERNS[NORMAL_IMAGE]
        return len(image_urls) == len(directory_contents) and all(
            normal_image_regex.match(file) for file in directory_contents
        )

    @contextmanager
    def _context_message(self, context_name: str, **contexts):
        self.callback(context_name, finishing=False, **contexts)
        end_contexts = {}
        yield end_contexts
        self.callback(context_name, finishing=True, is_successful=True, **end_contexts)

    @staticmethod
    def _infer_filetype(content_type: str | None, image_raw: bytes | None) -> str:
        # file extension 찾기
        if content_type:
            # content-type 해더에서 추론
            content_type = content_type.lower()
            for filetype_cls in IMAGE:
                if filetype_cls.MIME == content_type:
                    file_extension = filetype_cls.EXTENSION
        else:
            # 파일 헤더에서 추론
            file_extension = filetype.guess_extension(image_raw)
            if not file_extension:
                raise ValueError("Failed to infer file extension contents.")
                # 만약 필요한 경우 가장 흔한 확장자읜 jpg로 fallback하는 아래의 코드를 사용할 것.
                # file_extension = "jpg"

        return file_extension

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

        return {
            f"{subcategory}/{key}": None
            for key in auto_keys
        } | {
            f"{subcategory}/{key}": value
            for key, value in manual_keys.items()
        }
