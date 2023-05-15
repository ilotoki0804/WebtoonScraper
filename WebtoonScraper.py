import requests
from bs4 import BeautifulSoup as bs
import re
import os
import pickle
import re
import asyncio
import functools
import getsoup
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
                async def default_for_kwargs(value_range=None, titleid=0, best_challenge=self.determine_best_challenge(webtoon['titleid'])):
                    await self.download_one_webtoon(value_range=value_range, titleid=titleid, best_challenge=best_challenge)
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
        
    async def download_one_webtoon(self, value_range=None, titleid=766648, best_challenge=False):
        '''Check out doc of get_webtoons_async.'''
        if value_range:
            start, end = value_range
            if end == None:
                end = start
            
        # 제목 추출
        # 베도와 정식 웹툰을 나눴지만 titleid는 고유해 배도 링크에 정식 웹툰을 넣어도 상관은 없다.
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
            titleids = self.get_auto_episode_no(titleid, best_challenge)
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

# 폴더 다시 묶기
import os
import shutil
import re
from collections import defaultdict

class WebtoonFolderManagement:
    def __init__(self, alt_dir):
        self.BASE_DIR = r'webtoon'
        self.alt_dir = alt_dir
        self._make_directory(alt_dir)
        self.TEMP_DIR = 'temp'
        self._make_directory(self.TEMP_DIR)

    def _make_directory(self, directory, alert=True):
        try:
            os.makedirs(directory)
        except FileExistsError:
            if alert:
                print(f'Folder already exists. Overwrite the folder and continue. Folder name: {directory}')

    def divide_all_webtoons(self, episode_bundle, asking_every_time=False):
        webtoons = os.listdir(self.BASE_DIR)
        for webtoon in webtoons:
            alt_webtoon_dir = self.alt_dir + r'/' + webtoon
            base_webtoon_dir = self.BASE_DIR + r'/' + webtoon



            if asking_every_time:
                try:
                    episode_bundle = int(input(f'Please write down number for episode bundle. Recommend is 5. enter blank to skip.'))
                    if not episode_bundle:
                        continue
                except ValueError:
                    continue
                self._make_directory(alt_webtoon_dir)
                self._divide_webtoon(
                    base_webtoon_dir, alt_webtoon_dir, 
                    episode_bundle=episode_bundle
                )
            else:
                self._make_directory(alt_webtoon_dir)
                self._divide_webtoon(base_webtoon_dir, alt_webtoon_dir, episode_bundle=episode_bundle)
            os.rmdir(base_webtoon_dir)
            # break      

    def _move_thumbnail(self, base_webtoon_dir, alt_webtoon_dir):
        does_thumbnail_exist = False
        for episode_or_thumbnail in os.listdir(base_webtoon_dir):
            if re.match(r'.+[.](jpg|jpeg|png)$', episode_or_thumbnail, re.I):
                does_thumbnail_exist = True
                base_thumbnail_dir = f'{base_webtoon_dir}/{episode_or_thumbnail}'
                alt_thumbnail_dir2 = f'{self.TEMP_DIR}/{episode_or_thumbnail}'
                realt_thumbnail_dir = f'{alt_webtoon_dir}/{episode_or_thumbnail}'
                shutil.move(base_thumbnail_dir, alt_thumbnail_dir2)
                return does_thumbnail_exist, alt_thumbnail_dir2, realt_thumbnail_dir
        return False, None, None

    def _divide_webtoon(self, base_webtoon_dir, alt_webtoon_dir, episode_bundle, merge_last_bundle=True):
        self._make_directory(self.TEMP_DIR, alert=False)
        
        # Thumbnail 옮기기
        does_thumbnail_exist, alt_thumbnail_dir, realt_thumbnail_dir = self._move_thumbnail(base_webtoon_dir, alt_webtoon_dir)
        # print(self._move_thumbnail(base_webtoon_dir, alt_webtoon_dir))
        
        if not self._is_unified(base_webtoon_dir):
            self._unify_webtoon(base_webtoon_dir)

        if episode_bundle == 1:
            print('Episode bundle value is 1, so autometically revert directory state to original.')
            self.revert_to_original_download_state(base_webtoon_dir)
        episodes = os.listdir(base_webtoon_dir)
        if len(episodes) <= merge_last_bundle:
            merge_last_bundle = len(episodes)

        # 묶음으로 묶는 과정
        episode_bundle_name_collection = defaultdict(list)
        for episode in episodes:
            episode_no = int(episode.split('.')[0])
            episode_bundle_name_collection[(episode_no - 1)//episode_bundle].append(episode)
        if merge_last_bundle and len(episode_bundle_name_collection):
            episode_last_bundle = max(episode_bundle_name_collection.keys())
            last_bundle_value = episode_bundle_name_collection[episode_last_bundle]
            episode_ids = set()
            for image in last_bundle_value:
                episode_ids.add(image.split('.')[0])
            last_bundle_length = len(episode_ids)
            if last_bundle_length < episode_bundle:
                episode_list = list(episode_bundle_name_collection.keys())
                before_last_bundle = episode_list[episode_list.index(episode_last_bundle) - 1]
                # episode_bundle_name_collection[episode_last_bundle - 1].extend(last_bundle_value)
                episode_bundle_name_collection[before_last_bundle].extend(last_bundle_value)
                del episode_bundle_name_collection[episode_last_bundle]
        
        # 폴더에 넣는 과정
        temp_dir = fr'{self.TEMP_DIR}/temp'
        base_dir = fr'{base_webtoon_dir}'
        episode_bundle_name_collection = episode_bundle_name_collection.values()
        for episode_name_list in episode_bundle_name_collection:
            self._make_directory(temp_dir, alert=False)
            for image_name in episode_name_list:
                image_dir = fr'{base_dir}/{image_name}'
                shutil.move(image_dir, temp_dir)
            dir_name = self._make_dir_name(temp_dir)
            alt_dir = fr'{alt_webtoon_dir}/{dir_name}'
            self._make_directory(alt_dir)
            self._move_dir(temp_dir, alt_dir)

        # Thumbnail 다시 옮기기
        if does_thumbnail_exist:
            shutil.move(alt_thumbnail_dir, realt_thumbnail_dir)

        shutil.rmtree(self.TEMP_DIR)

    def _move_dir(self, base_episode_dir, alt_webtoon_dir, ignore_folders=False, rename=False, episode_name=None):
        images = os.listdir(base_episode_dir)
        if ignore_folders:
            images = (image for image in images if not re.match(r'^([.])*((?![.]).)+$', image)) # 디렉토리(확장자가 없는 경우, 맨 앞줄 '.'은 상관없음.)이면 제거
        for image in images:
            base_image_name = rf'{base_episode_dir}/{image}'
            # os.rename(base_image_name, alt_image_name)
            if rename:
                alt_image_name = rf'{alt_webtoon_dir}/{self._rename_image(image, episode_name)}'
            else:
                alt_image_name = rf'{alt_webtoon_dir}/{image}'
            shutil.move(base_image_name, alt_image_name)

    def _rename_image(self, image_name, episode_name):
        episode_split = re.search(r'^(\d+)[.] (.+)', episode_name)
        image_no, image_extension = image_name.split('.')[0], image_name.split('.')[-1]
        return f'{episode_split.group(1)}.{image_no}. {episode_split.group(2)}.{image_extension}'
    
    def _make_dir_name(self, base_webtoon_dir):
        episode_id = set([int(image.split('.')[0]) for image in os.listdir(base_webtoon_dir)])
        return f'{min(episode_id):04d}~{max(episode_id):04d}'

    def dividify_all_webtoon(self):
        webtoons = os.listdir(self.BASE_DIR)
        for webtoon in webtoons:
            print(webtoon)

            # 디렉토리 설정
            base_webtoon_dir = rf'{self.BASE_DIR}/{webtoon}'
            webtoon_episode_name = self._make_dir_name(base_webtoon_dir)
            alt_webtoon_dir = rf'{self.BASE_DIR}/{webtoon}/{webtoon_episode_name}'

            # 디렉토리 제작
            self._make_directory(alt_webtoon_dir)
            # self._make_directory(self.TEMP_FOLDER)

            # 옮길 웹툰 선정
            self._move_dir(base_webtoon_dir, alt_webtoon_dir, ignore_folders=True)

            break

    def _unify_webtoon(self, directory):
        episodes = os.listdir(directory)
        directory = directory[:-1] if directory[-1] == '/' or directory[-1] == '\\' else directory
        # child_dir = re.match(r'(.+)(?=\\|\/)(?=.+?$)', directory).group() # A/B/C가 주어지만 A/B를 호출하는 regex
        for episode in episodes:
            base_episode_dir = rf'{directory}/{episode}'
            self._move_dir(base_episode_dir, directory, rename=True, episode_name=episode)
            os.rmdir(base_episode_dir)
    
    def _is_unified(self, directory):
        episodes_or_images = os.listdir(directory)
        number_of_images = 0
        for episode_or_image in episodes_or_images:
            number_of_images += 1 if re.match(r'.+[.](jpg|jpeg|png)$', episode_or_image, re.I) else 0
        if number_of_images == 1 or number_of_images == 0:
            return False
        else:
            return True

    def revert_to_original_state(self, directory):
        # Thumbnail 옮기기
        does_thumbnail_exist, alt_thumbnail_dir, realt_thumbnail_dir = self._move_thumbnail(directory, directory)

        if not self._is_unified(directory):
            self._unify_webtoon(directory)
        
        images = os.listdir(directory)
        for image in images:
            image_nos = image.split('.')
            episode_no = image_nos[0]
            image_no = image_nos[1]
            episode_name = '.'.join(image_nos[2:-1])
            image_extension = image_nos[-1]
            episode_dir = f'{directory}/{episode_no}.{episode_name}'
            alt_image_name = f'{image_no}.{image_extension}'
            self._make_directory(episode_dir, alert=False)
            base_image_dir = f'{directory}/{image}'
            alt_image_dir = f'{episode_dir}/{alt_image_name}'
            shutil.move(base_image_dir, alt_image_dir)
        
        # Thumbnail 다시 옮기기
        if does_thumbnail_exist:
            shutil.move(alt_thumbnail_dir, realt_thumbnail_dir)
            os.removedirs(self.TEMP_DIR)