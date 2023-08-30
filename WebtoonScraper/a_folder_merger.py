"""This module provides FolderMerger class."""

from __future__ import annotations
from http.client import NOT_IMPLEMENTED
import os
import shutil
import re
from collections import defaultdict
from pathlib import Path
import logging
from textwrap import indent
from typing_extensions import Literal, Final
from xmlrpc.client import NOT_WELLFORMED_ERROR

from sqlalchemy import literal

DEFAULT_STATE: Final = 'default_state'
MERGED: Final = 'merged'
UNIFIED: Final = 'unified'
NOT_MATCHED: Final = 'not_matched'

DIRECTORY_STATES = Literal['default_state', 'merged', 'unified', 'not_matched']

PathOrStr = str | Path


class FolderMerger:
    """웹툰 뷰어 앱에서 정주행하기 좋도록 회차들을 단위에 따라 묶습니다."""

    def __init__(self) -> None:
        self.base_dir = 'webtoon'
        self.target_dir = 'webtoon'

    @property
    def base_dir(self) -> Path:
        """웹툰이 저장되어 있는, 바꿀 웹툰이 있는 디렉토리입니다."""
        return self._base_dir

    @base_dir.setter
    def base_dir(self, base_dir) -> None:
        self._base_dir = Path(base_dir)

    @property
    def target_dir(self) -> Path:
        """다 마친 웹툰을 저장할 디렉토리입니다. `self.base_dir`와 같아도 상관 없습니다."""
        return self._target_dir

    @target_dir.setter
    def target_dir(self, target_dir) -> None:
        self._target_dir = Path(target_dir)

    ############### MAIN FUNCTIONALITY ###############

    def select_webtoon_and_merge(self, merge_amount: int) -> None:
        """
        Selects a webtoon from the base directory to merge.

        Args:
            merge_amount (int): The number of episodes to merge.

        Returns:
            None

        Raises:
            ValueError: If an invalid input is provided.
            IndexError: If an invalid index is provided.
        """
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

    def merge_webtoons_in_directory(self, merge_amount) -> None:
        """해당 디렉토리에 있는 모든 웹툰 디렉토리들을 합칩니다."""
        webtoons = os.listdir(self.base_dir)
        for webtoon in webtoons:
            webtoon_dir = self.target_dir / webtoon
            self.merge_webtoon_episodes(webtoon_dir, merge_amount)

    # def merge_webtoon_episodes_in_directory(
    #     self,
    #     merge_amount
    # ):
    #     ...

    def merge_webtoon_episodes(self,
                               webtoon_dir: Path,
                               merge_amount,
                               # merge_last_bundle=True
                               ) -> None:
        """웹툰을 합칩니다. 이때 같은 디렉토리를 변환합니다."""
        # base_dir와 alt_dir가 같은 경우를 대비해 이름을 달리함.
        temp_alt_webtoon_dir = Path(f'{webtoon_dir}(merged)')
        self._merge_webtoon_episodes(webtoon_dir, temp_alt_webtoon_dir, merge_amount=merge_amount, merge_last_bundle=True)
        os.rmdir(webtoon_dir)
        temp_alt_webtoon_dir.rename(webtoon_dir)

    def _merge_webtoon_episodes(self, base_webtoon_dir: Path, alt_webtoon_dir: Path, merge_amount: int, merge_last_bundle=True):
        """
        _merge_webtoon_episodes는 base_dir/alt_dir 두 가지 input을 받고 두 값이 같아서는 안 되지만,
        merge_webtoon_episodes는 한 웹툰의 merge 상태를 바꿔줍니다.
        만약 웹툰을 합친 결과를 기존 디렉토리에 그대로 반영하고 싶다면 merge_webtoon_episodes를 사용하고,
        다른 디렉토리로 분리하고 싶다면 _merge_webtoon_episodes를 사용하세요.

        Args:
            base_webtoon_dir (Path): _description_
            alt_webtoon_dir (Path): _description_
            merge_amount (int): _description_
            merge_last_bundle (bool, optional): _description_. Defaults to True.

        Raises:
            AssertionError: 만약 base_webtoon_dir와 alt_webtoon_dir가 같은 경우에 생깁니다. merge_webtoons_in_directory를 대신 이용하세요.
        """
        # base_webtoon_dir와 alt_webtoon_dir가 같으면 안됨!
        assert base_webtoon_dir != alt_webtoon_dir, 'base_webtoon_dir and alt_webtoon_dir cannot be same. Use merge_webtoon_episodes instead.'

        alt_webtoon_dir.mkdir(parents=True, exist_ok=True)

        # Thumbnail 옮기기 > alt_dir로 옮기는 것으로 변경
        self._move_thumbnail(base_webtoon_dir, alt_webtoon_dir)

        # 에피소드를 분해해 base_webtoon_dir에 형식에 맞추어 넣음
        if self.detailed_check_directory_state(base_webtoon_dir) == UNIFIED:
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
        if self.fast_check_directory_state(base_webtoon_dir) == UNIFIED:
            logging.debug('Webtoon look unified already, so _move_thumbnail is skipped.')
            return
        for episode_or_thumbnail in os.listdir(base_webtoon_dir):
            if re.match(r'.+[.](jpg|jpeg|png)$', episode_or_thumbnail, re.I):
                base_thumbnail_dir = base_webtoon_dir / episode_or_thumbnail
                alt_thumbnail_dir = alt_webtoon_dir / episode_or_thumbnail
                shutil.move(base_thumbnail_dir, alt_thumbnail_dir)
                return

    ############### SUB FUNCTIONALITY ###############

    def _make_dir_name(self, images) -> str:
        episode_id = self._find_episode_id(images)
        return f'{min(episode_id):04d}~{max(episode_id):04d}'

    @staticmethod
    def _find_episode_id(images) -> set[int]:
        # episode_id = set(int(image.split('.')[0]) for image in images)
        return {int(image.split('.')[0]) for image in images}

    def _transit_folder_insides(self, base_episode_dir: Path,
                                alt_webtoon_dir: Path,
                                episode_name: str | None = None,
                                ignore_folders: bool = False,
                                rename: bool = False
                                ) -> None:
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

    def _unify_webtoon(self, directory) -> None:
        episodes = os.listdir(directory)
        for episode in episodes:
            base_episode_dir = directory / episode
            self._transit_folder_insides(base_episode_dir, directory, episode, rename=True)
            os.rmdir(base_episode_dir)

    def _rename_image(self, image_name, episode_name) -> str:
        episode_split = re.search(r'^(\d+)[.] (.+)', episode_name)
        if not episode_split:
            if re.search(r'^(\d+)~(\d+)', episode_name):
                raise ValueError(
                    'Episode name is not valid. It\'s because you tried merging already merged webtoon folder.'
                )
            raise ValueError('Episode name is not valid.')
        image_no, image_extension = image_name.split('.')[0], image_name.split('.')[-1]
        return f'{episode_split[1]}.{image_no}. {episode_split[2]}.{image_extension}'

    def is_unified(self, directory: PathOrStr) -> bool:
        episodes_or_images: list[str] = os.listdir(directory)
        webtoon_is_merged = re.compile(r'.+[.](jpg|jpeg|png|webp|gif)$', re.I)
        # webtoon_is_merged = re.compile(r'^.+\..{3,4}$', re.I)
        number_of_images = sum(
            1 if webtoon_is_merged.match(episode_or_image) else 0
            for episode_or_image in episodes_or_images
        )
        return number_of_images not in {1, 0}

    def fast_check_directory_state(self, directory: PathOrStr) -> DIRECTORY_STATES:
        """
        detailed_check_directory_state는 사용자용으로, 정확한 오류 메시지와 체크를 목적으로 하지만,
        이 함수는 프로그램 내에서 assertion을 목적으로, 빠른 체크를 목적으로 합니다.
        주의: detailed_check_directory_state를 수정할 때는 fast_check_directory_state도 수정해야 합니다.
        """
        episodes_or_images: list[str] = os.listdir(directory)

        if len(episodes_or_images) <= 1:
            logging.warning(f"It looks like the directory is {'almost' if len(episodes_or_images) else ''} empty. "
                            "Check your directory again.")

        # 확장자를 직접 이용하지 않기 때문에 re.I가 필요 없다.
        webtoon_is_unified = re.compile(r'\d{4}[.]\d{3}[.].+[.][a-zA-Z]{3,4}$')
        webtoon_is_merged = re.compile(r'\d{4}~\d{4}')
        webtoon_is_default_state = re.compile(r'^\d{4}\. .+$')
        it_is_not_webtoon_rather_webtoons_folder = re.compile(r'^.+[(].+[)]([(]merged[)])?$')

        directory_states: list[DIRECTORY_STATES] = [UNIFIED, MERGED, DEFAULT_STATE]
        regexes_to_use = [webtoon_is_unified, webtoon_is_merged, webtoon_is_default_state, it_is_not_webtoon_rather_webtoons_folder]
        for state_name, regex in zip(directory_states, regexes_to_use):
            # 매치되지 '않은' 것의 개수를 세는 것을 주의!!!
            number_of_images_NOT_matched = sum(
                0 if regex.match(episode_or_image) else 1
                for episode_or_image in episodes_or_images
            )

            if number_of_images_NOT_matched <= 1:
                return state_name

        return NOT_MATCHED

    def detailed_check_directory_state(self, directory: PathOrStr) -> DIRECTORY_STATES:
        """
        디렉토리가 merge된 상태인지 기본 상태(default_state)인지, unified된 상태인지, 아니면 일치하는 게 없는지 확인합니다.
        사용자용으로, 상세한 경고 메시지와 정확한 체크를 제공합니다. 단, 중요한 프로그램을 처음 가동할 때는 사용할 수 있습니다.
        주의: fast_check_directory_state를 수정할 때는 detailed_check_directory_state도 수정해야 합니다.
        """
        episodes_or_images: list[str] = os.listdir(directory)

        # 확장자를 직접 이용하지 않기 때문에 re.I가 필요 없다.
        webtoon_is_unified = re.compile(r'\d{4}[.]\d{3}[.].+[.][a-zA-Z]{3,4}$')
        webtoon_is_merged = re.compile(r'\d{4}~\d{4}')
        webtoon_is_default_state = re.compile(r'^\d{4}\. .+$')
        it_is_not_webtoon_rather_webtoons_folder = re.compile(r'^.+[(].+[)]([(]merged[)])?$')

        # # less error-prone but lossely checking regexes
        # webtoon_is_unified = re.compile(r'\d+[.]\d+[.].+[.].{3,4}$')
        # webtoon_is_merged = re.compile(r'\d+~\d+')
        # webtoon_is_default_state = re.compile(r'^\d{4}\. .+$')  # unified와 구별하려면 space가 필수이다.

        # webtoon_is_unified와 webtoon_is_default_state가 동시에 True라면 unified로 결과를 출력하는 것이 맞다.
        # webtoon_is_unified가 더 엄격한 규칙을 가지고 있기 때문이다.
        # webtoon_is_merged는 워낙 특이해서 false positive의 확률이 거의 없다.

        directory_number_of_not_matched: list[int] = []
        directory_bool_states: list[bool] = []
        directory_state_names: list[DIRECTORY_STATES | Literal['webtoons_folder']] = []

        directory_states: list[DIRECTORY_STATES | Literal['webtoons_folder']] = [UNIFIED, MERGED, DEFAULT_STATE, 'webtoons_folder']
        regexes_to_use = [webtoon_is_unified, webtoon_is_merged, webtoon_is_default_state, it_is_not_webtoon_rather_webtoons_folder]
        for state_name, regex in zip(directory_states, regexes_to_use):
            # 매치되지 '않은' 것의 개수를 세는 것을 주의!!!
            number_of_images_NOT_matched = sum(
                0 if regex.match(episode_or_image) else 1
                for episode_or_image in episodes_or_images
            )

            directory_number_of_not_matched.append(number_of_images_NOT_matched)
            directory_bool_states.append(number_of_images_NOT_matched <= 1)
            directory_state_names.append(state_name)

        if directory_bool_states[directory_states.index('webtoons_folder')]:
            logging.warning('This directory is looks like a webtoons_folder. Check your folder again.')
            if sum(directory_bool_states) == 1:
                return NOT_MATCHED
        webtons_folder_index = directory_states.index('webtoons_folder')
        del (directory_number_of_not_matched[webtons_folder_index],
             directory_bool_states[webtons_folder_index],
             directory_state_names[webtons_folder_index])

        match sum(directory_bool_states):  # 3.10 이상만 실행 가능.
            case 0:
                logging.warning('This directory is nether unified, merged nor default_state. '
                                "Probably the directory is not a webtoon folder.")
                return NOT_MATCHED

            case 1:
                state_name = directory_state_names[directory_bool_states.index(True)]
                assert state_name != 'webtoons_folder'
                return state_name

            case 2:
                unmatched_directory_state_index = directory_bool_states.index(False)
                del (directory_number_of_not_matched[unmatched_directory_state_index],
                     directory_bool_states[unmatched_directory_state_index],
                     directory_state_names[unmatched_directory_state_index])
                logging.warning(f'This directory is either {directory_state_names[0]} and {directory_state_names[1]}. '
                                "Probably there's a conflict or ")

            case _:
                match len(episodes_or_images):
                    case 0:
                        logging.warning('This directory is either unified, merged, and default_state. '
                                        "It's because directory is empty.")
                    case 1:
                        logging.warning('This directory is either unified, merged, and default_state. '
                                        "It's because directory only contains a single file, like thumbnail or a webtoon folder.")
                    case _:
                        logging.warning('This directory is either unified, merged, and default_state. '
                                        "Maybe it's because directory is not a webtoon folder.")

                return NOT_MATCHED

        return NOT_MATCHED

    ############### RESTORE FUNCTIONALITY ###############

    def restore_webtoons_in_directory(self) -> None:
        webtoons = os.listdir(self.base_dir)
        for webtoon in webtoons:
            webtoon_dir = self.base_dir / webtoon
            self.restore_webtoon(webtoon_dir)

    def restore_webtoon(self, directory: Path) -> None:
        # Thumbnail 옮기기
        temp_thumbnail_path = directory / 'thumbnail-TEMP'
        temp_thumbnail_path.mkdir(parents=True)
        self._move_thumbnail(directory, temp_thumbnail_path)

        if self.detailed_check_directory_state(directory) == UNIFIED:
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
