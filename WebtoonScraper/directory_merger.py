"""This module provides FolderMerger class."""
# re.match로 변경하기
from __future__ import annotations
import os
import shutil
import re
from collections import defaultdict
from pathlib import Path
import logging
from typing import Sequence

from typing_extensions import Literal, Final, NamedTuple

from matplotlib.widgets import EllipseSelector

if __name__ in {'__main__', 'a_folder_merger'}:
    from exceptions import DirectoryStateUnmatched
else:
    from .exceptions import DirectoryStateUnmatched

DEFAULT_STATE: Final = 'default_state'
MERGED: Final = 'merged'
UNIFIED: Final = 'unified'
NOT_MATCHED: Final = 'not_matched'
WEBTOONS_DIRECTORY: Final = 'webtoons_directory'

DIRECTORY_STATES = Literal['default_state', 'merged', 'unified', 'not_matched', 'webtoons_directory']

PathOrStr = str | Path


class WebtoonRegexes(NamedTuple):
    unified_image: re.Pattern
    merged_dir: re.Pattern
    default_episode_name_dir: re.Pattern
    webtoon_dir: re.Pattern
    normal_image: re.Pattern


# WebtoonRegexes = namedtuple('webtoon_regexes',
#                             ['unified_image', 'merged_dir', 'default_episode_name_dir', 'webtoon_dir', 'normal_image'])
webtoon_regexes = WebtoonRegexes(
    unified_image=re.compile(r'(?P<episode_no>^\d{4})[.](?P<image_no>\d{3})[.] (?P<episode_name>.+)[.](?P<extension>[a-zA-Z]{3,4})$'),  # 0001.001. 에피소드 이름.jpg
    merged_dir=re.compile(r'^(?P<from>\d{4})~(?P<to>\d{4})$'),  # 0001~0005
    default_episode_name_dir=re.compile(r'^(?P<no>\d{4})\. (?P<episode_name>.+)$'),  # 0001. 에피소드 이름
    webtoon_dir=re.compile(r'^(?P<webtoon_name>.+)[(](?P<id>.+?)[)][(]merged[)]$'),  # 웹툰 이름(id)[(merged)]
    normal_image=re.compile(r'^(?P<image_no>\d{3})[.](?P<extension>[a-zA-Z]{3,4})$'),  # 023.jpg
)

state_and_regexes: dict[DIRECTORY_STATES, re.Pattern[str]] = {
    UNIFIED: webtoon_regexes.unified_image,
    MERGED: webtoon_regexes.merged_dir,
    DEFAULT_STATE: webtoon_regexes.default_episode_name_dir,
    WEBTOONS_DIRECTORY: webtoon_regexes.webtoon_dir,
}

# webtoon_is_unified와 webtoon_is_default_state가 동시에 True라면 unified로 결과를 출력하는 것이 맞다.
# webtoon_is_unified가 더 엄격한 규칙을 가지고 있기 때문이다.
# webtoon_is_merged는 워낙 특이해서 false positive의 확률이 거의 없다.

# webtoon_regexes = WebtoonRegexes(  # 사용을 하게 될 경우 위처럼 그룹을 추가할 것! 그렇지 않으면 작동하지 않음.
#     unified_image=re.compile(r'\d+[.]\d+[.].+[.].{3,4}$'),
#     merged_dir=re.compile(r'\d+~\d+'),
#     default_episode_name_dir=re.compile(r'^\d{4}\. .+$'),  # unified와 구별하려면 space가 필수이다.
#     webtoon_dir=re.compile(r'^.+[(].+[)]([(]merged[)])?$'),
#     normal_image=re.compile(r'^.+[.](jpg|jpeg|png|webp|gif|bmp)$', re.I),
# )

ImageFileName = str


class FolderMerger:
    """웹툰 뷰어 앱에서 정주행하기 좋도록 회차들을 단위에 따라 묶습니다."""

    def __init__(self) -> None:
        self.source_dir = 'webtoon'
        self.target_dir = 'webtoon'

    @property
    def source_dir(self) -> Path:
        """웹툰이 저장되어 있는, 바꿀 웹툰이 있는 디렉토리입니다."""
        return self._base_dir

    @source_dir.setter
    def source_dir(self, source_dir: PathOrStr) -> None:
        self._base_dir = Path(source_dir)

    @property
    def target_dir(self) -> Path:
        """다 마친 웹툰을 저장할 디렉토리입니다. `self.base_dir`와 같아도 상관 없습니다."""
        return self._target_dir

    @target_dir.setter
    def target_dir(self, target_dir: PathOrStr) -> None:
        self._target_dir = Path(target_dir)

    ############### MAIN FUNCTIONALITY ###############

    def select_webtoon_and_merge(self, merge_amount: int) -> None:
        """소스 디렉토리에 있는 웹툰 디렉토리 중 사용자가 선택한 웹툰을 합칩니다."""
        webtoons = os.listdir(self.source_dir)

        print('Select webtoon to merge.')
        if len(webtoons) < 10:
            for i, webtoon in enumerate(webtoons, 1):
                print(f'{i}. {webtoon}')
        else:
            for i, webtoon in enumerate(webtoons, 1):
                print(f'{i:02d}. {webtoon}')

        try:
            user_answer = int(input('Enter number: '))
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
        self.merge_webtoon(self.source_dir / selected_webtoon_dir_name, merge_amount)
        print('Merging webtoon has ended.')

    def merge_webtoons_from_source_dir(self, merge_amount: int) -> None:
        """소스 디렉토리에 있는 모든 웹툰 디렉토리들을 합칩니다."""
        webtoons = os.listdir(self.source_dir)
        for webtoon in webtoons:
            webtoon_dir = self.target_dir / webtoon
            self.merge_webtoon(webtoon_dir, merge_amount)

    def merge_webtoon(
        self,
        webtoon_dir: Path,
        merge_amount: int,  # merge_amount는 필수이다. None이 될 수 없다.
    ) -> None:
        """
        merge_webtoon_dir_to_dir는 base_dir/alt_dir 두 가지 input을 받고 두 값이 같아서는 안 되지만,
        merge_webtoon는 한 웹툰의 merge 상태를 바꿔줍니다.
        webtoon_dir에 있는 웹툰을 합칩니다. 합쳐진 내용물을 기존 웹툰 디렉토리에 저장됩니다.
        """
        # base_dir와 alt_dir가 같은 경우를 대비해 이름을 달리함.
        temp_target_webtoon_dir = Path(f'{webtoon_dir}(merged)')
        self.merge_webtoon_dir_to_dir(webtoon_dir, temp_target_webtoon_dir, merge_amount)
        temp_target_webtoon_dir.rename(webtoon_dir)

    def merge_webtoon_dir_to_dir(
        self,
        source_webtoon_dir: Path,
        target_webtoon_dir: Path,
        merge_amount: int,
        merge_last_bundle=True
    ) -> None:
        """
        만약 웹툰을 합친 결과를 기존 디렉토리에 그대로 반영하고 싶다면 merge_webtoon_episodes를 사용하고,
        다른 디렉토리로 분리하고 싶다면 _merge_webtoon_episodes를 사용하세요.
        """
        # base_webtoon_dir와 alt_webtoon_dir가 같으면 코드가 망가짐.
        if source_webtoon_dir == target_webtoon_dir:
            raise NotImplementedError('base_webtoon_dir and alt_webtoon_dir cannot be same. Use merge_webtoon_episodes instead.')

        dir_state = self.fast_check_directory_state(source_webtoon_dir)
        if dir_state == MERGED and merge_amount == 1:
            logging.warning('Value of episode_bundle is 1, so autometically revert directory state to original.')
            self.restore_webtoon(source_webtoon_dir)
            return
        if dir_state in {MERGED, NOT_MATCHED, WEBTOONS_DIRECTORY}:
            raise DirectoryStateUnmatched(f'State of directory is {dir_state}, which cannot be merged.\n'
                                          f'sorce webtoon directory: {source_webtoon_dir}')

        # exist_ok=True는 옮기다 중간에 interrupt를 받아 끊긴 뒤 나중에 다시 재개할 때 도움이 된다.
        target_webtoon_dir.mkdir(parents=True, exist_ok=True)

        self.move_thumbnail_only(source_webtoon_dir, target_webtoon_dir)

        if dir_state == DEFAULT_STATE:
            self.all_images_to_one_source_dir_with_rename(source_webtoon_dir)
        elif dir_state == UNIFIED:
            logging.info('Directory seems already unified, so skipping unifing.')

        episodes = os.listdir(source_webtoon_dir)

        # merge_last_bundle을 고려하지 않고 컬랙션을 제작함
        merged_images = defaultdict(list)
        for episode in episodes:
            episode_no = int(episode.split('.')[0])
            merged_images[(episode_no - 1) // merge_amount].append(episode)

        # merge_last_bundle을 적용함
        merged_images_list: list[tuple[int, list[ImageFileName]]] = sorted(merged_images.items())
        _, last_images = merged_images_list[-1]
        if merge_last_bundle and len(self.find_episode_ids_of_unified_images(last_images)) > merge_amount:
            merged_second_last_list = merged_images_list[-2][1]
            merged_second_last_list += merged_images_list.pop()[1]

        # 폴더에 넣는 과정
        for _, images in merged_images_list:
            alt_dir_name = self.make_merged_directory_name(images)
            images_dir = target_webtoon_dir / alt_dir_name
            images_dir.mkdir(parents=True, exist_ok=True)
            for image in images:
                image_dir = source_webtoon_dir / image
                shutil.move(image_dir, images_dir)

        # 텅 빈 소스 디렉토리를 제거함
        os.rmdir(source_webtoon_dir)

    def move_thumbnail_only(self, source_webtoon_dir: Path, target_webtoon_dir: Path) -> None:
        for episode_or_thumbnail in os.listdir(source_webtoon_dir):
            if self.check_filename_state(episode_or_thumbnail) is NOT_MATCHED:
                base_thumbnail_dir = source_webtoon_dir / episode_or_thumbnail
                alt_thumbnail_dir = target_webtoon_dir / episode_or_thumbnail
                shutil.move(base_thumbnail_dir, alt_thumbnail_dir)
                return

    def all_images_to_one_source_dir_with_rename(self, source_dir, rename=True) -> None:
        """모든 하위 디렉토리에 있는 이미지를 (rename이 True라면) 이름 변경과 함께 모두 소스 디렉토리로 옮깁니다. Unifing이라고도 부릅니다."""
        episodes = os.listdir(source_dir)
        for episode in episodes:
            sub_episode_dir = source_dir / episode
            self.move_folder_contents(sub_episode_dir, source_dir, episode, rename=rename)
            os.rmdir(sub_episode_dir)

    def move_folder_contents(
        self,
        source_dir: Path,
        target_dir: Path,
        episode_name: str | None = None,
        rename: bool = False,
    ) -> None:
        """soure_dir 안의 내용물을 target_dir로 보내는 함수. 이때 rename이 True면 이름을 unifing에 알맞게 변경한다.

        Args:
            base_episode_dir (Path): 이미지가 들어있는 폴더
            alt_webtoon_dir (Path): 이미지를 보낼 폴더
            episode_name (str): 만약 rename을 할 경우, 이름을 정하기 위한 에피소드 이름.
            rename (bool, optional): 이름을 바꿀 것인지 여부. Defaults to False.
        """
        images = os.listdir(source_dir)

        for image in images:
            source_image_path = source_dir / image
            target_image_path = target_dir / (
                self.get_merged_image_name(image, episode_name) if rename else image)
            shutil.move(source_image_path, target_image_path)

    def get_merged_image_name(self, image_name, episode_name) -> str:
        image_name_processed: re.Match[str] | None = webtoon_regexes.normal_image.search(image_name)
        episode_name_processed: re.Match[str] | None = webtoon_regexes.default_episode_name_dir.search(episode_name)
        if not episode_name_processed:
            if webtoon_regexes.merged_dir.search(episode_name):
                raise ValueError(
                    "Episode name is not valid. It's because you tried to merge already merged webtoon directory.")
            raise ValueError(f'Episode name is not valid. Episode name: {episode_name}')
        if not image_name_processed:
            raise ValueError(f'Image name is not vaild. Image name: {image_name}, regex: {webtoon_regexes.normal_image}')

        image_no = image_name_processed.group('image_no')
        image_extension = image_name_processed.group('extension')
        episode_no = episode_name_processed.group('no')
        episode_name = episode_name_processed.group('episode_name')

        return f'{episode_no}.{image_no}. {episode_name}.{image_extension}'

    def find_episode_ids_of_unified_images(self, image_names: list[ImageFileName]) -> set[int]:
        # episode_id = set(int(image.split('.')[0]) for image in images)
        # return {int(image.split('.')[0]) for image in images}
        # return {int(webtoon_regexes.unified_image.search(image).group('episode_no')) for image in image_names}
        unique_ids: set[int] = set()
        for image in image_names:
            result = webtoon_regexes.unified_image.search(image)
            if result is None:
                dir_state = self.check_filename_state(image)
                raise DirectoryStateUnmatched(
                    f'State of directory is {dir_state}, which cannot be merged.\nProblematic image name: {image}')
            unique_ids.add(int(result.group('episode_no')))
        return unique_ids

    def make_merged_directory_name(self, image_names: list[ImageFileName]) -> str:
        episode_id = self.find_episode_ids_of_unified_images(image_names)
        return f'{min(episode_id):04d}~{max(episode_id):04d}'

    ############### CHECKING FUNCTIONALITY ###############

    def check_filename_state(self, file_or_directory_name: str) -> DIRECTORY_STATES:
        # sourcery skip: use-next, for simplicity and extensibility, decide not to use 'use-next'
        for state_name, regex in state_and_regexes.items():
            if regex.search(file_or_directory_name):
                return state_name
        return NOT_MATCHED

    def fast_check_directory_state(self, directory: PathOrStr) -> DIRECTORY_STATES:
        """
        detailed_check_directory_state는 사용자용으로, 정확한 오류 메시지와 체크를 목적으로 하지만,
        이 함수는 프로그램 내에서 assertion을 목적으로, 빠른 체크를 목적으로 합니다.
        따라서 episodes_or_images의 길이가 0이나 1일 때를 제외하고는 warning을 제공하지 않습니다.
        주의: detailed_check_directory_state를 수정할 때는 fast_check_directory_state도 수정해야 합니다.
        """
        episodes_or_images: list[str] = os.listdir(directory)
        # if 'thumbnail-TEMP' in episodes_or_images:
        #     # thumbnail-TEMP 관련 문제 해결
        #     logging.warning('thumbnail-TEMP directory detected. '
        #                     "It'll be ignored when directory is analized.")
        #     episodes_or_images.remove('thumbnail-TEMP')

        # not episodes_or_images는 일관성을 떨어뜨리기 때문에 사용하지 않는다.
        if len(episodes_or_images) == 0:  # sourcery skip
            logging.warning("It looks like the directory is empty. It cannot be something")
            return NOT_MATCHED

        if len(episodes_or_images) == 1:
            # 1개일 경우 썸네일 스킵 기능으로 인해 fast_check_directory_state가 제대로 동작하지 않는데,
            # 이때 check_filename_state를 사용하면 정확한 결과를 얻을 수 있다.
            return self.check_filename_state(episodes_or_images[0])

        for state_name, regex in state_and_regexes.items():
            # 매치되지 '않은' 것의 개수를 세는 것을 주의!!!
            number_of_images_NOT_matched = sum(
                0 if regex.match(episode_or_image) else 1
                for episode_or_image in episodes_or_images
            )

            logging.debug(number_of_images_NOT_matched)
            # 썸네일은 일반적으로 매치되지 않기 때문에 1의 여지를 둔다.
            if number_of_images_NOT_matched <= 1:
                return state_name

        return NOT_MATCHED

    def detailed_check_directory_state(self, directory: PathOrStr) -> DIRECTORY_STATES:
        """
        디렉토리가 merge된 상태인지 기본 상태(default_state)인지, unified된 상태인지, 아니면 일치하는 게 없는지 확인합니다.
        사용자용으로, 상세한 경고 메시지와 정확한 체크를 제공합니다.
        일반적으로는 fast_check_directory_state만으로도 충분하며, 따라서 프로그램 내에서는 fast만 사용합니다.
        주의: fast_check_directory_state를 수정할 때는 detailed_check_directory_state도 수정해야 합니다.
        """
        episodes_or_images: list[str] = os.listdir(directory)
        # if 'thumbnail-TEMP' in episodes_or_images:
        #     # thumbnail-TEMP 관련 문제 해결
        #     logging.warning('thumbnail-TEMP directory detected. '
        #                     "It'll be ignored when directory is analized.")
        #     episodes_or_images.remove('thumbnail-TEMP')

        if len(episodes_or_images) == 0:  # sourcery skip
            logging.warning("It looks like the directory is empty. It cannot be something")
            return NOT_MATCHED

        if len(episodes_or_images) == 1:
            # 1개일 경우 썸네일 스킵 기능으로 인해 fast_check_directory_state가 제대로 동작하지 않는데,
            # 이때 check_filename_state를 사용하면 정확한 결과를 얻을 수 있다.
            return self.check_filename_state(episodes_or_images[0])

        directory_states_dict: dict[DIRECTORY_STATES, tuple[bool, int]] = {}

        for state_name, regex in state_and_regexes.items():
            # 매치되지 '않은' 것의 개수를 세는 것을 주의!!!
            number_of_images_NOT_matched = sum(
                0 if regex.match(episode_or_image) else 1
                for episode_or_image in episodes_or_images
            )

            # tuple의 0번째 값은 해당 state가 맞다는 의미이다.
            directory_states_dict[state_name] = (number_of_images_NOT_matched <= 1, number_of_images_NOT_matched)

        not_matched_state = sum(value[0] for value in directory_states_dict.values())

        if not_matched_state == 0:
            logging.warning('This directory is not any specific state. '
                            "Probably the directory is not a webtoon directory. "
                            "Or something went wrong when being processed.")

        if not_matched_state == 1:
            for state_name, (bool_state, int_state) in directory_states_dict.items():
                if bool_state:
                    return state_name

        elif not_matched_state == 2:
            detected_states = [state_name for state_name, (bool_state, int_state)
                               in directory_states_dict.items() if bool_state]

            logging.warning(f'This directory is either {detected_states[0]} and {detected_states[1]}. '
                            "Probably there's a conflict. Please check your directory again.")

        else:
            # 참고: episodes_or_images의 길이가 0인 경우와 1인 경우는 이미 앞에서 다룸.
            directory_states_concatenated = ", ".join(state_name for state_name, (bool_state, int_state)
                                                      in directory_states_dict.items() if bool_state)
            logging.warning(f'This directory is {directory_states_concatenated}. Please check your directory again.')

        return NOT_MATCHED

    ############### RESTORE FUNCTIONALITY ###############

    def restore_webtoons_from_source_dir(self) -> None:
        webtoons = os.listdir(self.source_dir)
        for webtoon in webtoons:
            webtoon_dir = self.source_dir / webtoon
            self.restore_webtoon(webtoon_dir)

    def restore_webtoon(self, directory: Path) -> None:
        # Thumbnail 옮기기
        temp_thumbnail_path = directory.parent / f'TEMP-thumbnail-{directory.name}'
        temp_thumbnail_path.mkdir(parents=True)
        self.move_thumbnail_only(directory, temp_thumbnail_path)

        dir_state = self.detailed_check_directory_state(directory)
        if dir_state == MERGED:  # 가장 기본적인 상태
            self.all_images_to_one_source_dir_with_rename(directory, rename=False)
        elif dir_state == UNIFIED:
            ...  # 나중의 코드 처리를 위한 빈칸
        else:
            raise DirectoryStateUnmatched(f'State of directory is {dir_state}, which cannot be restored.\n'
                                          f'Directory name: {directory}')

        images = os.listdir(directory)

        for image in images:
            image_info = webtoon_regexes.unified_image.search(image)
            if not image_info:
                raise ValueError('image name is not valid. Possibly trying not merged webtoon folder.')
            episode_no = image_info.group('episode_no')
            image_no = image_info.group('image_no')
            episode_name = image_info.group('episode_name')
            image_extension = image_info.group('extension')

            episode_dir = directory / f'{episode_no}. {episode_name}'
            alt_image_name = f'{image_no}.{image_extension}'
            episode_dir.mkdir(parents=True, exist_ok=True)
            source_image_path = directory / image
            target_image_path = episode_dir / alt_image_name
            shutil.move(source_image_path, target_image_path)

        self.move_thumbnail_only(temp_thumbnail_path, directory)
        temp_thumbnail_path.rmdir()
