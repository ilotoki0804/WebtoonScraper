"""Abstract Class of all scrapers."""

from __future__ import annotations

import asyncio
import html
import json
import os
import re
import shutil
import time
from abc import abstractmethod
from collections.abc import Mapping
from contextlib import contextmanager, suppress
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    Generic,
    Literal,
    TypeVar,
)
from collections.abc import Container
from collections.abc import Callable, Sequence
from urllib import parse

import hxsoup
import pyfilename as pf
from yarl import URL
from tqdm import tqdm

from ..base import logger, platforms
from ..exceptions import (
    InvalidURLError,
    UseFetchEpisode,
)
from ..directory_state import (
    DIRECTORY_PATTERNS,
    NORMAL_IMAGE,
)
from ._helpers import EpisodeRange, ExtraInfoScraper, reload_manager
from ._helpers import shorten as _shorten

if TYPE_CHECKING:
    from typing import Self

WebtoonId = TypeVar("WebtoonId")


class RegisterMeta(type):
    def __init__(cls, *_, **__):
        if platform_name := getattr(cls, "PLATFORM", None):
            if already_registered := platforms.get(platform_name):
                # 시작하기 전의 메시지기 때문에 `-v` 플래그로 확인하기 어려움
                logger.debug(f"Overriding {already_registered} with Scraper {cls}.")
            else:
                logger.debug(f"Scraper {cls} has been registered as {platform_name}.")
            platforms[platform_name] = cls


class Scraper(Generic[WebtoonId], metaclass=RegisterMeta):  # MARK: SCRAPER
    """Abstract base class of all scrapers.

    전반적인 로직은 모두 이 페이지에서 관리하고, 썸네일을 받아오거나 한 회차의 이미지 URL을 불러오는 등의 방식은
    각자의 scraper들에서 구현합니다.
    """

    # 이 변수들은 웹툰 플랫폼에 종속적이기에 클래스 상수로 분류됨.
    PLATFORM: ClassVar[str]
    DOWNLOAD_INTERVAL: ClassVar[int | float] = 0
    INFORMATION_VARS: ClassVar[dict[str, None | str | Callable[[Any, str], Any]]] = dict(
        title=None,
        platform="PLATFORM",
        webtoon_thumbnail_url=None,
        episode_ids=None,
        episode_titles=None,
        author=None,
        download_status="download_status",
    )
    DEFAULT_IMAGE_FILE_EXTENSION: str | None = None
    extra_info_scraper: ExtraInfoScraper | None = None

    def __init__(self, webtoon_id: WebtoonId, /) -> None:
        self.hxoptions = hxsoup.MutableClientOptions(
            attempts=3,
            timeout=10,
            headers=dict(hxsoup.DEV_HEADERS),
            follow_redirects=True,
        )

        self.extra_info_scraper = self.extra_info_scraper or ExtraInfoScraper()
        self.webtoon_id = webtoon_id
        self.base_directory: Path | str = Path.cwd()
        self.use_progress_bar = True
        self.does_store_information = True
        self.existing_episode_policy: Literal["skip", "raise", "download_again", "hard_check"] = "skip"
        self.author = None
        self._stop_progress = False
        self.ignore_snapshot: bool = False
        self.save_extra_information: bool = False

    # MARK: PUBLIC METHODS

    @abstractmethod
    def get_episode_image_urls(self, episode_no: int) -> list[str] | None:
        """해당 회차를 구성하는 이미지들의 URL을 불러옵니다."""
        raise NotImplementedError

    def get_episode_extra(self, episode_no: int) -> None:
        """해당 회차를 구성하는 이미지들의 URL을 불러옵니다."""

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
    @abstractmethod
    def _extract_webtoon_id(cls, url: URL) -> WebtoonId | None:
        raise NotImplementedError

    @classmethod
    def from_url(
        cls,
        url: str,
        *args,  # cookie나 bearer같은 optional parameter를 잡기 위해 필요.
        **kwargs,
    ) -> Self:
        """Raw URL에서 자동으로 웹툰 ID를 추출합니다."""
        try:
            webtoon_id: WebtoonId | None = cls._extract_webtoon_id(URL(url))
        except Exception as e:
            raise InvalidURLError.from_url(url, cls) from e

        if webtoon_id is None:
            raise InvalidURLError.from_url(url, cls)

        return cls(webtoon_id, *args, **kwargs)

    def get_webtoon_directory_name(self) -> str:
        """웹툰 디렉토리를 만드는 데에 사용되는 string을 반환합니다."""
        return self._safe_name(f"{self.title}({self.webtoon_id})")

    def fetch_all(self, reload: bool = False) -> None:
        """웹툰 다운로드에 필요한 모든 필수적인 정보를 불러옵니다."""
        with suppress(UseFetchEpisode):
            self.fetch_webtoon_information(reload=reload)
        self.fetch_episode_information(reload=reload)

    def download_webtoon(self, download_range: EpisodeRange | Container[WebtoonId] | None = None) -> None:
        """웹툰을 다운로드합니다.

        Jupyter 등 async 환경에서는 제대로 동작하지 않을 수 있습니다. 그럴 경우 async_download_webtoon을 사용하세요.

        기본적으로는 별다른 인자를 필요로 하지 않으며 다운로드받을 범위와 웹툰 모아서 보기를 할 때는
        추가적인 파라미터를 이용할 수 있습니다.

        Args:
            download_range: 다운로드할 회차의 범위를 정합니다.
        """
        try:
            asyncio.run(self.async_download_webtoon(download_range=download_range))
        except RuntimeError as e:
            try:
                e.add_note("Use `scraper.async_download_webtoon` in Jupyter or asyncio environment.")
            except AttributeError:
                logger.error("Use `scraper.async_download_webtoon` in Jupyter or asyncio environment.")
            raise

    async def async_download_webtoon(self, download_range: EpisodeRange | Container[WebtoonId] | None = None) -> None:
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
            self.fetch_all()

        webtoon_directory = self._prepare_directory()

        assert self.extra_info_scraper is not None
        self.extra_info_scraper.initializer(self, webtoon_directory)

        with self._context_message("download_thumbnail"):
            thumbnail_name = self._download_webtoon_thumbnail(webtoon_directory)

        # 여기에서 1-based에서 0-based로 바뀜.
        if download_range is None:
            episode_no_list = range(len(self.episode_ids))
        else:
            episode_no_list = tuple(i for i in range(len(self.episode_ids)) if i + 1 in download_range)

        try:
            with self._context_message("download_episode"):
                await self._download_episodes(episode_no_list, webtoon_directory)

            webtoon_directory = self._post_process_directory(webtoon_directory)

        except BaseException as exc:
            logger.error("Aborting..." if isinstance(exc, KeyboardInterrupt) else "Finalizing...")
            self.extra_info_scraper.finalizer(self, locals(), exc=exc)
            raise

        else:
            self.extra_info_scraper.finalizer(self, locals(), exc=None)

    def callback(self, situation: str, **context) -> None:
        """웹툰 다운로드의 중요한 순간들을 알림받습니다.

        주의: callback은 다운로드 과정을 멈추고 작업합니다.
        최대한 빨리 끝날 수 있도록 하는 것이 속도에 좋습니다.
        """
        match situation, context:
            case "setup", {"finishing": False}:
                logger.info("Fetching metadata...")
            case "download_thumbnail", {"finishing": True}:
                logger.info(f"Downloading {_shorten(self.title)}...")
            case "download_episode", {"finishing": True}:
                logger.info(f"The webtoon {self.title} download ended.")
            case ("indicate" | "download_skipped" | "download_failed" | "downloading_image"), context:
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

                if not self._progress_indication(description):
                    if episode_no is not None:
                        description = f"[{episode_no:02d}/{len(self.episode_titles):02d}] {description}"
                    logger.info(description)
            case "description", _:
                logger.info(context["description"])
            case "episode_download_complete", _:
                is_download_successful = context["is_download_successful"]
                if is_download_successful:
                    episode_no = context["episode_no"]
                    episode_title = self.episode_titles[episode_no]
                    logger.info(f"Downloaded: #{episode_no} {_shorten(episode_title)}")
            case "episode_download_stopped", _:
                logger.error("WebtoonScraper stopped.")
            case the_others, context if context:
                logger.debug(f"WebtoonScraper status: {the_others}, context: {context}")
            case the_others, _:
                logger.debug(f"WebtoonScraper status: {the_others}")

    # MARK: PROPERTIES

    @property
    def cookie(self) -> str | None:
        try:
            return self.headers["Cookie"]
        except KeyError:
            return None

    @cookie.setter
    def cookie(self, value: str) -> None:
        self.headers.update(Cookie=value)

    @property
    def headers(self) -> dict[str, str]:
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

    def _prepare_directory(self) -> Path:
        webtoon_directory_name = self.get_webtoon_directory_name()
        webtoon_directory = Path(self.base_directory, webtoon_directory_name)
        webtoon_directory.mkdir(parents=True, exist_ok=True)
        return webtoon_directory

    def _load_snapshot(self, webtoon_directory: Path) -> None:
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
        # logger.info(f"{path}, '{path.relative_to(self.base_directory)}', {type(self._get_snapshot_contents(path))}")
        match self._get_snapshot_contents(path):
            case None:
                return None
            case dict():
                return "directory"
            case str():
                return "file"
            case other:
                raise TypeError(f"Unexpected type: {type(other).__name__}")

    def _stop(self):
        self._stop_progress = True

    @classmethod
    def _from_string(cls, string: str, /, **kwargs):
        """webtoon_id가 int가 아니라면 반드시 구현해야 합니다."""
        return cls(int(string), **kwargs)  # type: ignore

    def _apply_options(self, options: dict[str, str], /) -> None:
        if options:
            for option, raw_value in options.items():
                logger.warning(
                    f"Unknown option for {type(self).__name__}; {type(self).__name__} does not accept any option"
                    f": {option!r}. value: {raw_value!r}"
                )

    def _get_information(self, old_information: dict):
        """`information.json`에 탑재할 정보를 추가합니다.

        이 함수를 override하면 기본적으로 포함되어 있는 정보 외에 다양한 플랫폼에 한정적인 정보를 추가할 수 있습니다.
        None일 경우에는 1) dict일 경우 update가 사용됩니다. 2) 정보가 존재하지 않을 경우 오류가 나지 않고 스킵됩니다.
        """
        _ABSENT = object()
        information = {}
        for name, value in self.INFORMATION_VARS.items():
            field, sep, remains = name.partition(".")
            if sep:
                if field == "extra" and not self.save_extra_information:
                    continue
                name = remains
                information[field] = information.get(field, {})
                to_store = information[field]
            else:
                to_store = information

            if value is None:
                value = getattr(self, name, _ABSENT)
                old_value = old_information.get(name, _ABSENT)
                if value is _ABSENT:
                    if old_value is not _ABSENT:
                        continue
                    raise ValueError(f"{self}.{name} does not exist.")
                if isinstance(value, Mapping):
                    value = {str(k) if isinstance(k, int) else k: v for k, v in value.items()}
                    if old_value is not _ABSENT:
                        # old_value가 value에 덮어씌어져야 하니 `.update()`나 `|=`를 사용하면 안 됨!
                        value = old_value | value
                to_store[name] = value
            elif isinstance(value, str):
                to_store[name] = getattr(self, value)
            elif callable(value):
                to_store[name] = value(self, name)
            else:
                raise ValueError(f"Unexpected information value: {value!r}")
        return information

    @contextmanager
    def _context_message(self, context_name: str, **contexts):
        self.callback(context_name, finishing=False, **contexts)
        end_contexts = {}
        yield end_contexts
        self.callback(context_name, finishing=True, is_successful=True, **end_contexts)

    async def _download_episodes(self, episode_no_list: Sequence[int], webtoon_directory: Path) -> None:
        """에피소드를 반복적으로 다운로드합니다.

        Args:
            episode_no_list: episode_no가 들어 있는 iterable입니다.
                iterable이므로 list 등으로 변환하는 과정이 필요할 수도 있습니다.
            webtoon_directory: 웹툰 디렉토리입니다.
        """
        self._load_snapshot(webtoon_directory)

        # "skipped_by_range", "stopped"
        self.download_status: dict[int, Literal["failed", "downloaded", "already_exist", "skipped_by_snapshot"]] = {}
        if self.use_progress_bar:
            # episode_range는 specific하다고 self에 포함하지 않으면서 pbar는 self에 붙이는 건 어불성설 아닌가?
            # self.pbar를 생성하는 것보다 closure를 제공하는 등의 방식이 더 나을 것이라 생각함.
            episodes = self.pbar = tqdm(episode_no_list)
        else:
            episodes = episode_no_list
        async with self.hxoptions.build_async_client() as client:
            for i, episode_no in enumerate(episodes):
                if self._stop_progress:
                    self.callback(
                        "episode_download_stopped",
                        index=i,
                        episode_no=episode_no,
                        episodes=episodes,
                    )
                    break
                is_download_successful = await self._download_episode(episode_no, webtoon_directory, client)
                if not self.use_progress_bar:
                    self.callback(
                        "episode_download_complete",
                        index=i,
                        episode_no=episode_no,
                        episodes=episodes,
                        is_download_successful=is_download_successful,
                    )
                self.get_episode_extra(episode_no)

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

    async def _download_episode(self, episode_no: int, webtoon_directory: Path, client: hxsoup.AsyncClient) -> bool:
        """한 회차를 다운로드받습니다.

        이 함수는 일반적으로 사용됩니다. 각 스크래퍼의 구현이 궁금하다면 get_episode_image_urls을 대신 참고하세요.
        주의: 이 함수의 episode_no는 0부터 시작합니다.
        """
        episode_title = self.episode_titles[episode_no]
        directory_name = self._safe_name(f"{episode_no + 1:04d}. {episode_title}")
        episode_directory = webtoon_directory / directory_name

        episode_at_snapshot = self._snapshot_contents_info(episode_directory)

        if (exist_in_file := episode_directory.is_file()) or (exist_in_snapshot := episode_at_snapshot == "file"):
            if self.existing_episode_policy == "skip":
                self.download_status[episode_no] = "already_exist" if exist_in_file else "skipped_by_snapshot"
                self.callback("download_skipped", episode_no=episode_no, is_file=exist_in_file, is_snapshot=exist_in_snapshot)
                return True
            raise FileExistsError(f"File at {episode_directory} already exists. Please delete the file.")

        try:
            exist_in_file = episode_directory.is_dir()
            if exist_in_file or (exist_in_snapshot := episode_at_snapshot == "directory"):
                match self.existing_episode_policy:
                    case "skip":
                        self.download_status[episode_no] = "already_exist" if exist_in_file else "skipped_by_snapshot"
                        self.callback("download_skipped", episode_no=episode_no, is_file=exist_in_file, is_snapshot=exist_in_snapshot)
                        return True
                    case "raise":
                        raise FileExistsError(
                            f"Directory at {episode_directory} already exists. Please delete the directory."
                        )
                    case "download_again":
                        check_integrity = False
                    case "hard_check":
                        check_integrity = True
                if not exist_in_file:
                    episode_directory.mkdir()
            else:
                episode_directory.mkdir()
                check_integrity = False

            time.sleep(self.DOWNLOAD_INTERVAL)  # 실제로 요청을 보내기 직전에 interval을 넣음.
            episode_images_url = self.get_episode_image_urls(episode_no)

            if not episode_images_url:
                self.download_status[episode_no] = "failed"
                self.callback("download_failed", episode_no=episode_no, warning=True)
                if not os.listdir(episode_directory):
                    episode_directory.rmdir()
                return False

            if check_integrity:
                if self._does_directory_intact(episode_directory, episode_images_url):
                    self.download_status[episode_no] = "already_exist"
                    self.callback("download_skipped", episode_no=episode_no, intact=True)
                    if not exist_in_file:
                        episode_directory.rmdir()
                    return True

                shutil.rmtree(episode_directory)
                episode_directory.mkdir()

            self.callback("downloading_image", episode_no=episode_no)
        except BaseException:
            self.callback("cancelling", episode_no=episode_no)
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
            self.callback("cancelling", episode_no=episode_no)
            shutil.rmtree(episode_directory)
            raise

        self.download_status[episode_no] = "downloaded"
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
        response = await client.get(url)
        image_raw: bytes = response.content

        if not file_extension:
            # content-type 헤더가 해석되기를 기대함
            content_type: str = response.headers.get("content-type")
            category, _, extension = content_type.partition("/")
            if category == "image":
                file_extension = extension.lower()
            else:
                file_extension = self._get_file_extension(url)
        file_name = f"{image_no:03d}.{file_extension}"

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

    # @staticmethod
    # def _get_image_file

    @staticmethod
    def _safe_name(name: str) -> str:
        """일반 문자열을 파일명으로 사용 가능한 문자열로 변경합니다.

        Caution: Do NOT put a directory path(e.g. webtoon/ep1/001.jpg) here.
        Otherwise this function will smash slashes and backslashes.
        """
        return pf.convert(html.unescape(name))

    def _progress_indication(self, message: str) -> bool:
        if not self.use_progress_bar:
            return False
        try:
            self.pbar.set_description(message)
        except AttributeError:
            return False
        else:
            return True
