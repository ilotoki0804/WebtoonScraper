"""Abstract Class of all scrapers."""

from __future__ import annotations
import functools
import re
import os
import sys
import shutil
import html
from pathlib import Path
import time
from typing import Generic, Iterable, TypeAlias, TypeVar
from urllib import parse
from abc import abstractmethod, ABC
from typing import overload, ClassVar
import logging
import threading

# from requests.exceptions import ConnectionError
# from bs4 import BeautifulSoup
# from bs4.element import Tag
from tqdm import tqdm
from requests_utils.custom_defaults import CustomDefaults
from rich.table import Table
from rich.console import Console

if sys.version_info < (3, 10):
    logging.warning(f'Version ({sys.version}) is too low. Check your version.')

if __name__ in ("__main__", "A_scraper"):
    logging.warning(f'파일이 아닌 WebtoonScraper 모듈에서 실행되고 있습니다. {__name__ = }')
    from WebtoonScraper.directory_merger import merge_webtoon, webtoon_regexes, NORMAL_IMAGE
else:
    from ..directory_merger import merge_webtoon, webtoon_regexes, NORMAL_IMAGE

EpisodeNoRange: TypeAlias = 'tuple[int | None, int | None] | int | None'
WebtoonId = TypeVar('WebtoonId', int, tuple[int, int], str)


def force_reload_if_reload(f):
    # @functools.wraps(f)
    def wrapper(self, *args, reload: bool = False, **kwargs):
        # print(self, args, reload, kwargs)
        if not hasattr(self, '_already_loaded'):
            self._already_loaded = {}

        if self._already_loaded.get(f, False) and reload:
            logging.warning('Refreshing webtoon_information')

        if not self._already_loaded.get(f, False) or reload:
                return_value = f(self, *args, **kwargs)
            except Exception:
                logging.debug('Exception is occured while function is executed. '
                              'So function is not marked as loaded.')
                raise
            self._already_loaded[f] = True
            return return_value

        logging.debug(f'{f} is already loaded, so skipping loading. reload=True to re-enable.')

    return wrapper


class Scraper(ABC, Generic[WebtoonId]):
    """Abstract class of all scrapers.

    init, get_internet, 전반적인 로직 등은 모두 이 페이지에서 관리하고, 구체적인 다운로드 방법은 각각의 scraper들에게 맡깁니다.
    따라서 썸네일을 받아오거나 한 회차의 이미지 URL을 불러오는 등의 역할은 각자 scraper들에 구현되어 있습니다.
    """
    # 이 변수들은 웹툰 플랫폼에 종속적이기에 클래스 상수로 분류됨.
    BASE_URL: ClassVar[str]
    IS_CONNECTION_STABLE: ClassVar[bool]
    TEST_WEBTOON_ID: ClassVar
    INTERVAL_BETWEEN_EPISODE_DOWNLOAD_SECONDS: ClassVar[int] = 0

    def __init__(self, webtoon_id: WebtoonId) -> None:
        """시작에 필요한 여러가지를 관여합니다.
        주의: 이 함수는 반드시 subclass에서 재정의되어야 합니다.
        이 함수를 override할 때는 super().__init__(...)을 구현 "앞에" 위치하세요.
        하지만 timeout, attempts, cookie, headers중에 하나라도 정의한다면 self.update_requests()를 끝에 꼭 붙여야 합니다.

        Args:
            webtoon_id: 일반적으로 URL에 나타나는 웹툰의 ID입니다.
            pbar_independent: 만약 True라면 tqdm을 이용해서 로그를 표시하고, False라면 print를 통해서 로그를 표시합니다.
        """
        # 연결 관련 설정
        self.attempts: int = 2 if self.IS_CONNECTION_STABLE else 4
        self.timeout: int = 10
        self.headers: dict[str, str] = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                          '(KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36'
        }
        self.cookie: str
        self.rich_console = Console()

        self.webtoon_id = webtoon_id

        self.base_directory = 'webtoon'
        self.not_using_tqdm = False
        self.update_requests()

        # self.existing_episode_checking_mode: Literal[
        #     'interrupt_during_download', 'assume_legimate',
        #     'hard_check', 'dont_envolve_requests'
        # ] = 'interrupt_during_download'

    # MISCS

    def list_episodes(self) -> None:
        self.setup()
        table = Table(show_header=True, header_style="bold blue", box=None)
        table.add_column("Episode number (ID)", width=12)
        table.add_column("Episode Title", style='bold')
        for i, (episode_id, episode_title) in enumerate(zip(self.episode_ids, self.episode_titles), 1):
            table.add_row(f'{i:04d} [dim]({episode_id})[/dim]', str(episode_title))
        self.rich_console.print(table)

    def update_requests(self, **kwargs) -> None:
        """
        timeout, attempts, cookie, headers 중 하나라도 수정했을 때 self.reqeusts에 반영하기 위해서는
        이 함수를 이용해야 합니다.
        참고: 이 함수는 자동으로 self.headers에 self.cookie를 반영시킵니다. 따라서 self.cookie를 제작한 뒤
        이 함수를 호출하면 자동으로 self.headers에 self.cookie가 반영됩니다.
        """
        if 'timeout' in kwargs:
            self.timeout = kwargs['timeout']
        elif hasattr(self, 'timeout'):
            kwargs.update(timeout=self.timeout)

        if 'attempts' in kwargs:
            self.attempts = kwargs['attempts']
        elif hasattr(self, 'attempts'):
            kwargs.update(attempts=self.attempts)

        if 'cookie' in kwargs:
            self.cookie = kwargs['cookie']
        elif hasattr(self, 'cookie'):
            kwargs.update(cookie=self.cookie)

        if 'headers' in kwargs:
            if 'cookie' in kwargs:
                self.headers = kwargs['headers'] | {'Cookie': self.cookie}
                del kwargs['cookie']
            else:
                self.headers = kwargs['headers']
        elif hasattr(self, 'headers'):
            if 'cookie' in kwargs:
                self.headers |= {'Cookie': self.cookie}
                del kwargs['cookie']

            kwargs.update(headers=self.headers)

        self.requests = CustomDefaults(**kwargs)

    def set_to_instant_connection(self, revert_changes: bool = False) -> None:
        """
        이 함수를 실행하면 self.timeout이 3이 되고, self.attempts가 5가 됩니다.
        이렇게 되면 연결이 자주 실패하고 재시도하는데, 이렇게 하면 경우에 따라서는 더욱 빠르게 다운로드받을 수 있습니다.
        만약 revert_changes를 True로 하고 실행하면 기존에 있던 값을 다시 불러옵니다.
        예를 들어 기존에 self.timeout이 20이고 self.attempts가 2였다면,
        .set_to_instant_connection()을 실행하는 self.timeout과 self.attempts가 각각 3과 5가 되고,
        .set_to_instant_connection(True)를 실행하면 다시 각각 20과 2가 됩니다.

        Args:
            short_connection(bool):
                만약 True라면 timeout를 3초로 짧게 잡고 IS_STABLE_CONNECTION(거짓일 경우, 연결에 실패하면 재시도를 함.)을 False로 합니다.
                False라면 기본 설정을 유지하고 timeout도 길게(120초) 유지합니다.
        """
        if revert_changes:
            if not self._short_connection_previous_values:
                raise ValueError('Nothing to revert.')

            self.timeout = self._short_connection_previous_values['timeout']
            self.attempts = self._short_connection_previous_values['attempts']
            return

        if self.timeout != 3 or self.attempts != 5:
            self._short_connection_previous_values = {
                'timeout': self.timeout,
                'attempts': self.attempts
            }

        self.timeout = 3
        self.attempts = 5

        self.update_requests()

    def set_progress_indication(self, description: str) -> None:
        """진행사항을 표시할 곳을 tqdm의 description과 print 중 어떤 것을 사용할지 결정합니다.

        self.not_using_tqdm가 True라면 print를 사용하고, False라면 pbar를 이용합니다.
        이는 self.not_using_tqdm 설정을 변경해 사용할 수 있습니다. 기본값은 False입니다.
        만약 사용자에게 꼭 알려야 하는 중요한 것이 있다면 이 함수가 아닌 직접 print나 logging을 사용하는 것을 권장합니다.

        Args:
            description: 표시할 진행사항.

        Raises:
            AttributeError:
                download_one_webtoon으로 시작하지 않은 함수에서 이 함수를 호출한다면 생기는 오류입니다.
                예를 들어, 만약 download_one_episode 함수를 단독으로 실행했다면, self.pbar가 선언되지 않았기 때문에 오류가 발생합니다.
                오류를 해결하려면 self.not_using_tqdm를 True로 하거나 download_webtoon을 사용하세요.
        """
        if self.not_using_tqdm:
            print(description)
        else:
            self.pbar.set_description(description)

    @staticmethod
    def get_file_extension(filename_or_url: str) -> str | None:
        """Get file extionsion of filename_or_url.

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
        """Translate file or diretory name to accaptable name.

        Caution: Do NOT put here diretory path(e.g. webtoon/ep1/001.jpg),
        beacause it will translate slash and backslash to acceptable(and cannot be used for going directory) name.
        """
        # sourcery skip: remove-zero-from-range
        table = str.maketrans('\\/:*?"<>|\t\n', '⧵／：＊？＂＜＞∣   ')  # pylint: disable=invalid-character-backspace
        table.update(
            {i: 32 for i in range(0, 31)}
        )

        processed = html.unescape(file_or_diretory_name)  # change things like "&amp;" to "'".

        processed = processed.translate(table).strip()

        processed = re.sub(r'\.$', '．', processed)

        return processed

    def check_if_legitimate_webtoon_id(self) -> str | None:
        """If webtoon_id is legitimate, return title. Otherwise, return None"""
        try:
            self.fetch_webtoon_information()
            return self.title
        except Exception:
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

        self.pbar = tqdm(episode_no_list)
        for episode_no in self.pbar:
            # if를 붙이는 게 self.INTERVAL~이 0인 경우 빨라짐.
            if self.INTERVAL_BETWEEN_EPISODE_DOWNLOAD_SECONDS:
                time.sleep(self.INTERVAL_BETWEEN_EPISODE_DOWNLOAD_SECONDS)
            self.download_episode(episode_no, webtoon_directory)
        print(f'A webtoon {self.title} download ended.')

        webtoon_directory = self.unshuffle_lezhin_webtoon(webtoon_directory)

        if merge_amount is not None:
            print('Merging webtoon has started...')
            merge_webtoon(webtoon_directory, 5)
            print('Merging webtoon ended.')

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

    def make_directory_or_check_if_directory_is_valid(self, episode_directory: Path, episode_no: int, image_urls: list, subtitle: str) -> None | bool:
        """episode_directory를 생성하고 이미 있다면 해당 폴더 내 내용물이 적합한지 조사합니다.
        episode_no는 사용되지 않지만 혹시 모를 경우를 위해 남겨져 있습니다. 필요한 경우 제거하셔도 됩니다.

        None를 return한다면 회차를 다운로드해야 한다는 의미입니다.
        True를 return하면 해당 회차가 이미 완전히 다운로드되어 있으며, 따라서 다운로드를 지속할 이유가 없음을 의미합니다.
        """

        if episode_directory.is_file():
            # sourcery skip
            shutil.move(episode_directory, episode_directory.parent
                        / ('(replaced)' + episode_directory.name))
            episode_directory.mkdir()

        if not episode_directory.is_dir():
            episode_directory.mkdir()

        self.set_progress_indication(f'checking integrity of {subtitle}')

        # WIP
        # modes: 'interrupt_during_download', 'assume_legimate', 'hard_check', 'dont_envolve_requests'
        # 'dont_envolve_requests' is processed in higher function.

        # if self.existing_episode_checking_mode == 'assume_legimate':
        #     return True

        # if self.existing_episode_checking_mode == 'dont_envolve_requests':
        #     return len(os.listdir(episode_dir)) == len(image_urls)

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
        if self.make_directory_or_check_if_directory_is_valid(episode_directory, episode_no, episode_images_url, safe_episode_title):
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

    @abstractmethod
    def get_episode_image_urls(self, episode_no: int) -> list[str] | None:
        """해당 회차를 구성하는 이미지들을 불러옵니다."""

    def setup(self, reload: bool = False) -> None:
        """웹툰에 관련한 정보를 불러옵니다."""
        with suppress(UseFetchEpisode):
            self.fetch_webtoon_information(reload=reload)  # 데코레이터 트릭을 이용함.  # type: ignore
        with suppress(UseFetchEpisode):  # 현재는 필요 없지만 미래의 변화를 위해 남겨둠.
            self.fetch_episode_informations(reload=reload)  # 데코레이터 트릭을 이용함.  # type: ignore

    @force_reload_if_reload
    @abstractmethod
    def fetch_webtoon_information(self) -> None:
        """
        웹툰 정보를 불러옵니다. 각각의 에피소드에 대한 정보는 포함되지 않습니다.

        주의: subclass에서의 구현은 super().fetch_webtoon_information()를 프로그램 맨 앞에 포함하세요.
        또한 프로그램이 끝나고 self.is_webtoon_information_loaded = True를 실행해야 한다는 것을 잊지 마세요.
        """
        self.webtoon_thumbnail: str | tuple[bytes, str]
        self.title: str

    @force_reload_if_reload
    @abstractmethod
    def fetch_episode_informations(self) -> None:
        """
        웹툰의 에피소드 정보를 불러옵니다. 웹툰에 대한 정보는 포함하지 않습니다.

        주의: subclass에서의 구현은 super().fetch_episode_informations()를 프로그램 맨 앞에 포함하세요.
        또한 프로그램이 끝나고 self.is_episode_informations_loaded = True를 실행해야 한다는 것을 잊지 마세요.
        """
        self.episode_titles: list[str]
        self.episode_ids: list[int]