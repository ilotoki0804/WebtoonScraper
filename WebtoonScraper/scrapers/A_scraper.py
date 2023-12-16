"""Abstract Class of all scrapers."""

from __future__ import annotations
from dataclasses import dataclass
import functools
import re
import os
import sys
import shutil
from pathlib import Path
import time
from typing import Generic, Iterable, TypeVar
from urllib import parse
from abc import abstractmethod, ABC
from typing import ClassVar
import logging
import threading
from contextlib import suppress
from enum import Enum

from tqdm import tqdm
from resoup import CustomDefaults
from resoup.api_with_tools import DEFAULT_HEADERS
from rich.table import Table
from rich.console import Console
import pyfilename as pf

from ..directory_merger import merge_webtoon, webtoon_regexes, NORMAL_IMAGE
from ..exceptions import UseFetchEpisode
from ..miscs import EpisodeNoRange

WebtoonId = TypeVar('WebtoonId', int, str, tuple[int, int], tuple[str, int], tuple[str, str])


def reload_manager(f):
    """reload를 인자로 가지는 어떤 함수를 받아 reload가 True라면 cache가 있다면 제거하고
    다시 정보를 불러오도록 하는 decorator."""
    # __slots__가 필요하다면 Scraper에 _return_cache를 구현하면 됨!
    @functools.wraps(f)
    def wrapper(self, *args, reload: bool = False, **kwargs):
        try:
            self._return_cache
        except AttributeError:
            self._return_cache = {}

        if self._return_cache.get(f, False):
            if not reload:
                logging.info(f'{f} is already loaded, so skipping loading. '
                             'In order to reload, set parameter by reload=True.')
                return self._return_cache[f]
            logging.warning('Refreshing webtoon_information')

        try:
            return_value = f(self, *args, reload=reload, **kwargs)
        except Exception:
            logging.info('Exception is occured while function is executed. '
                         'So function is not marked as loaded.')
            raise

        self._return_cache[f] = return_value
        return return_value

    return wrapper


class ExistingEpisodeCheckMode(Enum):  # TODO
    """다운로드받을 에피소드와 이름이 같은 폴더가 존재할 때의 대처법입니다."""

    HARD_CHECK = 'hard_check'
    """해당 에피소드의 이미지 개수가 일치하지 않을 때 다시 다운로드받습니다(기본값)."""

    SKIP = "skip"
    """폴더가 이미 존재한다면 스킵합니다."""

    INTERRUPT = "interrupt"
    """폴처가 이미 존재한다면 예외를 발생시킵니다."""

    REDOWNLOAD = 'redownload'
    """항상 해당 폴더를 지우고 다시 다운로드합니다."""


class Scraper(ABC, Generic[WebtoonId]):
    """Abstract class of all scrapers.

    전반적인 로직은 모두 이 페이지에서 관리하고, 썸네일을 받아오거나 한 회차의 이미지 URL을 불러오는 등의 방식은
    각자 scraper들에 구현합니다.
    """
    # 이 변수들은 웹툰 플랫폼에 종속적이기에 클래스 상수로 분류됨.
    BASE_URL: ClassVar[str]
    IS_CONNECTION_STABLE: ClassVar[bool]
    TEST_WEBTOON_ID: ClassVar
    TEST_WEBTOON_IDS: ClassVar[tuple] = ()
    INTERVAL_BETWEEN_EPISODE_DOWNLOAD_SECONDS: ClassVar[int] = 0
    URL_REGEX: ClassVar[str]
    EXISTING_EPISODE_POLICY: ExistingEpisodeCheckMode

    def __init__(self, webtoon_id: WebtoonId) -> None:
        """시작에 필요한 여러가지를 관여합니다.
        주의: 이 함수는 반드시 subclass에서 재정의되어야 합니다.
        이 함수를 override할 때는 super().__init__(...)을 구현 "앞에" 위치하세요.
        또한 timeout, attempts, cookie, headers중에 하나라도 정의한다면 self.update_requests()를 끝에 꼭 붙여야 합니다.
        """
        self.attempts: int = 2 if self.IS_CONNECTION_STABLE else 4
        self.timeout: int = 10
        self.headers: dict[str, str] = DEFAULT_HEADERS
        self.cookie: str
        self.rich_console = Console()
        self.update_requests()

        self.webtoon_id = webtoon_id
        self.base_directory = 'webtoon'
        self.use_tqdm_while_download = True

    # MISCS

    def callback(self, situation: str, context=None):
        match situation:
            case "download_episode_end":
                print(f'A webtoon {self.title} download ended.')
            case "merge_webtoon_end":
                print('Merging webtoon ended.')
            case "merge_webtoon_start":
                print('Merging webtoon has started...')
            case the_others:
                logging.info(the_others)

    def list_episodes(self) -> None:
        self.setup()
        table = Table(show_header=True, header_style="bold blue", box=None)
        table.add_column("Episode number [dim](ID)[/dim]", width=12)
        table.add_column("Episode Title", style='bold')
        for i, (episode_id, episode_title) in enumerate(zip(self.episode_ids, self.episode_titles), 1):
            table.add_row(f'[red][bold]{i:04d}[/bold][/red] [dim]({episode_id})[/dim]', str(episode_title))
        self.rich_console.print(table)

    def update_requests(self) -> None:
        """
        timeout, attempts, cookie, headers 중 하나라도 수정했을 때 self.reqeusts에 반영하기 위해서는
        이 함수를 이용해야 합니다.
        참고: 이 함수는 자동으로 self.headers에 self.cookie를 반영시킵니다. 따라서 self.cookie를 제작한 뒤
        이 함수를 호출하면 자동으로 self.headers에 self.cookie가 반영됩니다.
        """
        names_can_be_applied = (
            "attempts",
            "raise_for_status",
            "avoid_sslerror",
            "params",
            "data",
            "cookies",
            "files",
            "auth",
            "timeout",
            "allow_redirects",
            "proxies",
            "hooks",
            "stream",
            "verify",
            "cert",
            "json",
        )

        to_apply = {
            name: getattr(self, name)
            for name in names_can_be_applied
            if hasattr(self, name)
        }
        if (headers := self.build_headers()) is not None:
            to_apply.update(headers=headers)

        self.requests = CustomDefaults(**to_apply)

    def set_progress_indication(self, description: str) -> None:
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

        print(description)

    @staticmethod
    def get_file_extension(filename_or_url: str) -> str | None:
        """Get file extionsion from filename or URL.

        Args:
            filename_or_url: 파일 확장자가 궁금한 파일명이나 URL. 이때 URL 쿼리는 무시됩니다.

        Returns:
            파일 확장자를 반환합니다.
        """
        url_path = parse.urlparse(filename_or_url).path  # 놀랍게도 일반 filename(file.jpg 등)에서도 동작함.
        extension_name = re.search(r'(?<=[.])\w+?$', url_path)
        return None if extension_name is None else extension_name.group(0)

    @staticmethod
    def get_safe_file_name(file_or_diretory_name: str) -> str:
        """Convert file or diretory name to accaptable name.

        Caution: Do NOT put a diretory path(e.g. webtoon/ep1/001.jpg) here.
        Otherwise it will smash slashes and backslashes.
        """
        return pf.to_safe_name(file_or_diretory_name)

    def check_if_legitimate_webtoon_id(
        self,
        exception_type: type[BaseException] | tuple[type[BaseException], ...] = Exception
    ) -> str | None:
        """If webtoon_id is legitimate, return title. Otherwise, return None"""
        try:
            self.fetch_webtoon_information()
            return self.title
        except exception_type:
            return None

    @property
    def base_directory(self) -> Path:
        return self._base_directory

    @base_directory.setter
    def base_directory(self, base_directory: str | Path) -> None:
        """
        웹툰을 다운로드할 디렉토리입니다. str이나 Path로 값을 받습니다.

        많은 이 변수의 사용처에서는 pathlib.Path를 필요로 합니다.
        이 property는 base_directory에 str을 넣어도 Path로 자동으로 변환해줍니다.
        이것을 이용하기 전에 안전한 파일명으로 바꾸는 것을 잊지 마세요!
        """
        self._base_directory = Path(base_directory)

    def build_headers(self) -> dict | None:
        if not hasattr(self, 'headers'):
            return None

        if hasattr(self, 'cookie'):
            return self.headers | {"Cookie": self.cookie}
        else:
            return self.headers

################################## MAIN ACTION ##################################

    def episode_no_range_to_real_range(self, episode_no_range: EpisodeNoRange) -> Iterable[int]:
        # 주의 episode_no_list는 0부터 시작합니다.
        episode_length = len(self.episode_ids)

        if not episode_no_range:
            return range(episode_length)

        if isinstance(episode_no_range, int):
            # 사용자용 숫자는 1이 더해진 상태라 1을 빼는 과정이 필요하다.
            return (episode_no_range - 1,)

        if not isinstance(episode_no_range, tuple):
            raise TypeError(f'Unknown type for episode_no_range({type(episode_no_range)}), check it again.')

        start, end = episode_no_range

        if start is None:
            start = 1
        if end is None:
            end = episode_length

        # 사용자용 숫자는 1이 더해진 상태라 1을 빼는 과정이 필요하다.
        return range(start - 1, end)

    def download_webtoon(
        self,
        episode_no_range: EpisodeNoRange = None,
        merge_amount: int | None = None
    ) -> None:
        """웹툰 다운로드의 주축이 되는 함수. 이 함수를 통해 웹툰을 다운로드합니다.

        주의: 유료 회차나 성인 웹툰은 기본적으로는 다운로드받을 수 없습니다.
        Args:
            episode_no_range: 다운로드할 회차의 범위를 정합니다.
                None일 경우(기본값): 웹툰의 모든 회차를 다운로드 받습니다.
                tuple일 경우: (처음, 끝)의 튜플로 값을 받습니다. 이때 1부터 시작하고 끝 숫자를 포함합니다.
                        두 값 중 None인 것이 있다면 처음이나 끝으로 평가됩니다.
                    예1) (1, 10): 1회차부터 10회차까지를 다운로드함
                    예2) (None, 20): 1회차부터 20회차까지를 다운로드함
                    예2) (3, None): 3회차부터 끝까지 다운로드함
                int일 경우: 한 회차만 다운로드 받습니다.
            merge_amount: 웹툰을 모두 다운로드 받은 뒤 웹툰을 묶습니다. None(기본값)이라면 웹툰을 묶지 않습니다.
        """
        self.setup()

        webtoon_directory_name = self.get_webtoon_directory_name()
        webtoon_directory = self.base_directory / webtoon_directory_name

        webtoon_directory.mkdir(parents=True, exist_ok=True)

        self.download_webtoon_thumbnail(webtoon_directory)

        episode_no_list = self.episode_no_range_to_real_range(episode_no_range)

        self.callback("download_episode_start")
        self.pbar = tqdm(episode_no_list)
        for episode_no in self.pbar:
            # if를 붙이는 게 self.INTERVAL~이 0인 경우 빨라짐.
            if self.INTERVAL_BETWEEN_EPISODE_DOWNLOAD_SECONDS:
                time.sleep(self.INTERVAL_BETWEEN_EPISODE_DOWNLOAD_SECONDS)
            self.download_episode(episode_no, webtoon_directory)
        self.callback("download_episode_end")

        webtoon_directory = self.unshuffle_lezhin_webtoon(webtoon_directory)

        if merge_amount is not None:
            self.callback("merge_webtoon_start")
            merge_webtoon(webtoon_directory, 5)
            self.callback("merge_webtoon_end")

    def get_webtoon_directory_name(self) -> str:
        """
        웹툰 디렉토리를 만드는 데에 사용되는 string을 반환합니다.
        네이버 포스트나 레진같이 일반적이지 않은 방식으로 웹툰을 다운로드하는 경우에 사용됩니다.
        """
        return f'{self.get_safe_file_name(self.title)}({self.webtoon_id})'

    def unshuffle_lezhin_webtoon(self, base_webtoon_directory: Path):
        """
        For lezhin's shuffle process.
        This function changes webtoon_directory to unshuffled webtoon's directory (if exist).
        레진을 제외하면 unshuffler가 필요한 경우가 없기 때문에 레진 외의 웹툰들은 그대로 놔두시면 됩니다.
        """
        return base_webtoon_directory

    def make_directory_or_check_if_directory_is_valid(self, episode_directory: Path, image_urls: list, subtitle: str) -> None | bool:
        """episode_directory를 생성하고 이미 있다면 해당 폴더 내 내용물이 적합한지 조사합니다.
        episode_no는 사용되지 않지만 혹시 모를 경우를 위해 남겨져 있습니다. 필요한 경우 제거하셔도 됩니다.

        None를 return한다면 회차를 다운로드해야 한다는 의미입니다.
        True를 return하면 해당 회차가 이미 완전히 다운로드되어 있으며, 따라서 다운로드를 지속할 이유가 없음을 의미합니다.
        """

        if episode_directory.is_file():
            raise FileExistsError(f"File at {episode_directory} already exists. Please delete the file.")

        if not episode_directory.is_dir():
            episode_directory.mkdir()

        self.set_progress_indication(f'checking integrity of {subtitle}')

        is_filename_appropriate = all(webtoon_regexes[NORMAL_IMAGE].match(file) for file in os.listdir(episode_directory))
        if not is_filename_appropriate or len(image_urls) != len(os.listdir(episode_directory)):
            self.set_progress_indication(f'{subtitle} is not vaild. Automatically restore files.')
            shutil.rmtree(episode_directory)
            episode_directory.mkdir()
        else:
            self.set_progress_indication(f'skipping {subtitle}')
            return True

    def download_episode(self, episode_no: int, webtoon_directory: Path) -> None:
        """한 회차를 다운로드받는다. 주의: 이 함수의 episode_no는 0부터 시작합니다."""
        safe_episode_title = self.get_safe_file_name(self.episode_titles[episode_no])

        if not safe_episode_title:
            logging.warning(f'this episode is not free or not yet created. This episode won\'t be loaded. {episode_no=}')
            self.set_progress_indication('unknown episode')
            return

        episode_images_url = self.get_episode_image_urls(episode_no)

        if episode_images_url is None:
            logging.warning(f'this episode is not free or not yet created. This episode won\'t be loaded. {episode_no=}')
            self.set_progress_indication('unknown episode')
            return

        episode_directory = webtoon_directory / f'{episode_no + 1:04d}. {safe_episode_title}'
        if self.make_directory_or_check_if_directory_is_valid(episode_directory, episode_images_url, safe_episode_title):
            return

        self.set_progress_indication(f'downloading {safe_episode_title}')

        threads = [threading.Thread(target=self.download_image, args=(episode_directory, element, i))
                   for i, element in enumerate(episode_images_url)]
        [thread.start() for thread in threads]
        [thread.join() for thread in threads]

    def download_image(self, episode_directory: Path, url: str, image_no: int, file_extension: str | None = None) -> None:
        """
        Download image from url and returns to {episode_directory}/{file_name(translated to accactable name)}.

        Args:
            file_extension: 만약 None이라면(기본값) 파일 확장자를 자동으로 알아내고, 아니라면 해당 값을 파일 확장자로 사용합니다.
        """
        if file_extension is None:
            image_extension = self.get_file_extension(url)
            if image_extension is None:
                raise ValueError('File extension not detected. Use default_file_extension or check your code.')
        else:
            image_extension = file_extension

        file_name = f'{image_no:03d}.{image_extension}'

        image_raw: bytes = self.requests.get(url).content

        file_directory = episode_directory / file_name
        file_directory.write_bytes(image_raw)

    def download_webtoon_thumbnail(self, webtoon_directory: Path, file_extension: str | None = None) -> None:
        """
        웹툰의 썸네일을 불러오고 thumbnail_directory에 저장합니다.
        Args:
            webtoon_directory (Path): 썸네일을 저장할 디렉토리입니다.
            file_extionsion (str | None): 파일 확장자입니다. 만약 None이라면(기본값) 자동으로 값을 확인합니다.
        """
        self.callback("download_thubnail_start")
        thumbnail_data: str | tuple[bytes, str] = self.webtoon_thumbnail
        if isinstance(thumbnail_data, str):  # It means thumnail_data is URL
            if file_extension:
                image_extension = file_extension
            else:
                image_extension = self.get_file_extension(thumbnail_data)
                if image_extension is None:
                    raise ValueError(f'File extension not detected. thumbnail_data: {thumbnail_data}')

            image_raw = self.requests.get(thumbnail_data).content
        elif isinstance(thumbnail_data, tuple):  # It means thumnail_data is raw image data
            image_raw, image_extension = thumbnail_data
        else:
            raise TypeError('Type of thumbnail_data(or self.webtoon_thumbnail) is invalid; It must be string or bytes.')

        image_path = webtoon_directory / f'{self.get_safe_file_name(self.title)}.{image_extension}'
        image_path.write_bytes(image_raw)
        self.callback("download_thubnail_end")

    @abstractmethod
    def get_episode_image_urls(self, episode_no: int) -> list[str] | None:
        """해당 회차를 구성하는 이미지들을 불러옵니다."""

    def setup(self, reload: bool = False) -> None:
        """웹툰에 관련한 정보를 불러옵니다."""
        self.callback("setup_start")
        with suppress(UseFetchEpisode):
            self.fetch_webtoon_information(reload=reload)
        with suppress(UseFetchEpisode):  # 현재는 필요 없지만 혹시 모를 변화를 위해 남김.
            self.fetch_episode_informations(reload=reload)
        self.callback("setup_end")

    @reload_manager
    @abstractmethod
    def fetch_webtoon_information(self, *, reload: bool = False) -> None:
        """
        웹툰 정보를 불러옵니다. 각각의 에피소드에 대한 정보는 포함되지 않습니다.
        """
        self.webtoon_thumbnail: str | tuple[bytes, str]
        self.title: str

    @reload_manager
    @abstractmethod
    def fetch_episode_informations(self, *, reload: bool = False) -> None:
        """
        웹툰의 에피소드 정보를 불러옵니다. 웹툰에 대한 정보는 포함하지 않습니다.
        """
        self.episode_titles: list[str]
        self.episode_ids: list[int]
