"""This module provides FolderMerger class."""

from __future__ import annotations
import os
import shutil
import re
from collections import defaultdict
from pathlib import Path
import logging

class FolderMerger:
    """웹툰 뷰어 앱에서 정주행하기 좋도록 회차들을 단위에 따라 묶습니다."""
    def __init__(self):
        self.base_dir = 'webtoon'
        self.target_dir = 'webtoon'

    @property
    def base_dir(self):
        """웹툰이 저장되어 있는, 바꿀 웹툰이 있는 디렉토리입니다."""
        return self._base_dir

    @base_dir.setter
    def base_dir(self, base_dir):
        self._base_dir = Path(base_dir)

    @property
    def target_dir(self):
        """다 마친 웹툰을 저장할 디렉토리입니다. `self.base_dir`와 같아도 상관 없습니다."""
        return self._targe_dir

    @target_dir.setter
    def target_dir(self, targe_dir):
        self._targe_dir = Path(targe_dir)

    ############### MAIN FUNCTIONALITY ###############

    def select_webtoon_wanted_to_merge(self, merge_amount: int):
        webtoons = os.listdir(self.base_dir)
        print('Select webtoon to merge.')
        for i, webtoon in enumerate(webtoons, 1):
            print(f'{i:02d}. {webtoon}')

        try:
            user_answer = int(input('Enter the number of webtoon you want to merge: '))
        except ValueError as e:
            try:
                e.add_note('Invalid input.')
                raise
            except AttributeError:  # for under Python 3.11
                raise ValueError('Invalid input.') from e

        try:
            selected_webtoon_dir_name = webtoons[user_answer - 1]
        except IndexError as e:
            try:
                e.add_note('Invalid index.')
                raise
            except AttributeError:  # for under Python 3.11
                raise IndexError('Invalid index.') from e

        print(f'You selected {selected_webtoon_dir_name}. Merging webtoon has started.')
        self.merge_webtoon_episodes(self.base_dir / selected_webtoon_dir_name, merge_amount)
        print('Merging webtoon has ended.')

    def merge_webtoons_in_directory(self, merge_amount):
        webtoons = os.listdir(self.base_dir)
        for webtoon in webtoons:
            webtoon_dir = self.target_dir / webtoon
            self.merge_webtoon_episodes(webtoon_dir, merge_amount)

    def merge_webtoon_episodes(self,
                               webtoon_dir: Path,
                               merge_amount,
                               # merge_last_bundle=True
                               ):
        """
        _merge_webtoon_episodes는 base_dir/alt_dir 두 가지 input을 받고 두 값이 같아서는 안 되지만,
        merge_webtoon_episodes는 한 가지 input만 받고 한 폴더 내의 상태를 바꿔준다.
        """
        # base_dir와 alt_dir가 같은 경우를 대비해 이름을 달리함.
        temp_alt_webtoon_dir = Path(f'{webtoon_dir}(merged)')
        self._merge_webtoon_episodes(webtoon_dir, temp_alt_webtoon_dir, merge_amount=merge_amount, merge_last_bundle=True)
        os.rmdir(webtoon_dir)
        temp_alt_webtoon_dir.rename(webtoon_dir)

    def _merge_webtoon_episodes(self, base_webtoon_dir: Path, alt_webtoon_dir: Path, merge_amount, merge_last_bundle=True):
        # base_webtoon_dir와 alt_webtoon_dir가 같으면 안됨!
        if base_webtoon_dir == alt_webtoon_dir:
            raise NotImplementedError('base_webtoon_dir and alt_webtoon_dir cannot be same. Use merge_webtoon_episodes instead.')

        alt_webtoon_dir.mkdir(parents=True, exist_ok=True)

        # Thumbnail 옮기기 > alt_dir로 옮기는 것으로 변경
        self._move_thumbnail(base_webtoon_dir, alt_webtoon_dir)

        # 에피소드를 분해해 base_webtoon_dir에 형식에 맞추어 넣음
        if not self._is_unified(base_webtoon_dir):
            self._unify_webtoon(base_webtoon_dir)

        # episode_bundle이 1인 경우 revert_to_original_download_state 수행
        if merge_amount == 1:
            logging.warning('Value of episode_bundle is 1, so autometically revert directory state to original.')
            self.restore_webtoon(base_webtoon_dir)
        episodes = os.listdir(base_webtoon_dir)

        # merge_last_bundle을 고려하지 않고 컬랙션을 제작함
        merged_images = defaultdict(list)
        for episode in episodes:
            episode_no = int(episode.split('.')[0])
            merged_images[(episode_no - 1) // merge_amount].append(episode)

        # merge_last_bundle을 적용함
        merged_images_list: list[tuple[int, list[str]]] = sorted(merged_images.items())
        _, last_images = merged_images_list[-1]
        if merge_last_bundle and len(self._find_episode_id(last_images)) > merge_amount:
            merged_second_last_list = merged_images_list[-2][1]
            merged_second_last_list += merged_images_list.pop()[1]

        # 폴더에 넣는 과정
        for _, images in merged_images_list:
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
        return f'{min(episode_id):04d}~{max(episode_id):04d}'

    @staticmethod
    def _find_episode_id(images):
        # episode_id = set(int(image.split('.')[0]) for image in images)
        return {int(image.split('.')[0]) for image in images}

    def _transit_folder_insides(self, base_episode_dir: Path,
                                alt_webtoon_dir: Path,
                                episode_name: str | None = None,
                                ignore_folders: bool = False,
                                rename: bool = False
                                ):
        """base와 alt 두 종류의 폴더를 받아 base 안의 내용물을 alt로 보내는 함수

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
            if rename:
                alt_image_name = alt_webtoon_dir / self._rename_image(image, episode_name)
            else:
                alt_image_name = alt_webtoon_dir / image
            shutil.move(base_image_name, alt_image_name)

    def _unify_webtoon(self, directory):
        episodes = os.listdir(directory)
        for episode in episodes:
            base_episode_dir = directory / episode
            self._transit_folder_insides(base_episode_dir, directory, episode, rename=True)
            os.rmdir(base_episode_dir)

    def _rename_image(self, image_name, episode_name):
        episode_split = re.search(r'^(\d+)[.] (.+)', episode_name)
        if not episode_split:
            if re.search(r'^(\d+)~(\d+)', episode_name):
                raise ValueError(
                    'Episode name is not valid. It\'s because you tried merging already merged webtoon folder.'
                )
            raise ValueError('Episode name is not valid.')
        image_no, image_extension = image_name.split('.')[0], image_name.split('.')[-1]
        return f'{episode_split[1]}.{image_no}. {episode_split[2]}.{image_extension}'

    def _is_unified(self, directory):
        episodes_or_images = os.listdir(directory)
        number_of_images = sum(
            1 if re.match(r'.+[.](jpg|jpeg|png)$', episode_or_image, re.I) else 0
            for episode_or_image in episodes_or_images
        )
        return number_of_images not in [1, 0]

    ############### RESTORE FUNCTIONALITY ###############

    def restore_webtoons_in_directory(self):
        webtoons = os.listdir(self.base_dir)
        for webtoon in webtoons:
            webtoon_dir = self.base_dir / webtoon
            self.restore_webtoon(webtoon_dir)

    def restore_webtoon(self, directory: Path):
        # Thumbnail 옮기기
        temp_thumbnail_path = directory / 'thumbnail-TEMP'
        temp_thumbnail_path.mkdir(parents=True)
        self._move_thumbnail(directory, temp_thumbnail_path)

        if not self._is_unified(directory):
            # self._unify_webtoon(directory)
            directories = os.listdir(directory)
            directories = (
                directory_
                for directory_ in directories
                if directory_ != 'thumbnail-TEMP'
            )

            for directory_ in directories:
                directory_ = directory / directory_
                self._transit_folder_insides(directory_, directory)
                directory_.rmdir()

        images = os.listdir(directory)
        images = (image for image in images if image != 'thumbnail-TEMP')

        for image in images:
            image_info = re.match(r'(\d+)\.(\d+)\. (.+?)\.(\w.+)', image)
            if not image_info:
                raise ValueError('image name is not valid. Possibly trying not merged webtoon folder.')
            episode_no, image_no = image_info[1], image_info[2]
            episode_name, image_extension = image_info[3], image_info[4]

            episode_dir = directory / f'{episode_no}. {episode_name}'
            alt_image_name = f'{image_no}.{image_extension}'
            episode_dir.mkdir(parents=True, exist_ok=True)
            base_image_path = directory / image
            alt_image_path = episode_dir / alt_image_name
            shutil.move(base_image_path, alt_image_path)

        self._move_thumbnail(temp_thumbnail_path, directory)
        temp_thumbnail_path.rmdir()
