# 네이버 웹툰 fetching(공식, 비동기적)
import requests
from bs4 import BeautifulSoup as bs
import re
import os
import pickle
import re
import asyncio
import functools
import getsoup as getsoup
from tqdm import tqdm
import shutil

class NaverWebtoonScraper:
    def __init__(self):
        # for aviod 403 error / user agent or Chrome
        self.user_agent = {'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36'}
        self.table = str.maketrans('\\/:*?"<>|\t', '⧵／：＊？＂＜＞∣  ') # for translate filename for forbidden charactor.
        self.loop = asyncio.get_event_loop() # for loop.run_in_executor()
        self.root = 'webtoon'

    def get_webtoons(self, *webtoons):
        '''Run crawler in sync function'''
        asyncio.run(self.get_webtoons_async(*webtoons))

    async def get_webtoons_async(self, *webtoons):
        '''Get webtoons automatically.\n
        If you want to download webtoon 766648, type like 'get_webtoons_async(76648)'.\n
        If you want to download some part of webtoon, type like 'get_webtoons_async({titleid:76648, range:(1,20)}).\n
        You can use keyword argument down below.\n
            titleid(Required) : webtoon you want to download. int or str required.\n
            value_range(Optional) : range of episode you want to download. Kepp in mind this means 'id' of that, webtoon, not what author determines.\n
                                    Form of value range: (start, stop) or None
                                        주의: start와 stop에서 stop은 해당 stop에 해당하는 id도 포함됩니다. range함수와는 다릅니다.
                                        None일 경우 자동으로 값이 잡힙니다. 하지만 굳이 작성할 필요는 없습니다.
            best_challenge(Optional) : if webtoon is best chellenge, make it True. Otherwise, False.'''
        for webtoon in webtoons:
            if type(webtoon) == int or type(webtoon) == str:
                titleid = int(webtoon)
                await self.download_one_webtoon(None, titleid=titleid, best_challenge=self.determine_best_challenge(titleid))
            elif type(webtoon) == dict:
                # dict를 받으면 kwargs로 변환해서 download_one_webtoon으로 변환
                async def default_for_kwargs(value_range=None, titleid=0, best_challenge=self.determine_best_challenge(webtoon['titleid']), attempt=10):
                    await self.download_one_webtoon(value_range=value_range, titleid=titleid, best_challenge=best_challenge, attempt=attempt)
                await default_for_kwargs(**webtoon)
            else:
                raise TypeError
            
    def determine_best_challenge(self, titleid):
        '''If webtoon is best challenge, this returns True. Otherwise, False.'''
        title = getsoup.get_soup_from_requests(f'https://comic.naver.com/webtoon/detail?titleId={titleid}', 'meta[property="og:title"]')
        title = title[0].get('content')
        if title:
            return False
        else:
            return True
        
    async def download_one_webtoon(self, value_range=None, titleid=766648, best_challenge=False, attempt=10):
        '''Check out doc of get_webtoons_async.'''
        if value_range:
            start, end = value_range
            if end == None:
                end = start
            
        # 제목 추출
        if best_challenge:
            a = requests.get(f'https://comic.naver.com/bestChallenge/list?titleId={titleid}')
        else:
            a = requests.get(f'https://comic.naver.com/webtoon/list?titleId={titleid}')
        soup = bs(a.text, "html.parser")
        title = soup.select_one('meta[property="og:title"]')

        # type checking
        if title == None:
            raise TypeError
        else:
            title = title['content']

        title = title
        title_dir = f'{self.root}/{title.translate(self.table)}({titleid})'
        # 디렉토리를 만들고 있으면 그대로 진행한다.
        try:
            os.makedirs(title_dir)
        except FileExistsError:
            print(f'"{title_dir}" already exist')

        # 웹툰 썸네일 가져오기
        self.get_webtoon_thumbnail(titleid, title, title_dir)

        # i로 돌릴 것 가져오기 : auto일 경우를 확인
        if not value_range:
            titleids = self.get_auto_episode_no(titleid, best_challenge, attempt=attempt)
        else:
            titleids = range(start, end + 1)

        # 한 타이틀 전체 추출
        subtitles = {}
        self.pbar = tqdm(list(titleids))
        for i in self.pbar:
            if best_challenge:
                a = requests.get(f'https://comic.naver.com/bestChallenge/detail?titleId={titleid}&no={i}')
            else:
                a = requests.get(f'https://comic.naver.com/webtoon/detail?titleId={titleid}&no={i}')
            # print(a.text)
            soup = bs(a.text, "html.parser")
            
            # 부제목 추출
            subtitle = soup.select('#subTitle_toolbar')
            # 부제목이 추출되지 않는다면 잘못된 id에 접근한 것이다. 그 이유는 해당 id에 해당하는 웹툰이 삭제되었거나
            # 그 id가 아직 생성되지 않은 것이다. 혹은 유료 미리보기 상태일 수도 있다.
            if not subtitle:
                print('It looks like this episode is truncated or last episode is latest episode. This episode won\'t be loaded.')
                print(f'Webtoon title: {title}, title ID: {titleid}, episode ID: {i}')
                self.pbar.set_description('wrong episode')
                continue
            subtitles[i] = subtitle[0].text

            # 이미지 리스트 추출
            # 이상하게 베도와 정식 웹툰은 웹툰이 보이는 위치가 다르다.
            if best_challenge:
                elements = soup.select('#comic_view_area > div > img')
            else:
                elements = soup.select('#sectionContWide > img')



            # 윈도우는 파일명 뒤에 .이 있으면 제거하고 파일을 생성한다. 따라서 .을 제거하는 re가 필요하다.(앞이나 중간은 상관없음)
            subtitle_dir = re.sub('[.]+$', '', subtitles[i].translate(self.table))
            # print(subtitle_dir)

            # 한 에피소드 다운로드
            episode_directory = f'{title_dir}/{i:04d}. {subtitle_dir}'.strip()
            # 디렉토리가 이미 있으면 다운로드를 스킵한다.
            try:
                os.mkdir(episode_directory)
            except FileExistsError:
                def integrity_recover():
                    self.pbar.set_description(f'integrity of {i} is not vaild. delete directory and continue action.')
                    # self.pbar.set_description(f'integrity of {i} is not vaild. delete directory and raise error.')
                    shutil.rmtree(episode_directory)
                    os.mkdir(episode_directory)
                    # raise AssertionError

                # print(f'skipping {i}')
                self.pbar.set_description(f'checking integrity of {i}')
                if not all([re.match(r"\d{3}[.](png|jpg|jpeg|bmp|gif)", file) for file in os.listdir(episode_directory)]):
                    integrity_recover()
                if not len(elements) == len(os.listdir(episode_directory)):
                    elements_revised = [element['src'] for element in elements if not ('agerate' in element['src'] or 'ctguide' in element['src'])]
                    if not len(elements_revised) == len(os.listdir(episode_directory)):
                        integrity_recover()
                    else:
                        self.pbar.set_description(f'skipping {i}')
                        continue
                else:
                    continue

            self.pbar.set_description('downloading')
            await self.download_one_episode(i, episode_directory, elements)

        # break
        print(f'A webtoon {title} download ended.')

    async def download_one_episode(self, epsodeno, episode_directory, elements):
        # 한 에피소드 내 이미지들 다운로드
        # 코루틴 리스트 생성
        images_coroutine = [self.download_single_image(episode_directory, element, elements.index(element)) for element in elements]
        await asyncio.gather(*images_coroutine)
  
    async def download_single_image(self, episode_directory, element, j):
        # 만약 imageno_re가 작동하지 않을 경우 age restriction이나 컷툰 안내인지 확인하고 맞으면 pass.
        try:
            # element를 src로 바꿈
            element = element['src']
            if 'agerate' in element or 'ctguide' in element:
                return

            # 이미지 확장자 불러옴
            # image_re = re.compile(r'[.](jpe?g|png)$', re.I)
            # image_extension = image_re.search(element).group(1)
            image_extension = element.split('.')[-1]

            file_name = f'{j:03d}.{image_extension}'
            # print(episode_directory, file_name, sep='|')
            self.pbar.set_description(episode_directory + '|' + file_name)
            get_request_with_user_agent = functools.partial(requests.get, element, headers=self.user_agent)
            image_raw = await self.loop.run_in_executor(None, get_request_with_user_agent)
            image_raw = image_raw.content
            with open(f'{episode_directory}/{file_name.translate(self.table)}', 'wb') as image:
                image.write(image_raw)
            # break
        except AttributeError as e: # re를 쓰던 시절의 잔재. re를 제거하면 이것도 제거하자.
            if 'age' in element or 'ctguide' in element:
                pass
            else:
                raise AttributeError(e)

    def get_auto_episode_no(self, titleid, best_challenge, attempt=10):
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

    def get_webtoon_thumbnail(self, webtoon_id, title, title_dir):
        request = requests.get(f'https://comic.naver.com/webtoon/list?titleId={webtoon_id}', headers=self.user_agent)
        soup = bs(request.text, "html.parser")
        image_url = soup.select_one('meta[property="og:image"]')['content']
        
        image_raw = requests.get(image_url, headers=self.user_agent).content
        with open(f'{title_dir}/{title}.jpg', 'wb') as image:
            image.write(image_raw)