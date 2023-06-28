# 회차 묶기
import os
import shutil
import re
from collections import defaultdict
from pathlib import Path
import logging


class FolderManager:
    def __init__(self):
        
        self.BASE_DIR = 'webtoon'
        self.ALT_DIR = 'webtoon'

    @property
    def BASE_DIR(self):
        return self._BASE_DIR

    @BASE_DIR.setter
    def BASE_DIR(self, BASE_DIR):
        self._BASE_DIR = Path(BASE_DIR)

    @property
    def ALT_DIR(self):
        return self._ALT_DIR

    @ALT_DIR.setter
    def ALT_DIR(self, ALT_DIR):
        self._ALT_DIR = Path(ALT_DIR)

    ############### MAIN FUNCTIONALITY ###############

    def merge_webtoons_in_directory(self, merge_amount):
        webtoons = os.listdir(self.BASE_DIR)
        for webtoon in webtoons:
            alt_webtoon_dir = self.ALT_DIR / webtoon
            # base_dir와 alt_dir가 같은 경우를 대비해 이름을 달리함.
            temp_alt_webtoon_dir = self.ALT_DIR / (webtoon + '(merged)') # why do I have to?
            base_webtoon_dir = self.BASE_DIR / webtoon
            self._merge_webtoon_episodes(base_webtoon_dir, temp_alt_webtoon_dir, merge_amount=merge_amount)
            shutil.rmtree(base_webtoon_dir)
            temp_alt_webtoon_dir.rename(alt_webtoon_dir)
            # break

    def merge_webtoon_episodes(self,
                               webtoon_dir: Path,
                               merge_amount,
                               merge_last_bundle=True):
        # base_dir와 alt_dir가 같은 경우를 대비해 이름을 달리함.
        # temp_alt_webtoon_dir = Path(str(webtoon_dir.parents)) / (webtoon_dir.name + '(merged)') # why do I have to?
        temp_alt_webtoon_dir = Path(str(webtoon_dir) + '(merged)')
        self._merge_webtoon_episodes(webtoon_dir, temp_alt_webtoon_dir, merge_amount=merge_amount, merge_last_bundle=merge_last_bundle)
        os.rmdir(webtoon_dir)
        temp_alt_webtoon_dir.rename(webtoon_dir)

    def _merge_webtoon_episodes(self, base_webtoon_dir: Path, alt_webtoon_dir: Path, merge_amount, merge_last_bundle=True):
        # base_webtoon_dir와 alt_webtoon_dir가 같으면 안됨!
        if base_webtoon_dir == alt_webtoon_dir:
            raise NotImplementedError('base_webtoon_dir and alt_webtoon_dir cannot be same.')
        
        alt_webtoon_dir.mkdir(parents=True, exist_ok=True)

        # Thumbnail 옮기기 > alt_dir로 옮기는 것으로 변경
        self._move_thumbnail(base_webtoon_dir, alt_webtoon_dir)
        
        # 에피소드를 분해해 base_webtoon_dir에 형식에 맞추어 넣음
        if not self._is_unified(base_webtoon_dir):
            self._unify_webtoon(base_webtoon_dir)

        # episode_bundle이 1인 경우 revert_to_original_download_state 수행
        if merge_amount == 1:
            print('Value of episode_bundle is 1, so autometically revert directory state to original.')
            self.restore_webtoon(base_webtoon_dir)
        episodes = os.listdir(base_webtoon_dir)

        # merge_last_bundle을 고려하지 않고 컬랙션을 제작함
        merged_images: list[list[str]] = defaultdict(list)
        for episode in episodes:
            episode_no = int(episode.split('.')[0])
            merged_images[(episode_no - 1)//merge_amount].append(episode)

        # merge_last_bundle을 적용함
        merged_images = list(merged_images.items())
        merged_images.sort()
        _, last_images = merged_images[-1]
        if merge_last_bundle and len(self._find_episode_id(last_images)) != merge_amount:
            merged_second_last_list = merged_images[-2][1]
            merged_second_last_list += merged_images.pop()[1]

        # 폴더에 넣는 과정
        for _, images in merged_images:
            alt_dir_name = self._make_dir_name(images)
            images_dir = alt_webtoon_dir / alt_dir_name
            images_dir.mkdir(parents=True, exist_ok=True)
            for image in images:
                image_dir = base_webtoon_dir / image
                shutil.move(image_dir, images_dir)

    def _move_thumbnail(self, base_webtoon_dir, alt_webtoon_dir):
        if self._is_unified(base_webtoon_dir):
            logging.debug('Webtoon look unified already, so _move_thumbnail is skipped.')
            return
        for episode_or_thumbnail in os.listdir(base_webtoon_dir):
            if re.match(r'.+[.](jpg|jpeg|png)$', episode_or_thumbnail, re.I):
                base_thumbnail_dir = base_webtoon_dir / episode_or_thumbnail
                alt_thumbnail_dir = alt_webtoon_dir / episode_or_thumbnail
                shutil.move(base_thumbnail_dir, alt_thumbnail_dir)
                return
            
    ############### SUB FUNCTIONALITY ###############

    def _make_dir_name(self, images):
        episode_id = self._find_episode_id(images)
        # episode_id = set(int(image.split('.')[0]) for image in images)
        return f'{min(episode_id):04d}~{max(episode_id):04d}'
    
    @staticmethod
    def _find_episode_id(images):
        episode_id = set(int(image.split('.')[0]) for image in images)
        return episode_id
    
    def _move_images(self, base_episode_dir: Path, alt_webtoon_dir: Path,
                     episode_name: str|None=None, ignore_folders: bool=False, rename: bool=False):
        """이미지가 들어있는 폴더를 받아서 rename하거나 하지 않고 alt_webtoon_dir로 보내는 함수

        Args:
            base_episode_dir (Path): 이미지가 들어있는 폴더
            alt_webtoon_dir (Path): 이미지를 보낼 폴더
            episode_name (str): 만약 rename을 할 경우, 이름을 정하기 위한 에피소드 이름.
            ignore_folders (bool, optional): 폴더를 무시할 지 여부. Defaults to False.
            rename (bool, optional): 이름을 바꿀 것인지 여부. Defaults to False.
        """
        images = os.listdir(base_episode_dir)
        if ignore_folders:
            # 디렉토리(확장자가 없는 경우, 맨 앞줄 '.'은 상관없음.)이면 제거
            images = (image for image in images if not re.match(r'^([.])*((?![.]).)+$', image))
        for image in images:
            base_image_name = base_episode_dir / image
            # os.rename(base_image_name, alt_image_name)
            if rename:
                alt_image_name = alt_webtoon_dir / self._rename_image(image, episode_name)
            else:
                alt_image_name = alt_webtoon_dir / image
            shutil.move(base_image_name, alt_image_name)

    def _unify_webtoon(self, directory):
        episodes = os.listdir(directory)
        for episode in episodes:
            base_episode_dir = directory / episode
            self._move_images(base_episode_dir, directory, episode, rename=True)
            os.rmdir(base_episode_dir)

    def _rename_image(self, image_name, episode_name):
        episode_split = re.search(r'^(\d+)[.] (.+)', episode_name)
        image_no, image_extension = image_name.split('.')[0], image_name.split('.')[-1]
        return f'{episode_split.group(1)}.{image_no}. {episode_split.group(2)}.{image_extension}'
    
    def _is_unified(self, directory):
        episodes_or_images = os.listdir(directory)
        number_of_images = 0
        for episode_or_image in episodes_or_images:
            number_of_images += 1 if re.match(r'.+[.](jpg|jpeg|png)$',
                                              episode_or_image, re.I) else 0
        if number_of_images == 1 or number_of_images == 0:
            return False
        else:
            return True
    
    ############### RESTORE FUNCTIONALITY ###############

    def restore_webtoons_in_directory(self):
        webtoons = os.listdir(self.BASE_DIR)
        for webtoon in webtoons:
            webtoon_dir = self.BASE_DIR / webtoon
            self.restore_webtoon(webtoon_dir)

    def restore_webtoon(self, directory: Path):
        # Thumbnail 옮기기
        temp_thumbnail_path = directory / 'thumbnail-TEMP'
        temp_thumbnail_path.mkdir(parents=True)
        self._move_thumbnail(directory, temp_thumbnail_path)
        
        if not self._is_unified(directory):
            # self._unify_webtoon(directory)
            directories = os.listdir(directory)
            directories = (directory_ for directory_ in directories
                           if not directory_ == 'thumbnail-TEMP')
            
            for directory_ in directories:
                directory_ = directory / directory_
                self._move_images(directory_, directory)
                directory_.rmdir()

        images = os.listdir(directory)
        images = (image for image in images if not image == 'thumbnail-TEMP')

        for image in images:
            image_info = re.match(r'(\d+)\.(\d+)\. (.+?)\.(\w.+)', image)
            episode_no, image_no = image_info.group(1), image_info.group(2)
            episode_name, image_extension = image_info.group(3), image_info.group(4)

            episode_dir = directory / f'{episode_no}. {episode_name}'
            alt_image_name = f'{image_no}.{image_extension}'
            episode_dir.mkdir(parents=True, exist_ok=True)
            base_image_path = directory / image
            alt_image_path = episode_dir / alt_image_name
            shutil.move(base_image_path, alt_image_path)

        self._move_thumbnail(temp_thumbnail_path, directory)
        temp_thumbnail_path.rmdir()

if __name__ == "__main__":
    print(os.curdir)
    fm = FolderManager()
    # fm.BASE_DIR = './(699830)'
    # fm.BASE_DIR = 'webtoon/(699830)'
    # fm.BASE_DIR = 'webtoon'
    # fm.ALT_DIR = './going_on'
    # fm.ALT_DIR = 'webtoon/going_on'
    # fm.ALT_DIR = 'webtoon'
    # print(fm.BASE_DIR, repr(fm.ALT_DIR))
    # print(fm._BASE_DIR, repr(fm._ALT_DIR))
    # fm.merge_webtoon_episodes(fm.ALT_DIR, fm.BASE_DIR, 5)
    # fm.merge_webtoon_episodes(fm.BASE_DIR, fm.ALT_DIR, 5)
    # fm.restore_webtoon(fm.ALT_DIR)

    # fm.merge_webtoons_in_directory(10)
    # fm.restore_webtoons_in_directory()
    # fm.merge_webtoon_episodes(Path('webtoon/(699830)'), 5)
