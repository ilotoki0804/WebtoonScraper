'''Abstract Class of all scrapers.
resolved: make pbar independent from all scrapers.
resolved: make _get_internet
resolved: replace string to pathlib
resolved: make abstract scraper
resolved: str이라 되어 있는 path들 모두 path 또는 purepath로 바꾸기
'''

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
    '''Abstract class of all scrapers.'''
    def __init__(self, pbar_independent: bool=False, short_connection=False) -> None:
        self.loop = asyncio.get_event_loop()
        self.USER_AGENT = {
            'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
            '(KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36'
            }
        self.set_folders()
        self.TIMEOUT = 500
        self.PBAR_INDEPENDENT = pbar_independent
        if short_connection:
            self.TIMEOUT = 3
            self.IS_STABLE_CONNECTION = False
    
    @abstract_attribute
    def BASE_URL(self):
        pass
    
    @abstract_attribute
    def IS_STABLE_CONNECTION(self):
        pass
    
    # @profile
    async def get_internet(
            self, get_type: Literal['requests', 'soup', 'soup_select', 'soup_select_one'], 
            url: str, selector=None, 
            is_run_in_executor=False, 
            attempt: int=10, 
            headers=None
            ) -> requests.Response|bs|list|bsTag|None:
        '''get anything from internet
        NOT FULLY DOCUMENTED!
        resolved: timeout
        '''
        async def send_get_request():
            if is_run_in_executor:
                response = await self.loop.run_in_executor(None, lambda: requests.get(url, headers=headers, timeout=self.TIMEOUT))
            else:
                response = requests.get(url, headers=headers, timeout=self.TIMEOUT)
            return response

        if not headers:
            headers = self.USER_AGENT

        if self.IS_STABLE_CONNECTION:
            response = await send_get_request()
        else:
            for _ in range(attempt):
                try:
                    response = await send_get_request()
                    break
                except Exception as e:
                    print('An error occured. Retrying...')
                    print(f'Error detail: {e}')

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
        '''self.pbar_independent가 True라면 print를 사용하고, False라면 pbar를 이용한다.
        pbar는 처음 함수를 호출할 때 확인할 수 있다.
        :description: print하거나 pbar에 표시할 것.
        '''
        if self.PBAR_INDEPENDENT:
            print(description)
        else:
            self.pbar.set_description(description)

    def get_file_extension(self, filename_or_url: str) -> str:
        '''get file extionsion of filename_or_url. only supports jpg/png/jpeg/gif file format. If URL has queries, this ignores it.'''
        return re.search(r'(?<=[.])(jpg|png|jpeg|gif)(?=[?].+$|$)', filename_or_url, re.I).group()
        # return filename_or_url.split('.')[-1].lower()

    @staticmethod
    def get_acceptable_file_name(file_or_diretory_name: str, strict_checking: bool=False) -> str:
        '''Translate file or diretory name to accaptable name.
        Don't put here diretory path beacause it will translate slash and backslash to acceptable(and cannot be used for going directory) name.'''
        table = str.maketrans('\\/:*?"<>|\t', '⧵／：＊？＂＜＞∣  ')

        unescaped = html.unescape(file_or_diretory_name)
        
        translated = unescaped.translate(table).strip()

        is_single_dot_searched = re.search('(?<![.])[.]$', translated)
        if is_single_dot_searched:
            subbed = re.sub('[.]$', '．', translated)
        else:
            subbed = re.sub('[.]+$', '…', translated)

        if strict_checking:
            strict_checked_string = ''
            for chractor in subbed:
                if ord(chractor) in (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 34, 42, 58, 60, 62, 63, 124):
                    strict_checked_string += ' '
                else:
                    strict_checked_string += chractor
            return strict_checked_string
        return subbed
    
    def set_folders(self, base_dir: str='webtoon') -> str:
        '''set base folder.'''
        self.BASE_DIR = Path(base_dir)

################################## MAIN ACTION ##################################

    def download_one_webtoon(self, titleid: int, value_range: tuple|int|None=None) -> None:
        '''async를 사용하지 않는 일반 상태일 경우 사용하는 함수이다. 사용법은 download_one_webtoon_async와 동일하다.'''
        self.loop.run_until_complete(self.download_one_webtoon_async(titleid, value_range))

    # @profile
    async def download_one_webtoon_async(self, titleid, episode_no_range: tuple|int|None=None) -> None:
        '''웹툰 다운로드의 주죽이 되는 함수. 이 함수를 통해 웹툰을 다운로드한다.
        주의: 유료 회차는 다운로드받을 수 없다.
        :titleid: 다운로드할 웹툰의 titleid 혹은 title_no를 입력한다.
        :episode_no_range: 다운로드할 회차를 정한다.
                                tuple일 경우: (처음, 끝) 순서로 값을 받는다. 이때 끝을 포함한다.
                                    예) (1,10): 1회차부터 10회차를 다운로드함
                                int일 경우: 한 회차만 다운로드 받는다.
                                None일 경우: 웹툰의 모든 회차를 다운로드 받는다.
        :attempt(deprecated): episode_no_range가 None이어서 자동으로 웹툰을 다운로드 받을 경우 몇 번째 episode까지 다운로드 받을지 결정한다.
        '''

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
        '''웹툰의 title을 불러온다.'''
        pass

    @abstractmethod
    async def save_webtoon_thumbnail(self, titleid: int, title: str, thumbnail_dir: Path) -> None:
        '''웹툰의 썸네일을 불러오고 thumbnail_dir에 저장한다.'''
        pass
    
    @abstractmethod
    async def get_all_episode_no(self, titleid: int, attempt: int) -> Iterable:
        '''웹툰에서 전체 에피소드를 가져온다.'''
        pass

    # @profile
    def _check_validate_of_files(self, episode_dir: Path, episode_no: int, image_urls: list) -> None|bool:
        '''episode_dir를 생성하고 이미 있다면 해당 폴더 내 내용물이 적합한지 조사한다.
        None를 return한다면 회차를 다운로드해야 한다는 의미이다.
        True를 return하면 해당 회차가 이미 완전히 다운로드되어 있으며, 따라서 다운로드를 지속할 이유가 없음을 의미한다.
        '''
        try:
            episode_dir.mkdir()
        except FileExistsError:
            self._set_pbar(f'checking integrity of {episode_no=}')
            is_filename_appropriate = all(re.match(r"\d{3}[.](png|jpg|jpeg|bmp|gif)", file) for file in os.listdir(episode_dir))
            if not is_filename_appropriate or not len(image_urls) == len(os.listdir(episode_dir)):
                self._set_pbar(f'{episode_no=} is not vaild. Automatically restore files.')
                shutil.rmtree(episode_dir)
                episode_dir.mkdir()
            else:
                self._set_pbar(f'skipping {episode_no=}')
                return True

    # @profile
    async def download_one_episode(self, episode_no: int, titleid: int, webtoon_dir: Path) -> None:
        '''한 회차를 다운로드받는다.'''
        subtitle = await self.get_subtitle(titleid, episode_no, file_acceptable=True)

        if not subtitle:
            print(f'this episode is not free or not yet created. This episode won\'t be loaded. {episode_no=}')
            self._set_pbar('unknown episode')
            return

        episode_images_url = await self.get_episode_images_url(titleid, episode_no)

        episode_dir = webtoon_dir / f'{episode_no:04d}. {subtitle}'
        if self._check_validate_of_files(episode_dir, episode_no, episode_images_url):
            return

        self._set_pbar(f'{episode_no:04d}. {subtitle}')
        get_image_coroutines = (self.download_single_image(episode_dir, element, i) for i, element in enumerate(episode_images_url))
        await asyncio.gather(*get_image_coroutines)

    @abstractmethod
    async def get_subtitle(self, titleid: int, episode_no: int, file_acceptable: bool) -> str:
        '''부제목, 즉 회차의 제목을 불러온다.'''
        pass

    @abstractmethod
    async def get_episode_images_url(self, titleid: int, episode_no: int) -> list:
        '''해당 회차를 구성하는 이미지들을 불러온다.'''
        pass

    # @profile
    async def download_single_image(self, episode_dir: Path, url: str, image_no: int) -> None:
        '''download image from url and returns to {episode_dir}/{file_name(translated to accactable name)}'''
        image_extension = self.get_file_extension(url)
        file_name = f'{image_no:03d}.{image_extension}'

        # self._set_pbar(f'{episode_dir}|{file_name}')
        image_raw = await self.get_internet(get_type='requests', url=url, is_run_in_executor=True)
        image_raw = image_raw.content

        file_dir = episode_dir / file_name
        file_dir.write_bytes(image_raw)