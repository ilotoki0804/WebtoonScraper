# 회차 묶기
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