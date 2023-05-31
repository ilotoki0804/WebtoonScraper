import re
import os
import asyncio
import shutil

import requests
from tqdm import tqdm

# 베도
from WebtoonScraper import NaverWebtoonScraper
from WebtoonScraper.getsoup import *

class BestChallengeScraper(NaverWebtoonScraper):
    '''Scraping webtoons from naver webtoon best challenge'''

    async def _get_title(self, titleid):
        title = get_soup_from_requests(f'https://comic.naver.com/bestChallenge/list?titleId={titleid}', 'meta[property="og:title"]')
        return title[0]['content']

    async def _get_subtitle(self, soup):
        subtitle = soup.select_one('#subTitle_toolbar')
        if not subtitle:
            return None
        return self._get_acceptable_file_name(subtitle.text)

    async def _get_image_urls(self, soup):
        image_urls = soup.select('#comic_view_area > div > img')
        return [element['src'] for element in image_urls if not ('agerate' in element['src'] or 'ctguide' in element['src'])]

    async def download_one_webtoon_async(self, value_range: tuple|None=None, titleid=766648, attempt=50):
        '''Check out docstring of get_webtoons_async. This is main function.'''

        title = await self._get_title(titleid)
        title = self._get_acceptable_file_name(title)
        webtoon_dir = f'{self.base_dir}/{title}({titleid})'

        try:
            os.makedirs(webtoon_dir)
        except FileExistsError:
            pass

        await self._get_webtoon_thumbnail(titleid, title, webtoon_dir)

        if not value_range:
            titleids = self._get_auto_episode_no(titleid, attempt=attempt)
        else:
            start, end = value_range
            titleids = range(start, end + 1)

        self.pbar = tqdm(list(titleids))
        for episode_no in self.pbar:
            await self._download_one_episode(episode_no, titleid, webtoon_dir, title)
        print(f'A webtoon {title} download ended.')

    async def _download_one_episode(self, episode_no, titleid, webtoon_dir, title):
        soup = get_soup_from_requests(f'https://comic.naver.com/bestChallenge/detail?titleId={titleid}&no={episode_no}')
    
        subtitle = await self._get_subtitle(soup)

        # 부제목이 추출되지 않는다면 잘못된 id에 접근한 것이다. 그 이유는 해당 id에 해당하는 웹툰이 삭제되었거나
        # 그 id가 아직 생성되지 않은 것이다. 혹은 유료 미리보기 상태일 수도 있다.
        if not subtitle:
            print('It looks like this episode is truncated or not yet created. This episode won\'t be loaded.')
            print(f'Webtoon title: {title}, title ID: {titleid}, episode ID: {episode_no}')
            self.pbar.set_description('wrong episode')
            return

        image_urls = await self._get_image_urls(soup)

        episode_dir = f'{webtoon_dir}/{episode_no:04d}. {subtitle}'

        try:
            os.mkdir(episode_dir)
        except FileExistsError:
            self.pbar.set_description(f'checking integrity of {episode_no}')
            if not all(re.match(r"\d{3}[.](png|jpg|jpeg|bmp|gif)", file) for file in os.listdir(episode_dir))\
                or not len(image_urls) == len(os.listdir(episode_dir)):
                self.pbar.set_description(f'integrity of {episode_no} is not vaild. Automatically restore files.')
                shutil.rmtree(episode_dir)
                os.mkdir(episode_dir)
            else:
                self.pbar.set_description(f'skipping {episode_no}')
                return

        self.pbar.set_description('downloading')
        # 한 에피소드 내 이미지들 다운로드
        # 코루틴 리스트 생성
        get_images_coroutines = (self._download_single_image(episode_dir, url, i) for i, url in enumerate(image_urls))
        await asyncio.gather(*get_images_coroutines)

    async def _download_single_image(self, episode_dir, url, image_no):
        '''download image from url and returns to {episode_dir}/{file_name(translated to accactable name)}'''

        image_extension = self._get_file_extension(url)
        file_name = self._get_acceptable_file_name(f'{image_no:03d}.{image_extension}')

        self.pbar.set_description(episode_dir + '|' + file_name)
        get_image_raw = lambda url: requests.get(url, headers=self.user_agent).content
        image_raw = await self.loop.run_in_executor(None, get_image_raw, url)

        with open(f'{episode_dir}/{file_name}', 'wb') as image:
            image.write(image_raw)

    def _get_auto_episode_no(self, titleid, attempt):
        '''Returns iterator of episode no info.'''
        selector = '.item > a > div > img'
        for i in range(attempt):
            selected = get_soup_from_requests(f'https://comic.naver.com/bestChallenge/detail?titleId={titleid}&no={i}', selector)
            if selected:
                break
        if not selected:
            raise ValueError('soup is empty. Maybe attempt is too low?')
        return (int(selected_one.get('alt')) for selected_one in selected)

    async def _get_webtoon_thumbnail(self, webtoon_id, title, title_dir):
        '''Get webtoon thumbnail from webtoon_id and make thumbnail picture file in <title_dir>/<title>.jpg
        No reason for async but WebtoonsScraper'''
        image_url = get_soup_from_requests(f'https://comic.naver.com/webtoon/list?titleId={webtoon_id}', 'meta[property="og:image"]')[0]['content']
        image_extension = self._get_file_extension(image_url)
        image_raw = requests.get(image_url, headers=self.user_agent, timeout=self.TIMEOUT).content
        with open(f'{title_dir}/{title}.{image_extension}', 'wb') as image:
            image.write(image_raw)
