import requests
from bs4 import BeautifulSoup as bs
import re
import os
import asyncio
import WebtoonScraper.getsoup as getsoup
# import localpackage.getsoup as getsoup
from tqdm import tqdm
import shutil

# def set_folders(classes, base_dir='webtoon', alt_dir='webtoon_merge', temp_dir='Temp'):
#     BASE_DIR, ALT_DIR, TEMP_DIR = base_dir, alt_dir, temp_dir

# def _set_folders(self, base_dir='webtoon', alt_dir='webtoon_merge', temp_dir='Temp):
#     self.base_dir, self.alt_dir, self.temp_dir = base_dir, alt_dir, temp_dir
    
class NaverWebtoonScraper:
    def __init__(self):
        self.table = str.maketrans('\\/:*?"<>|\t', '⧵／：＊？＂＜＞∣  ') # for translate filename for forbidden charactor.
        self.loop = asyncio.get_event_loop()
        self.user_agent = {'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36'}
    
    def _get_file_extension(self, filename_or_url:str):
        return filename_or_url.split('.')[-1].lower()
    
    def _get_acceptable_file_name(self, filename_or_diretory_name:str):
        '''Translate file or diretory name to accaptable name.
        Don't put here diretory path beacause it will translate slash and backslash to acceptable(and cannot be used for going directory) name.'''
        # translate unacceptable charactor.
        translated = filename_or_diretory_name.translate(self.table).strip()

        # 윈도우는 파일명 뒤에 .이 있으면 제거하고 파일을 생성한다. 따라서 .을 제거하는 re가 필요하다.(앞이나 중간은 상관없음)
        # if searched only single dot, replaced with full-width dot. Otherwise, replaced with '…' string. The number of dot is not preserved.
        is_single_dot_searched = re.search('(?<![.])[.]$', translated)
        if is_single_dot_searched:
            subbed = re.sub('[.]$', '．', translated)
        else:
            subbed = re.sub('[.]+$', '…', translated)

        return subbed
    
    
    def set_folders(self, base_dir='webtoon'):
        self.base_dir = base_dir.rstrip('/')

    def get_webtoons(self, *webtoons):
        '''Run crawler in sync function, get more details in "get_webtoons_async" function.'''
        self.loop.run_until_complete(self.get_webtoons_async(*webtoons))

    async def get_webtoons_async(self, *webtoons):
        '''
        Get webtoons automatically.\n
        If you want to download webtoon 766648, type like 'get_webtoons_async(76648)'.\n
        If you want to download some part of webtoon, type like 'get_webtoons_async({titleid:76648, range:(1,20)}).\n
        You can use keyword argument down below.\n
        :titleid:(Required) : webtoon you want to download. int or str required.\n
            value_range(Optional) : range of episode you want to download. Kepp in mind this means 'id' of that, webtoon, not what author determines.\n
                                    Form of value range: (start, stop) or None
                                        주의: start와 stop에서 stop은 해당 stop에 해당하는 id도 포함됩니다. range함수와는 다릅니다.
                                        None일 경우 자동으로 값이 잡힙니다. 하지만 기본값이 None이라 굳이 작성할 필요는 없습니다.
            best_challenge(Optional) : if webtoon is best chellenge, make it True. Otherwise, False.
        '''
        for webtoon in webtoons:
            if type(webtoon) == int:
                await self.download_one_webtoon_async(None, titleid=webtoon, best_challenge=None)
            elif type(webtoon) == dict:
                await self.download_one_webtoon_async(**webtoon)
            else:
                raise TypeError('Function only gets type int or dict')
            
    def determine_best_challenge(self, titleid):
        '''If webtoon is best challenge, this returns True. Otherwise, False.'''
        title = getsoup.get_soup_from_requests(f'https://comic.naver.com/webtoon/detail?titleId={titleid}', 'meta[property="og:title"]')
        title = title[0].get('content')
        if title:
            return False
        else:
            return True
        
    async def download_one_webtoon_async(self, value_range: tuple|None=None, titleid=766648, best_challenge=None, attempt=50):
        '''Check out docstring of get_webtoons_async.'''
        if best_challenge == None:
            best_challenge = self.determine_best_challenge(titleid)
            
        # 제목 추출
        if best_challenge:
            title = getsoup.get_soup_from_requests(f'https://comic.naver.com/bestChallenge/list?titleId={titleid}', 'meta[property="og:title"]')
        else:
            title = getsoup.get_soup_from_requests(f'https://comic.naver.com/webtoon/list?titleId={titleid}', 'meta[property="og:title"]')
        title = title[0]['content']

        title_dir = f'{self.base_dir}/{self._get_acceptable_file_name(title)}({titleid})'
        
        try:
            os.makedirs(title_dir)
        except FileExistsError:
            print(f'Folder "{title_dir}" already exists.')

        self._get_webtoon_thumbnail(titleid, title, title_dir)

        # i로 돌릴 것 가져오기 : None일 경우를 확인
        if not value_range:
            titleids = self._get_auto_episode_no(titleid, best_challenge, attempt=attempt)
        else:
            start, end = value_range
            titleids = range(start, end + 1)

        # 한 타이틀 전체 추출
        self.pbar = tqdm(list(titleids))
        for episode_no in self.pbar:
            if best_challenge:
                soup = getsoup.get_soup_from_requests(f'https://comic.naver.com/bestChallenge/detail?titleId={titleid}&no={episode_no}')
            else:
                soup = getsoup.get_soup_from_requests(f'https://comic.naver.com/webtoon/detail?titleId={titleid}&no={episode_no}')
            subtitle = soup.select_one('#subTitle_toolbar').text

            # 부제목이 추출되지 않는다면 잘못된 id에 접근한 것이다. 그 이유는 해당 id에 해당하는 웹툰이 삭제되었거나
            # 그 id가 아직 생성되지 않은 것이다. 혹은 유료 미리보기 상태일 수도 있다.
            if not subtitle:
                print('It looks like this episode is truncated or not yet created. This episode won\'t be loaded.')
                print(f'Webtoon title: {title}, title ID: {titleid}, episode ID: {episode_no}')
                self.pbar.set_description('wrong episode')
                continue
            
            subtitle_dir_able = self._get_acceptable_file_name(subtitle)

            # 이미지 리스트 추출
            # 이상하게 베도와 정식 웹툰은 웹툰이 보이는 위치가 다르다.
            if best_challenge:
                image_urls = soup.select('#comic_view_area > div > img')
            else:
                image_urls = soup.select('#sectionContWide > img')
            image_urls = [element['src'] for element in image_urls if not ('agerate' in element['src'] or 'ctguide' in element['src'])]

            # 한 에피소드 다운로드
            episode_dir = f'{title_dir}/{episode_no:04d}. {subtitle_dir_able}'
            # 디렉토리가 이미 있으면 다운로드를 스킵한다.
            try:
                os.mkdir(episode_dir)
            except FileExistsError:
                # print(f'skipping {i}')
                self.pbar.set_description(f'checking integrity of {episode_no}')
                if not all([re.match(r"\d{3}[.](png|jpg|jpeg|bmp|gif)", file) for file in os.listdir(episode_dir)]) or not len(image_urls) == len(os.listdir(episode_dir)):
                    self.pbar.set_description(f'integrity of {episode_no} is not vaild. Automatically restore files.')
                    shutil.rmtree(episode_dir)
                    os.mkdir(episode_dir)
                else:
                    self.pbar.set_description(f'skipping {episode_no}')
                    continue

            self.pbar.set_description('downloading')
            await self._download_one_episode(episode_dir, image_urls)
        print(f'A webtoon {title} download ended.')

    async def _download_one_episode(self, episode_dir, urls):
        # 한 에피소드 내 이미지들 다운로드
        # 코루틴 리스트 생성
        get_images_coroutines = (self._download_single_image(episode_dir, element, i) for i, element in enumerate(urls))
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

    def _get_auto_episode_no(self, titleid, best_challenge, attempt):
        '''Returns iterator of episode no info.'''
        selector = '.item > a > div > img'
        for i in range(attempt):
            if best_challenge:
                selected = getsoup.get_soup_from_requests(f'https://comic.naver.com/bestChallenge/detail?titleId={titleid}&no={i}', selector)
            else:
                selected = getsoup.get_soup_from_requests(f'https://comic.naver.com/webtoon/detail?titleId={titleid}&no={i}', selector)
            if selected:
                break
        if not selected:
            raise ValueError('soup is empty. Maybe attempt is too low?')
        return (int(selected_one.get('alt')) for selected_one in selected)

    def _get_webtoon_thumbnail(self, webtoon_id, title, title_dir):
        '''Get webtoon thumbnail from webtoon_id and make thumbnail picture file in <title_dir>/<title>.jpg'''
        image_url = getsoup.get_soup_from_requests(f'https://comic.naver.com/webtoon/list?titleId={webtoon_id}', 'meta[property="og:image"]')[0]['content']
        image_extension = self._get_file_extension(image_url)
        image_raw = requests.get(image_url, headers=self.user_agent).content
        with open(f'{title_dir}/{title}.{image_extension}', 'wb') as image:
            image.write(image_raw)