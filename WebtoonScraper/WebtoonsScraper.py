# webtoons
import re
import os
import asyncio
import shutil

import requests
from bs4 import BeautifulSoup as bs
from tqdm import tqdm

from WebtoonScraper import NaverWebtoonScraper
from WebtoonScraper.NaverWebtoonScraper import *
from WebtoonScraper.getsoup import *

class WebtoonsScraper(NaverWebtoonScraper):
    '''Scraping webtoons from webtoons.com'''
    def __init__(self):
        super().__init__()
        self.user_agent = {
            'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36',
            "Referer": "http://www.webtoons.com"
        }
        self.debug = False
        self.BASE_URL = 'https://www.webtoons.com/en/fantasy/watermelon'

    async def _get_title(self, titleid):
        title_function = lambda: get_soup_from_requests(f'{self.BASE_URL}/list?title_no={titleid}',
                                                   'meta[property="og:title"]',
                                                   user_agent=self.user_agent)
        title_original = await self._run_unreliable_function(title_function)
        return title_original[0]['content']

    async def _get_subtitle(self, titleid, episode_no):
        subtitle_function = lambda: get_soup_from_requests(
            f'{self.BASE_URL}/prologue/viewer?title_no={titleid}&episode_no={episode_no}',
            '#toolbar > div.info > div > h1',
            user_agent=self.user_agent
        )
        subtitle_original = await self._run_unreliable_function(subtitle_function)
        if subtitle_original == []:
            return None
        else:
            return subtitle_original[0].text

    async def _get_image_urls(self, titleid:int, episode_no:int):
        subtitle_function = lambda: get_soup_from_requests(
            f'{self.BASE_URL}/prologue/viewer?title_no={titleid}&episode_no={episode_no}',
            '#_imageList > img',
            user_agent=self.user_agent
        )
        elements = await self._run_unreliable_function(subtitle_function)
        return [element.get('data-url') for element in elements]

    async def download_one_webtoon_async(self, value_range: tuple|None=None, titleid=1435, attempt=50):
        '''Check out docstring of get_webtoons_async.'''
        # if best_challenge == None:
        #     best_challenge = self.determine_best_challenge(titleid)

        title = await self._get_title(titleid)
        title = self._get_acceptable_file_name(title)
        webtoon_dir = f'{self.base_dir}/{title}({titleid})'

        try:
            os.makedirs(webtoon_dir)
        except FileExistsError:
            print(f'Folder "{webtoon_dir}" already exists.')

        await self._get_webtoon_thumbnail(titleid, title, webtoon_dir)

        # i로 돌릴 것 가져오기 : None일 경우를 확인
        if not value_range:
            titleids = await self._get_auto_episode_no(titleid, attempt=attempt)
        else:
            start, end = value_range
            titleids = range(start, end + 1)

        # 한 타이틀 전체 추출
        self.pbar = tqdm(list(titleids))
        for episode_no in self.pbar:
            await self._download_one_episode(episode_no, titleid, webtoon_dir, title)
        print(f'A webtoon {title} download ended.')

    async def _download_one_episode(self, episode_no, titleid, webtoon_dir, title):
        subtitle = await self._get_subtitle(titleid, episode_no)

        # 부제목이 추출되지 않는다면 잘못된 id에 접근한 것이다. 그 이유는 해당 id에 해당하는 웹툰이 삭제되었거나
        # 그 id가 아직 생성되지 않은 것이다. 혹은 유료 미리보기 상태일 수도 있다.
        if not subtitle:
            print('It looks like this episode is truncated or not yet created. This episode won\'t be loaded.')
            print(f'Webtoon title: {title}, title ID: {titleid}, episode ID: {episode_no}')
            self.pbar.set_description('wrong episode')
            return

        subtitle = self._get_acceptable_file_name(subtitle)

        # 이미지 리스트 추출
        # 이상하게 베도와 정식 웹툰은 웹툰이 보이는 위치가 다르다.
        image_urls = await self._get_image_urls(titleid, episode_no)

        # 한 에피소드 다운로드
        episode_dir = f'{webtoon_dir}/{episode_no:04d}. {subtitle}'
        # 디렉토리가 이미 있으면 다운로드를 스킵한다.
        try:
            os.mkdir(episode_dir)
        except FileExistsError:
            # print(f'skipping {i}')
            self.pbar.set_description(f'checking integrity of {episode_no}')
            if not all(re.match(r"\d{3}[.](png|jpg|jpeg|bmp|gif)", file) for file in os.listdir(episode_dir)) or not len(image_urls) == len(os.listdir(episode_dir)):
                self.pbar.set_description(f'integrity of {episode_no} is not vaild. Automatically restore files.')
                shutil.rmtree(episode_dir)
                os.mkdir(episode_dir)
            else:
                self.pbar.set_description(f'skipping {episode_no}')
                return

        self.pbar.set_description('downloading')

        # 한 에피소드 내 이미지들 다운로드
        # 코루틴 리스트 생성
        get_images_coroutines = (self._download_single_image(episode_dir, element, i) for i, element in enumerate(image_urls))
        await asyncio.gather(*get_images_coroutines)

    async def _download_single_image(self, episode_dir, url, image_no):
        '''download image from url and returns to {episode_dir}/{file_name(translated to accactable name)}'''
        image_extension = self._get_file_extension(url)
        file_name = self._get_acceptable_file_name(f'{image_no:03d}.{image_extension}')

        self.pbar.set_description(episode_dir + '|' + file_name)
        get_image_raw = lambda: requests.get(url, headers=self.user_agent, timeout=self.TIMEOUT).content
        image_raw = await self._run_unreliable_function(get_image_raw)

        with open(f'{episode_dir}/{file_name}', 'wb') as image:
            image.write(image_raw)

    async def _get_auto_episode_no(self, titleid, attempt):
        '''Returns iterator of episode no info. attempt is currently useless. Best chellenge is not considered.'''
        get_episode_function = lambda: get_soup_from_requests(
            f'{self.BASE_URL}/prologue/viewer?title_no={titleid}&episode_no={1}',
            '#_bottomEpisodeList > div.episode_cont > ul > li',
            user_agent=self.user_agent
        )
        elements = await self._run_unreliable_function(get_episode_function)
        return (int(element.get('data-episode-no')) for element in elements)

    async def _run_unreliable_function(self, function, attempt=10):
        '''Run function that has unreliable connection in async mode.'''
        for _ in range(attempt):
            try:
                # print('start trying.')
                return await self.loop.run_in_executor(None, function)
            # except (ConnectionResetError, ConnectionError) as e:
            #     print('error :', e)
            #     pass
            # except Exception as e:
            #     raise Exception(f'error : {e}, exception is raised.')
            except Exception as e:
                # if e.errno == 'Connection aborted.':
                #     continue
                if self.debug:
                    raise Exception(f'error: {e}') from e
                else:
                    print(f'error: {e}, retrying...')
        raise ConnectionError('Trying hard but failed. increasing the number of attept may be helpful.')

    async def _get_webtoon_thumbnail(self, webtoon_id, title, title_dir):
        '''Get webtoon thumbnail from webtoon_id and make thumbnail picture file in <title_dir>/<title>.jpg'''
        image_url_function = lambda: get_soup_from_requests(f'{self.BASE_URL}/list?title_no={webtoon_id}', 'meta[property="og:image"]')[0]['content']
        image_url = await self._run_unreliable_function(image_url_function)
        image_extension = self._get_file_extension(image_url)
        image_raw_function = lambda: requests.get(image_url, headers=self.user_agent).content
        image_raw = await self._run_unreliable_function(image_raw_function)
        with open(f'{title_dir}/{title}.{image_extension}', 'wb') as image:
            image.write(image_raw)

    async def _get_real_thumbnail(self, webtoon_id, title, title_dir):
        '''Get webtoon 'real' thumbnail from webtoon_id and make thumbnail picture file in <title_dir>/<title>.jpg'''
        @self._run_unreliable_function_decorator
        def response_function():
            return requests.get(f'{self.BASE_URL}/rss?title_no={webtoon_id}', timeout=self.TIMEOUT)
        response = await response_function()
        # response_function = lambda: requests.get(f'{self.BASE_URL}/rss?title_no={webtoon_id}', timeout=self.TIMEOUT)
        # response = await self._run_unreliable_function(response_function)

        soup = bs(response.text, 'xml')
        image_url = soup.select_one('channel > image > url').text
        image_extension = self._get_file_extension(image_url)
        image_raw_function = lambda: requests.get(image_url, headers=self.user_agent, timeout=self.TIMEOUT).content
        image_raw = await self._run_unreliable_function(image_raw_function)
        with open(f'{title_dir}/{title}.{image_extension}', 'wb') as image:
            image.write(image_raw)

    def _run_unreliable_function_decorator(self, function, attempt=10):
        '''Run function that has unreliable connection in async mode.'''
        async def decorated():
            for _ in range(attempt):
                try:
                    return await self.loop.run_in_executor(None, function)
                except Exception as e:
                    if self.debug:
                        raise Exception(f'error: {e}') from e
                    else:
                        print(f'error: {e}, retrying...')
            raise ConnectionError('Trying hard but failed. increasing the number of attept may be helpful.')
        return decorated
