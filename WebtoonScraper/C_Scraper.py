"""Abstract Class of all scrapers."""
# [x]: file_acceptable built-in으로 만들기
# [x]: titleid tuple도 허용해서 NPScraper에서 이용할 수 있도록 하기
# [x]: get_data 시 list로 정보 받아오기
# TODO: None 대신 NoReturn 사용하기
# TODO: download vs save : 용어 정리하기
# TODO: 카카오 웹툰/카카오 페이지 웹툰, 네이버 블로그 만들기
# TODO: short_connection 등 docs 추가하기
# TODO: Webtoon get_webtoon_platform 조금 더 잘 만들 방법 강구하기
# TODO: annotations 추가하고 필요 version낮추기
# TODO: print문 모두 제거하고 logging으로 변경하기
# TODO: get_webtoon_data에서 dataclass같은 걸 이용해서 self.webtoon_data.titleid같을 걸로 이용할 수 있도록 함.
# TODO: 레진코믹스 pyjsparser 대신 정적 분석 시도하기
import re
import os
import asyncio
import shutil
import html
from pathlib import Path
# from typing import Iterable, Literal
from typing import Literal, NoReturn
from abc import abstractmethod, ABCMeta
# from collections import namedtuple
# from contextlib import suppress
from typing import overload
# import logging

import requests
from requests.exceptions import ConnectionError
from bs4 import BeautifulSoup as bs
from bs4.element import Tag
from tqdm import tqdm
from async_lru import alru_cache

if __name__ in ("__main__", "C_Scraper"):
    from A_FolderManager import FolderManager
else:
    from .A_FolderManager import FolderManager

TitleId = int | tuple[int, int] | str


class Scraper(metaclass=ABCMeta):
    """Abstract class of all scrapers.

    init, get_internet, 전반적인 로직 등은 모두 이 페이지에서 관리하고, 구체적인 다운로드 방법은 각각의 scraper들에게 맡깁니다.
    따라서 썸네일을 받아오거나 한 회차의 이미지 URL을 불러오는 등의 역할은 각자 scraper들에 구현되어 있습니다.
    """

    def __init__(self, pbar_independent: bool = False) -> None:
        """시작에 필요한 여러가지를 관여합니다.

        header, timeout을 구성하고 set_folders()를 호출합니다.

        Args:
            pbar_independent: 만약 True라면 tqdm을 이용해서 로그를 표시하고, False라면 print를 통해서 로그를 표시합니다.
        """
        # BASE_URL and IS_STABLE_CONNECTION have to be defined!
        self.HEADERS = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
            '(KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36'
        }
        self.BASE_DIR = 'webtoon'
        self.TIMEOUT = 120
        self.PBAR_INDEPENDENT = pbar_independent
        self.IS_STABLE_CONNECTION = None  # IS_STABLE_CONNECTION must be defined!
        self.short_connection = False

    @property
    def short_connection(self) -> bool:
        return self._short_connection

    @short_connection.setter
    def short_connection(self, short_connection: bool):
        """
        이 함수는 short_connection을 설정합니다.
        short_connection에는 특징이 있는데, True로 바꾸는 순간 그 전에 설정한 IS_STABLE_CONNECTION과
        TIMEOUT이 날아가고 각각 False와 3으로 변합니다. 이 함수는 short_connection을 False로 바꿀 때
        기존의 설정으로 돌아갈 수 있도록 돕습니다.

        Args:
            short_connection(bool):
                만약 True라면 timeout를 3초로 짧게 잡고 IS_STABLE_CONNECTION(거짓일 경우, 연결에 실패하면 재시도를 함.)을 False로 합니다.
                False라면 기본 설정을 유지하고 timeout도 길게(120초) 유지합니다.

        Exceptions:
            AttributeError: short_connection 값을 선언하기 이전에 반드시 self.IS_STABLE_CONNECTION과
                self.TIMEOUT을 선언해야 합니다. 만약 그렇지 않으면 AttributeError가 raise됩니다.
        """
        def save_prev_settings():
            # is_stable_connection and timeout must be defined prior to short_connection.
            self._prev_IS_STABLE_CONNECTION = self.IS_STABLE_CONNECTION
            self._prev_TIMEOUT = self.TIMEOUT
            self.TIMEOUT = 3

        def load_prev_settings():
            self.IS_STABLE_CONNECTION = self._prev_IS_STABLE_CONNECTION
            self.TIMEOUT = self._prev_TIMEOUT

        if not hasattr(self, '_short_connection'):
            if short_connection:
                self._prev_IS_STABLE_CONNECTION = None  # to suppress error
                self._prev_TIMEOUT = None  # to suppress error
                save_prev_settings()
        else:
            if short_connection and not self._short_connection:
                save_prev_settings()
            else:
                load_prev_settings()
        self._short_connection = short_connection

    @overload
    async def get_internet(  # noqa
        self,
        get_type: Literal['requests'],
        url: str,
        selector: None = None,
        is_run_in_executor: bool = False,
        attempt: int = 10,
        headers: dict | None = None
    ) -> requests.Response: ...

    @overload
    async def get_internet(  # noqa
        self,
        get_type: Literal['soup'],
        url: str,
        selector: None = None,
        is_run_in_executor: bool = False,
        attempt: int = 10,
        headers: dict | None = None
    ) -> bs: ...

    @overload
    async def get_internet(  # noqa
        self,
        get_type: Literal['soup_select'],
        url: str,
        selector: str,
        is_run_in_executor: bool = False,
        attempt: int = 10,
        headers: dict | None = None
    ) -> list: ...

    @overload
    async def get_internet(  # noqa
        self,
        get_type: Literal['soup_select_one'],
        url: str,
        selector: str,
        is_run_in_executor: bool = False,
        attempt: int = 10,
        headers: dict | None = None
    ) -> Tag | None: ...

    async def get_internet(  # noqa
        self,
        get_type: Literal['requests', 'soup', 'soup_select', 'soup_select_one'],
        url: str,
        selector: str | None = None,
        is_run_in_executor: bool = False,
        attempt: int = 10,
        headers: dict | None = None
    ) -> requests.Response | bs | list | Tag | None:
        """Get response/beautifulsoup/beautifulsoup tag list/beautifulsoup tag from internet.

        Args:
            get_type:
                인터넷에서 url로부터 받은 것으로부터 할 것이 무엇인지를 결정합니다.

                'requests': reqests.get한 값을 그대로(.content나 .test, .json()이 붙지 않은 원본 그대로) 반환합니다.
                'soup': reqests.get한 값을 BeautifulSoup를 거친 다음 반환합니다.
                'soup_select': BeautifulSoup를 거친 값을 .select()함수를 사용한 후 반환합니다.
                'soup_select_one': BeautifulSoup를 거친 값을 .select_one()함수를 사용한 후 반환합니다.
            url: 가져올 URL을 결정합니다.
            attempt:
                self.IS_STABLE_CONNECTION이 False일 때 몇 번 시도한 뒤 포기할지를 결정합니다. 기본값은 10입니다.
                예를 들어 attempt가 10이라면 만약 해당 사이트에 연결을 10번 시도한 뒤에도 실패한다면 포기하고 ConnectionError를 raise합니다.'
            headers: requests.get을 보낼 때 사용할 header를 받습니다. 만약 없을 경우 self.HEADERS를 대신 사용합니다.
        Returns:
            반환값은 어떤 get_type을 사용했는가에 따라 다르다.
            'requests': requests.Response
            'soup': BeautifulSoup
            'soup_select': list[bs4.element.Tag]
            'soup_select_one': bs4.element.Tag
        Raises:
            ConnectionError:
                만약 연결 오류 횟수가 시도 횟수를 넘어서면 이 에러를 발생합니다.
                에러가 반복되면시도 횟수(attempt 인자)를 늘리거나 timeout을 길게 설정해 보세요.
            이외에도 이 함수는 loop.run_in_executor나 request.get(), bs()(BeautifulSoup를 의미합니다.), soup.select(), soup.select_one()을 사용하기에 해당 함수에서 오류가 날 수 있습니다.
            self.loop.run_in_executor에서 오류가 발생한 경우:
                이는 self.loop가 initiate되지 않아 생긴 오류일 가능성이 큽니다.
                self.IS_STABLE_CONNECTION를 False로 하거나 이 함수가 download_one_webtoon_async가 호출된 뒤에 사용하세요.
            requests.get()에서 오류가 발생한 경우: 해당 URL을 통해 request를 보내는 과정에서 오류가 발생한 것입니다. url, header, timeout을 종합적으로 살펴보세요.
            bs()에서 오류가 발생한 경우: 잘못된 BeautifulSoup 호출로 대부분 response가 올바르지 않을 가능성이 큽니다. response(requests.get의 결과)를 확인하세요.
            soup.select()/soup.select_one()에서 오류가 발생한 경우: soup나 selector가 올바르지 않을 가능성이 큽니다. soup나 selector를 확인하세요.
        """
        async def send_get_request():
            if is_run_in_executor:
                response = await self.loop.run_in_executor(None, lambda: requests.get(url, headers=headers, timeout=self.TIMEOUT))
            else:
                response = requests.get(url, headers=headers, timeout=self.TIMEOUT)
            return response

        if not headers:
            headers = self.HEADERS

        if self.IS_STABLE_CONNECTION:
            response = await send_get_request()
        else:
            response = requests.Response()
            is_success = False
            for _ in range(attempt):
                try:
                    response = await send_get_request()
                except ConnectionError:
                    print('A connection error occured. But don\'t worry. It should be normal process. Retrying...')
                else:
                    is_success = True
                    break
            if not is_success:
                raise ConnectionError('Trying hard but failed. Maybe low attempt or timeout settizng is reason.'
                                      ' Trying increasing attempt time or timeout. Or sometimes it is caused by invaild titleid.')

        if get_type in ('soup', 'soup_select', 'soup_select_one'):
            soup = bs(response.text, "html.parser")
            if get_type == 'soup':
                return soup
            if selector is None:
                raise ValueError('Selector can\'t be None.')
            if get_type == 'soup_select':
                return soup.select(selector)
            if get_type == 'soup_select_one':
                return soup.select_one(selector)
        elif get_type == 'requests':
            return response
        else:
            raise ValueError('Unknown get_type.')

    def _set_pbar(self, description: str) -> None:
        """로그를 남길 때 tqdm을 사용할지 print를 사용할지 self.PBAR_INDEPENDENT를 통해 결정합니다.

        self.pbar_independent가 True라면 print를 사용하고, False라면 pbar를 이용합니다. 이는 __init__ 함수에서 결정합니다.
        만약 사용자에게 꼭 알려야 하는 중요한 것이 있다면 이 함수가 아닌 직접 print를 사용하는 것을 권합니다.

        Args:
            description: print하거나 pbar에 표시해야 하는 것.

        Raises:
            AttributeError:
                download_one_webtoon_async(으)로 시작하지 않은 함수에서 이 함수를 호출한다면 생가는 오류입니다.
                예를 들어, 만약 download_one_episode 함수를 단독으로 실행했다면, self.pbar가 선언되지 않았기 때문에 오류가 발생합니다.
                오류를 피하려면 처음 시작할 때 pbar_independent를 True로 하거나 download_one_webtoon_async을/를 사용하는 것을 추천합니다.
        """
        if self.PBAR_INDEPENDENT:
            print(description)
        else:
            self.pbar.set_description(description)

    @staticmethod
    def get_file_extension(filename_or_url: str) -> str | None:
        """Get file extionsion of filename_or_url.

        only supports jpg/png/jpeg/gif file format. If URL has queries, this ignores it.

        Args:
            filename_or_url: 파일 확장자가 궁금한 파일명이나 URL. 이때 URL 쿼리는 무시됩니다.

        Returns:
            파일 확장자를 반환합니다.
        """
        serch_result: re.Match | None = re.search(r'(?<=[.])(jpg|png|jpeg|gif|webp)(?=[?].+$|$)', filename_or_url, re.I)

        return None if serch_result is None else serch_result[0]
        # return filename_or_url.split('.')[-1].lower()

    @staticmethod
    def get_safe_file_name(file_or_diretory_name: str) -> str:
        """Translate file or diretory name to accaptable name.

        Caution: Don't put here diretory path beacause it will translate slash and backslash to acceptable(and cannot be used for going directory) name.
        """
        # sourcery skip: remove-zero-from-range
        table = str.maketrans('\\/:*?"<>|\t\n', '⧵／：＊？＂＜＞∣   ')
        table.update(
            {i: 32 for i in range(0, 31)}
        )

        processed = html.unescape(file_or_diretory_name)  # change things like "&amp;" to "'".

        processed = processed.translate(table).strip()

        processed = re.sub(r'\.$', '．', processed)

        return processed

    @property
    def BASE_DIR(self):
        return self._BASE_DIR

    @BASE_DIR.setter
    def BASE_DIR(self, BASE_DIR):
        self._BASE_DIR = Path(BASE_DIR)

################################## MAIN ACTION ##################################

    def download_one_webtoon(self, titleid: TitleId, episode_no_range: tuple[int, int] | int | None = None, merge: int | None = None) -> None:
        """async를 사용하지 않는 일반 상태일 경우 사용하는 함수이다. 사용법은 download_one_webtoon_async와 동일하다."""
        asyncio.run(self.download_one_webtoon_async(titleid, episode_no_range, merge))

    async def download_one_webtoon_async(self, titleid: TitleId, episode_no_range: tuple[int, int] | int | None = None, merge: int | None = None) -> None:
        """웹툰 다운로드의 주죽이 되는 함수. 이 함수를 통해 웹툰을 다운로드한다.

        주의: 유료 회차는 다운로드받을 수 없다.
        :titleid: 다운로드할 웹툰의 titleid 혹은 title_no를 입력한다.
        :episode_no_range: 다운로드할 회차를 정한다.
                                tuple일 경우: (처음, 끝) 순서로 값을 받는다. 이때 끝을 포함한다.
                                    예) (1,10): 1회차부터 10회차를 다운로드함
                                int일 경우: 한 회차만 다운로드 받는다.
                                None일 경우: 웹툰의 모든 회차를 다운로드 받는다.
        :merge: 웹툰을 모두 다운로드 받은 뒤 웹툰을 묶는다.
        """
        self.loop = asyncio.get_running_loop()

        title = self.get_safe_file_name(await self.get_title(titleid))
        webtoon_dir_name = await self.get_webtoon_dir_name(titleid, title)
        webtoon_dir = self.BASE_DIR / webtoon_dir_name
        self.webtoon_dir = webtoon_dir

        webtoon_dir.mkdir(parents=True, exist_ok=True)

        await self.save_webtoon_thumbnail(titleid, title, webtoon_dir)

        episode_no_list = await self.get_all_episode_no(titleid)
        if not episode_no_range:
            episode_no_list_plus_1 = range(1, len(episode_no_list) + 1)
        elif isinstance(episode_no_range, int):
            episode_no_list_plus_1 = (episode_no_range,)
        else:
            start, end = episode_no_range
            episode_no_list_plus_1 = range(start, end + 1)

        # episode_nos_plus_1 starts with 1, but episode_no starts with 0, so it needs to be subtracted from 1
        self.pbar = tqdm([i - 1 for i in episode_no_list_plus_1])
        for episode_no in self.pbar:
            await self.download_one_episode(episode_no, titleid, webtoon_dir)
        print(f'A webtoon {title} download ended.')

        webtoon_dir = await self.lezhin_unshuffle_process(titleid, webtoon_dir)

        if merge is not None:
            print('Merging webtoon has started...')
            fd = FolderManager()
            # print(webtoon_dir, fd)
            fd.merge_webtoon_episodes(webtoon_dir, 5)
            print('Merging webtoon ended.')

    async def get_webtoon_dir_name(self, titleid: TitleId, title: str) -> str:
        return f'{title}({titleid})'

    async def lezhin_unshuffle_process(self, titleid: TitleId, base_webtoon_dir: Path):
        """For lezhin's shuffle process. This function changes webtoon_dir to unshuffled webtoon's directory."""
        return base_webtoon_dir

    def _check_validate_of_files(self, episode_dir: Path, episode_no: int, image_urls: list, subtitle: str) -> None | bool:
        """episode_dir를 생성하고 이미 있다면 해당 폴더 내 내용물이 적합한지 조사한다.

        None를 return한다면 회차를 다운로드해야 한다는 의미이다.
        True를 return하면 해당 회차가 이미 완전히 다운로드되어 있으며, 따라서 다운로드를 지속할 이유가 없음을 의미한다.
        """
        try:
            episode_dir.mkdir()
        except FileExistsError:
            self._set_pbar(f'checking integrity of {subtitle}')
            is_filename_appropriate = all(re.match(r"\d{3}[.](png|jpg|jpeg|bmp|gif)", file) for file in os.listdir(episode_dir))
            if not is_filename_appropriate or len(image_urls) != len(os.listdir(episode_dir)):
                self._set_pbar(f'{subtitle} is not vaild. Automatically restore files.')
                shutil.rmtree(episode_dir)
                episode_dir.mkdir()
            else:
                self._set_pbar(f'skipping {subtitle}')
                return True

    async def download_one_episode(self, episode_no: int, titleid: TitleId, webtoon_dir: Path) -> None:
        """한 회차를 다운로드받는다."""
        subtitle = self.get_safe_file_name(await self.get_subtitle(titleid, episode_no))

        if not subtitle:
            print(f'this episode is not free or not yet created. This episode won\'t be loaded. {episode_no=}')
            self._set_pbar('unknown episode')
            return

        episode_images_url = await self.get_episode_images_url(titleid, episode_no)

        if episode_images_url is None:  # for lezhin
            print(f'this episode is not free or not yet created. This episode won\'t be loaded. {episode_no=}')
            self._set_pbar('unknown episode')
            return

        episode_dir = webtoon_dir / f'{episode_no + 1:04d}. {subtitle}'
        if self._check_validate_of_files(episode_dir, episode_no, episode_images_url, subtitle):
            return

        self._set_pbar(f'downloading {subtitle}')
        get_image_coroutines = (self.download_single_image(episode_dir, element, i) for i, element in enumerate(episode_images_url))
        await asyncio.gather(*get_image_coroutines)

    async def download_single_image(self, episode_dir: Path, url: str, image_no: int, default_file_extension: str | None = None) -> None:
        """Download image from url and returns to {episode_dir}/{file_name(translated to accactable name)}."""
        image_extension = self.get_file_extension(url)

        # for Bufftoon
        if image_extension is None:
            if default_file_extension is None:
                raise ValueError('File extension not detected.')
            image_extension = default_file_extension

        file_name = f'{image_no:03d}.{image_extension}'

        # self._set_pbar(f'{episode_dir}|{file_name}')
        image_raw: bytes = (await self.get_internet(get_type='requests', url=url, is_run_in_executor=True)).content

        file_dir = episode_dir / file_name
        file_dir.write_bytes(image_raw)

    @abstractmethod
    async def get_all_episode_no(self, titleid: TitleId) -> list:
        """웹툰에서 전체 에피소드를 가져온다."""
        return (await self.get_webtoon_data(titleid))['episode_ids']

    async def episode_no_to_episode_id(self, titleid: TitleId, episode_no: int, reverse: bool = False) -> int:
        """reverse가 참일 경우 반대로 episode_id에서 episode_no를 불러옴."""
        if not reverse:
            return (await self.get_all_episode_no(titleid))[episode_no]
        else:
            return (await self.get_all_episode_no(titleid)).index(episode_no)

    @abstractmethod
    async def get_title(self, titleid: TitleId) -> str:
        """웹툰의 title을 불러온다. 기본 구현을 사용할 시 super()를 이용하세요."""
        return (await self.get_webtoon_data(titleid))['title']

    @abstractmethod
    async def get_subtitle(self, titleid: TitleId, episode_no: int) -> str:
        """부제목, 즉 회차의 제목을 불러온다. 기본 구현을 사용할 시 super()를 이용하세요."""
        return (await self.get_webtoon_data(titleid))['subtitles'][episode_no]

    @abstractmethod
    async def save_webtoon_thumbnail(self, titleid: TitleId, title: str, thumbnail_dir: Path, default_file_extension: str | None = None) -> None:
        """웹툰의 썸네일을 불러오고 thumbnail_dir에 저장합니다. 기본 구현을 사용할 시 super()를 이용하세요."""
        thumbnail_data: str | tuple[bytes, str] = (await self.get_webtoon_data(titleid))['webtoon_thumbnail']
        if isinstance(thumbnail_data, str):  # It means thumnail_data is URL
            image_extension = self.get_file_extension(thumbnail_data)
            if image_extension is None:
                if default_file_extension is None:
                    raise ValueError('File extension not detected.')
                image_extension = default_file_extension
            image_raw = (await self.get_internet(get_type='requests', url=thumbnail_data)).content
        elif isinstance(thumbnail_data, tuple):  # It means thumnail_data is raw image data
            image_raw, image_extension = thumbnail_data
        else:
            raise ValueError('Thumbnail_data is invalid; It must be string or bytes.')

        image_path = thumbnail_dir / f'{title}.{image_extension}'
        image_path.write_bytes(image_raw)

    @abstractmethod
    async def get_episode_images_url(self, titleid: TitleId, episode_no: int) -> list:
        """해당 회차를 구성하는 이미지들을 불러온다. 기본 구현을 사용할 시 super()를 이용하세요."""
        return (await self.get_webtoon_data(titleid))['episode_images_url'][episode_no]

    @overload
    async def get_webtoon_data(self, titleid: TitleId) -> dict[Literal['title'], str]: ... # noqa

    @overload
    async def get_webtoon_data(self, titleid: TitleId) -> dict[Literal['subtitles'], list[str]]: ... # noqa

    @overload
    async def get_webtoon_data(self, titleid: TitleId) -> dict[Literal['webtoon_thumbnail'], str | tuple[bytes | str]]: ... # noqa

    @overload
    async def get_webtoon_data(self, titleid: TitleId) -> dict[Literal['episode_images_url'], list[list[str]]]: ... # noqa

    @overload
    async def get_webtoon_data(self, titleid: TitleId) -> dict[Literal['episode_ids'], list[str]]: ... # noqa

    @abstractmethod
    @alru_cache(maxsize=4)
    async def get_webtoon_data(self, titleid: TitleId) \
        -> dict[Literal['title', 'subtitles', 'webtoon_thumbnail', 'episode_images_url', 'episode_ids'],
                list[str] | list[list[str]] | str | bytes | tuple[bytes | str]]:
        """웹툰에서 데이터를 불러옵니다. 많이 불리기 때문에 무조건 @lru_cache를 사용해야 합니다.

        Args:
            titleid (TitleId): titleid를 받습니다.

        Returns:
            dict: key에 따라 각각 자동으로 불러올 정보를 정의합니다.
                keys:
                    'title' (str): 웹툰의 제목 정보를 불러옵니다.
                    'subtitles' (list[str]): 웹툰의 부제목(에피소드 제목) 정보를 불러옵니다.
                    'webtoon_thumbnail' (str/tuple[bytes, str]): 웹툰의 썸네일 정보를 불러옵니다.
                        만약 값이 string일 경우는 URL로 추론하고 URL에서 정보를 불러오지만,
                        tuple일 경우에는 thumbnail raw data와 file extension으로 추론하고 thumbnail_dir에 저장합니다.
                    'episode_ids' (list(int)): episode id list를 불러옵니다.
                    'episode_images_url' (list[list[str]]): 실제 웹툰 이미지들의 url로 구성된 list입니다.
                        다만 이렇게 많은 양을 메모리에 올려놓는 것은 부담이 될 수 있습니다.
                이 key 중에서 없는 것이 있어도 상관 없습니다. 다만 그럴 경우 직접 구현하여야 합니다.
                만약 함수들이 독립적이고 각자 구현될 수 있다면 한 데에 모아 구현하는 것보다 각각에 해당하는 함수들에
                구현하고 super()를 이용하는 것이 합리적입니다.
        """
