"""Abstract Class of all scrapers."""

import re
import os
import asyncio
import shutil
import html
from pathlib import Path
from typing import Iterable, Literal
# from abc import ABCMeta
from abc import abstractmethod

from better_abc import ABCMeta, abstract_attribute
import requests
from bs4 import BeautifulSoup as bs
from tqdm import tqdm
from bs4.element import Tag as bsTag

class Scraper(metaclass=ABCMeta):
    """Abstract class of all scrapers.
    
    init, get_internet, 전반적인 로직 등은 모두 이 페이지에서 관리하고, 구체적인 다운로드 방법은 각각의 scraper들에게 맡깁니다.
    따라서 썸네일을 받아오거나 한 회차의 이미지 URL을 불러오는 등의 역할은 각자 scraper들에 구현되어 있습니다.
    """

    def __init__(self, pbar_independent: bool=False, short_connection=False) -> None:
        """시작에 필요한 여러가지를 관여합니다.
        
        header, timeout을 구성하고 set_folders()를 호출합니다.
        
        Args:
            pbar_independent: 만약 True라면 tqdm을 이용해서 로그를 표시하고, False라면 print를 통해서 로그를 표시합니다.
            short_connection:
                만약 True라면 timeout를 3초로 짧게 잡고 IS_STABLE_CONNECTION(거짓일 경우, 연결에 실패하면 재시도를 함.)을 False로 합니다.
                False라면 기본 설정을 유지하고 timeout도 길게(120초) 유지합니다.
        """
        # self.loop = asyncio.get_event_loop()
        self.HEADERS = {
            'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
            '(KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36'
            }
        self.set_folders()
        self.TIMEOUT = 120
        self.PBAR_INDEPENDENT = pbar_independent
        if short_connection:
            self.TIMEOUT = 3
            self.IS_STABLE_CONNECTION = False
    
    @abstract_attribute
    def BASE_URL(self):
        """Abstract 'attribute' for self.BASE_URL."""
        pass
    
    @abstract_attribute
    def IS_STABLE_CONNECTION(self):
        """Abstract 'attribute' for self.IS_STABLE_CONNECTION."""
        pass
    
    # @profile
    async def get_internet(
            self, get_type: Literal['requests', 'soup', 'soup_select', 'soup_select_one'], 
            url: str, selector=None, 
            is_run_in_executor=False, 
            attempt: int=10, 
            headers=None
            ) -> requests.Response|bs|list|bsTag|None:
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
            for _ in range(attempt):
                is_success = False
                try:
                    response = await send_get_request()
                    is_success = True
                    break
                except Exception as e:
                    print('An error occured. Retrying...')
                    print(f'Error detail: {e}')
            if not is_success:
                raise ConnectionError('Trying hard but failed. Maybe low attempt or timeout settizng is reason.'
                                      ' Trying increasing attempt time or timeout. Or sometimes it is caused by invaild titldid.')

        if get_type in ('soup', 'soup_select', 'soup_select_one'):
            soup = bs(response.text, "html.parser")
            if get_type == 'soup':
                return soup
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
    def get_file_extension(filename_or_url: str) -> str:
        """Get file extionsion of filename_or_url.
        
        only supports jpg/png/jpeg/gif file format. If URL has queries, this ignores it.

        Args:
            filename_or_url: 파일 확장자가 궁금한 파일명이나 URL. 이때 URL 쿼리는 무시됩니다.
        
        Returns:
            파일 확장자를 반환합니다.
        """
        serch_result: re.Match = re.search(r'(?<=[.])(jpg|png|jpeg|gif)(?=[?].+$|$)', filename_or_url, re.I)
        return serch_result.group()
        # return filename_or_url.split('.')[-1].lower()

    @staticmethod
    def get_acceptable_file_name(file_or_diretory_name: str, strict_checking: bool=False) -> str:
        """Translate file or diretory name to accaptable name.

        Caution: Don't put here diretory path beacause it will translate slash and backslash to acceptable(and cannot be used for going directory) name.
        """
        table = str.maketrans('\\/:*?"<>|\t\n', '⧵／：＊？＂＜＞∣   ')

        processed = html.unescape(file_or_diretory_name) # change things like "&amp;" to "'".
        
        processed = processed.translate(table).strip()

        processed = re.sub(r'\.$', '．', processed)

        if strict_checking:
            strict_checked_string = ''
            for chractor in processed:
                if ord(chractor) in (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21,
                                     22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 34, 42, 58, 60, 62, 63, 124):
                    strict_checked_string += ' '
                else:
                    strict_checked_string += chractor
            return strict_checked_string
        return processed
    
    def set_folders(self, base_dir: str='webtoon') -> None:
        """Set base folder."""
        self.BASE_DIR = Path(base_dir)

################################## MAIN ACTION ##################################

    def download_one_webtoon(self, titleid: int, value_range: tuple|int|None=None) -> None:
        """async를 사용하지 않는 일반 상태일 경우 사용하는 함수이다. 사용법은 download_one_webtoon_async와 동일하다."""
        asyncio.run(self.download_one_webtoon_async(titleid, value_range))
        # self.loop.run_until_complete(self.download_one_webtoon_async(titleid, value_range))

    # @profile
    async def download_one_webtoon_async(self, titleid, episode_no_range: tuple|int|None=None) -> None:
        """웹툰 다운로드의 주죽이 되는 함수. 이 함수를 통해 웹툰을 다운로드한다.

        주의: 유료 회차는 다운로드받을 수 없다.
        :titleid: 다운로드할 웹툰의 titleid 혹은 title_no를 입력한다.
        :episode_no_range: 다운로드할 회차를 정한다.
                                tuple일 경우: (처음, 끝) 순서로 값을 받는다. 이때 끝을 포함한다.
                                    예) (1,10): 1회차부터 10회차를 다운로드함
                                int일 경우: 한 회차만 다운로드 받는다.
                                None일 경우: 웹툰의 모든 회차를 다운로드 받는다.
        :attempt(deprecated): episode_no_range가 None이어서 자동으로 웹툰을 다운로드 받을 경우 몇 번째 episode까지 다운로드 받을지 결정한다.
        """
        self.loop = asyncio.get_running_loop()

        title = await self.get_title(titleid, file_acceptable=True)
        webtoon_dir = self.BASE_DIR / f'{title}({titleid})'

        webtoon_dir.mkdir(parents=True, exist_ok=True)

        await self.save_webtoon_thumbnail(titleid, title, webtoon_dir)

        if not episode_no_range:
            titleids = await self.get_all_episode_no(titleid, attempt=50)
        elif isinstance(episode_no_range, int):
            titleids = (episode_no_range,)
        else:
            start, end = episode_no_range
            titleids = range(start, end + 1)

        self.pbar = tqdm(list(titleids))
        for episode_no in self.pbar:
            await self.download_one_episode(episode_no, titleid, webtoon_dir)
        print(f'A webtoon {title} download ended.')

    @abstractmethod
    async def get_title(self, titleid: int, file_acceptable: bool) -> str:
        """웹툰의 title을 불러온다."""
        pass

    @abstractmethod
    async def save_webtoon_thumbnail(self, titleid: int, title: str, thumbnail_dir: Path) -> None:
        """웹툰의 썸네일을 불러오고 thumbnail_dir에 저장한다."""
        pass
    
    @abstractmethod
    async def get_all_episode_no(self, titleid: int, attempt: int) -> Iterable:
        """웹툰에서 전체 에피소드를 가져온다."""
        pass

    # @profile
    def _check_validate_of_files(self, episode_dir: Path, episode_no: int, image_urls: list, subtitle: str) -> None|bool:
        """episode_dir를 생성하고 이미 있다면 해당 폴더 내 내용물이 적합한지 조사한다.

        None를 return한다면 회차를 다운로드해야 한다는 의미이다.
        True를 return하면 해당 회차가 이미 완전히 다운로드되어 있으며, 따라서 다운로드를 지속할 이유가 없음을 의미한다.
        """
        try:
            episode_dir.mkdir()
        except FileExistsError:
            self._set_pbar(f'checking integrity of {subtitle}')
            is_filename_appropriate = all(re.match(r"\d{3}[.](png|jpg|jpeg|bmp|gif)", file) for file in os.listdir(episode_dir))
            if not is_filename_appropriate or not len(image_urls) == len(os.listdir(episode_dir)):
                self._set_pbar(f'{subtitle} is not vaild. Automatically restore files.')
                shutil.rmtree(episode_dir)
                episode_dir.mkdir()
            else:
                self._set_pbar(f'skipping {subtitle}')
                return True

    # @profile
    async def download_one_episode(self, episode_no: int, titleid: int, webtoon_dir: Path) -> None:
        """한 회차를 다운로드받는다."""
        subtitle = await self.get_subtitle(titleid, episode_no, file_acceptable=True)

        if not subtitle:
            print(f'this episode is not free or not yet created. This episode won\'t be loaded. {episode_no=}')
            self._set_pbar('unknown episode')
            return

        episode_images_url = await self.get_episode_images_url(titleid, episode_no)

        episode_dir = webtoon_dir / f'{episode_no:04d}. {subtitle}'
        if self._check_validate_of_files(episode_dir, episode_no, episode_images_url, subtitle):
            return

        self._set_pbar(f'downloading {subtitle}')
        get_image_coroutines = (self.download_single_image(episode_dir, element, i) for i, element in enumerate(episode_images_url))
        await asyncio.gather(*get_image_coroutines)

    @abstractmethod
    async def get_subtitle(self, titleid: int, episode_no: int, file_acceptable: bool) -> str:
        """부제목, 즉 회차의 제목을 불러온다."""
        pass

    @abstractmethod
    async def get_episode_images_url(self, titleid: int, episode_no: int) -> list:
        """해당 회차를 구성하는 이미지들을 불러온다."""
        pass

    # @profile
    async def download_single_image(self, episode_dir: Path, url: str, image_no: int) -> None:
        """Download image from url and returns to {episode_dir}/{file_name(translated to accactable name)}."""
        # print(url)
        image_extension = self.get_file_extension(url)
        file_name = f'{image_no:03d}.{image_extension}'

        # self._set_pbar(f'{episode_dir}|{file_name}')
        image_raw = await self.get_internet(get_type='requests', url=url, is_run_in_executor=True)
        image_raw = image_raw.content

        file_dir = episode_dir / file_name
        file_dir.write_bytes(image_raw)