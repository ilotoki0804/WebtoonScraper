"""This module provides FolderMerger class."""
# 디렉토리 복구 함수 제작
from __future__ import annotations
import os
import shutil
import re
from collections import defaultdict
from pathlib import Path
import logging
from typing import Iterable, TypeAlias, Final

from typing_extensions import Literal

from .exceptions import DirectoryStateUnmatchedError, UserCanceledError

# container는 file을 담고 있는 것을 의미합니다.
# container에 들어가는 file이 directory일 수 있기 때문에
# directory라는 말을 사용할 경우 오해가 생길 수 있어 container라는 유사어로 대체하여 표현합니다.
# episode directory 같은 경우엔 image의 container이면서도 webtoon directory의 content입니다.
NORMAL_WEBTOON_DIRECTORY: Final = 'normal_webtoon_directory'
NORMAL_EPISODE_DIRECTORY: Final = 'normal_episode_directory'
NORMAL_IMAGE: Final = 'normal_image'

MERGED_WEBTOON_DIRECTORY: Final = 'merged_webtoon_directory'
MERGED_EPISODE_DIRECTORY: Final = 'merged_episode_directory'
# merged episode directory와 unified webtoon directory는 본질적으로 같으며,
# 의미를 확실하게 하기 위해 동일한 값의 다른 변수를 만듦.
UNIFIED_WEBTOON_DIRECTORY: Final = MERGED_EPISODE_DIRECTORY
MERGED_IMAGE: Final = 'merged_image'

# 만약 이름을 WEBTOONS_DIRECTORY로 한다면 매우 햇갈릴 가능성이 높기에 굳이 WEBTOON_DIRECTORY_CONTAINER라는 이름을 사용합니다.
WEBTOON_DIRECTORY_CONTAINER: Final = 'webtoon_directory_container'
WEBTOON_DIRECTORY: Final = 'webtoon_directory'

NOT_MATCHED: Final = 'not_matched'

ContainerStates = Literal['normal_webtoon_directory', 'normal_episode_directory', 'merged_webtoon_directory',
                          'merged_episode_directory', 'webtoon_directory_container', 'not_matched']
FileStates = Literal['normal_episode_directory', 'normal_image', 'merged_episode_directory', 'merged_image',
                     'webtoon_directory', 'not_matched']
PathOrStr: TypeAlias = 'str | Path'

# NOT_MATCHED를 제외한 모든 FileStates를 포함함.
FILE_TO_CONTAINER: Final[dict[FileStates, ContainerStates]] = {
    NORMAL_EPISODE_DIRECTORY: NORMAL_WEBTOON_DIRECTORY,
    NORMAL_IMAGE: NORMAL_EPISODE_DIRECTORY,

    MERGED_EPISODE_DIRECTORY: MERGED_WEBTOON_DIRECTORY,
    MERGED_IMAGE: MERGED_EPISODE_DIRECTORY,

    WEBTOON_DIRECTORY: WEBTOON_DIRECTORY_CONTAINER,
}

CONTAINER_TO_FILE: Final[dict[str, str]] = {value: key for key, value in FILE_TO_CONTAINER.items()}


# 각 라인 끝 주석 처리된 부분: 덜 예민한 버전(거의 대부분 매치 개수 관련임)의 regex; 만약 현재 regex가 잘 작동하지 않을 경우 사용할 것. 없을 수도 있음.
webtoon_regexes: dict[FileStates, re.Pattern[str]] = {
    NORMAL_EPISODE_DIRECTORY: re.compile(r'^(?P<episode_no>\d{4})\. (?P<episode_name>.+)$'),  # 0001. episode_name
    NORMAL_IMAGE: re.compile(r'^(?P<image_no>\d{3})[.](?P<extension>[a-zA-Z0-9]{3,4})$'),  # 023.jpg
    # ^(?P<image_no>\d+)[.](?P<extension>[a-zA-Z0-9]+)$

    MERGED_EPISODE_DIRECTORY: re.compile(r'^(?P<from>\d{4})~(?P<to>\d{4})$'),  # 0001~0005
    # ^(?P<from>\d+)~(?P<to>\d+)$
    MERGED_IMAGE: re.compile(r'^(?P<episode_no>\d{4})[.](?P<image_no>\d{3})[.] (?P<episode_name>.+)[.](?P<extension>[a-zA-Z]{3,4})$'),  # 0001.001. episode_name.jpg
    # ^(?P<episode_no>\d+)[.](?P<image_no>\d+)[.] (?P<episode_name>.+)[.](?P<extension>[a-zA-Z]+)$

    WEBTOON_DIRECTORY: re.compile(r'^(?P<webtoon_name>.+)[(](?P<titleid>(?!merged).+?)[)](?:[(]merged[)])?$'),  # webtoon_name(titleid)[(merged)]
}


class DirectoryMerger:
    """웹툰 뷰어 앱에서 정주행하기 좋도록 회차들을 단위에 따라 묶습니다."""

    def __init__(self) -> None:
        """Subclass를 만든다면 super().__init__()뒤에 다른 코드를 삽입하세요."""
        self.source_directory = 'webtoon'
        self.target_directory = 'webtoon'

    @property
    def source_directory(self) -> Path:
        """웹툰이 저장되어 있는, 바꿀 웹툰이 있는 디렉토리입니다."""
        return self._base_directory

    @source_directory.setter
    def source_directory(self, source_directory: PathOrStr) -> None:
        self._base_directory = Path(source_directory)

    @property
    def target_directory(self) -> Path:
        """다 마친 웹툰을 저장할 디렉토리입니다. `self.base_directory`와 같아도 상관 없습니다."""
        return self._target_directory

    @target_directory.setter
    def target_directory(self, target_directory: PathOrStr) -> None:
        self._target_directory = Path(target_directory)

    ############### MAIN FUNCTIONALITY ###############

    def select(
        self,
        merge_amount: int | None = None,
        manual_container_state: ContainerStates | None = None,
        ask: bool = False,
    ) -> None:
        """소스 디렉토리에 있는 웹툰 디렉토리 중 사용자가 선택한 웹툰을 합칩니다."""
        webtoons = os.listdir(self.source_directory)

        print('Select webtoon to merge or restore.')
        if len(webtoons) < 10:
            for i, webtoon in enumerate(webtoons, 1):
                print(f'{i}. {webtoon}')
        else:
            for i, webtoon in enumerate(webtoons, 1):
                print(f'{i:02d}. {webtoon}')

        user_answer = int(input('Enter number: '))
        selected_webtoon_directory_name = webtoons[user_answer - 1]

        selected_directory = self.source_directory / selected_webtoon_directory_name

        if manual_container_state is None:
            directory_state = fast_check_container_state(selected_directory)
        else:
            directory_state = manual_container_state

        if directory_state == NORMAL_WEBTOON_DIRECTORY:
            action = 'merge'
        elif directory_state == MERGED_WEBTOON_DIRECTORY:
            action = 'restore'
        else:
            raise DirectoryStateUnmatchedError('Directory state is nether default state nor merged. Cannot merge or restore.')

        if ask:
            if directory_state == NORMAL_WEBTOON_DIRECTORY:
                user_answer = input(f'{selected_webtoon_directory_name} seems default state. Merge it? '
                                    '(merge(m), restore(r), cancel(c), default: merge) ').lower()
                action = 'restore' if user_answer in {'restore', 'r'} else 'merge'
            else:
                user_answer = input(f'{selected_webtoon_directory_name} seems merged state. Restore it? '
                                    '(restore(r), merge(m), cancel(c) default: restore) ').lower()
                action = 'merge' if user_answer in {'merge', 'm'} else 'restore'

            if user_answer in {'cancel', 'c'}:
                raise UserCanceledError("User canceled to merge or restore.")

        message = "Merging" if action == "merge" else "Restoring"

        print(f'{selected_webtoon_directory_name} is selected. {message} webtoon has started.')
        if action == 'merge':
            if merge_amount is None:
                merge_amount = int(input('merge amount: '))
            merge_webtoon(selected_directory, merge_amount)
        else:
            restore_webtoon(selected_directory)
        print(f'{message} webtoon has ended.')

    def merge_webtoons_from_source_directory(self, merge_amount: int) -> None:
        """소스 디렉토리에 있는 모든 웹툰 디렉토리들을 합쳐 다시 소스 디렉토리에 놓습니다."""
        webtoons = os.listdir(self.source_directory)
        for webtoon in webtoons:
            webtoon_directory = self.target_directory / webtoon
            try:
                merge_webtoon(webtoon_directory, merge_amount)
            except DirectoryStateUnmatchedError:
                logging.warning(f'Skip {webtoon_directory} directory. It looks not available to merge.')

    def restore_webtoons_from_source_directory(self) -> None:
        """소스 디렉토리에 있는 모든 웹툰 디렉토리들을 합쳐진 상태에서 다시 복구해 소스 디렉토리에 놓습니다."""
        webtoons = os.listdir(self.source_directory)
        for webtoon in webtoons:
            webtoon_directory = self.source_directory / webtoon
            try:
                restore_webtoon(webtoon_directory)
            except DirectoryStateUnmatchedError:
                logging.warning(f'Skip {webtoon_directory} directory. It looks not available to restore.')


def _get_episode_no(directory_name: str) -> int:
    directory_name_matched = webtoon_regexes[NORMAL_EPISODE_DIRECTORY].match(directory_name)
    assert directory_name_matched is not None, f"Directory state is invalid. {directory_name = }"
    return int(directory_name_matched.group("episode_no"))


def fast_merge_webtoon(
    source_webtoon_directory: Path,
    target_webtoon_directory: Path,
    merge_amount: int,
    manual_directory_state: ContainerStates | None = None,
    merge_last_bundle: bool = True,
) -> None:
    """
    merge_webtoon이나 merge_webtoon_directory_to_directory와 동일하지만 중요한 차이점이 몇 가지 있습니다.
    1. 같은 폴더로 이동하는 경우와 아닌 경우를 구분하지 않습니다.
    1. 파일을 단 한 번 이동합니다.
    1. 폴더가 아닌 파일은 merge를 방해하지 않으며 잘 integrate됩니다.

    Args:
        source_webtoon_directory: 소스가 되는 웹툰이 들어있는 디렉토리입니다.
        target_webtoon_directory: 웹툰은 merge한 결과가 있을 디렉토리입니다.
        merge_amount: 한 merged episode에 들어갈 에피소드의 개수입니다.
        manual_directory_state: \
            디렉토리 상태는 기본적으로 자동으로 감지되도록 되어 있습니다. \
            그러나 자동 감지 결과를 무시하고 직접 디렉토리 상태를 설정하고 싶을 경우 이 인자를 통해 \
            자신이 원하는 디렉토리 상태를 설정할 수 있습니다. 권장되지는 않습니다.
        merge_last_bundle: \
            마지막 merged episode의 크기는 merge amount에 비해 작을 수 있습니다. \
            이 인자가 참일 경우 마지막 merged episode를 그 전의 merged episode와 통합합니다.
    """
    directory_state = manual_directory_state or fast_check_container_state(source_webtoon_directory)
    if directory_state != NORMAL_WEBTOON_DIRECTORY:
        raise DirectoryStateUnmatchedError(
            f'State of directory is {directory_state}, which cannot be merged.'
            + (' Maybe what you need was restore_webtoon.' if directory_state == MERGED_WEBTOON_DIRECTORY else '')
            + f'\nsorce webtoon directory: {source_webtoon_directory}'
        )

    # source_webtoon_directory == target_webtoon_directory인 경우 때문에 exist_ok는 True여야 한다.
    target_webtoon_directory.mkdir(parents=True, exist_ok=True)

    directories, files = _iterdir_seperating_directories_and_files(source_webtoon_directory)

    # 디렉토리 그룹핑
    grouped_directories: defaultdict[int, list[Path]] = defaultdict(list)
    for directory in directories:
        episode_no = _get_episode_no(directory.name)
        grouped_directories[episode_no // merge_amount].append(directory)

    # 마지막 번들 묶기
    last_bundle = max(grouped_directories)
    if last_bundle < merge_amount and merge_last_bundle:
        last_bundle_items = grouped_directories.pop(last_bundle)
        grouped_directories[max(grouped_directories)] += last_bundle_items

    # 그루핑 끝난 디렉토리들 실제로 옮김
    for directories in grouped_directories.values():
        # 디렉토리명 만듦
        episode_no_range = {
            _get_episode_no(directory.name) for directory in directories
        }
        new_directory_name = f'{min(episode_no_range):04d}~{max(episode_no_range):04d}'
        target_episode_directory = target_webtoon_directory / new_directory_name
        target_episode_directory.mkdir()

        for directory in directories:
            for image_name in os.listdir(directory):
                merged_name = _get_merged_image_name(image_name, directory.name)
                os.renames(directory / image_name, target_episode_directory / merged_name)

    # 남은 폴더가 아닌 파일들 옮기기
    if source_webtoon_directory != target_webtoon_directory and files:
        for file in files:
            os.renames(file, target_webtoon_directory / file.name)


def merge_webtoon(
    webtoon_directory: Path,
    merge_amount: int,
) -> None:
    """
    merge_webtoon_directory_to_directory는 source_webtoon_directory/target_webtoon_directory 두 가지 input을 받지만,
    merge_webtoon는 한 디렉토리의 상태를 바꿔줍니다.
    webtoon_directory에 있는 웹툰을 합칩니다. 합쳐진 내용물을 기존 웹툰 디렉토리에 저장됩니다.
    주의: 이 함수는 윈도우에서 가끔씩 권한 오류로 실패합니다. 그럴 경우 (merged)가 붙어 있는 폴더에서 (merged)를 제거해 수동으로 디렉토리 이름을 변경해 주세요.
    """
    temp_target_webtoon_directory = Path(f'{webtoon_directory}(merged)')
    merge_webtoon_directory_to_directory(webtoon_directory, temp_target_webtoon_directory, merge_amount)
    try:
        temp_target_webtoon_directory.rename(webtoon_directory)
    except PermissionError:
        logging.error(f'Failed to rename {temp_target_webtoon_directory.name} to {webtoon_directory.name}.\n'
                      "It's quite often situation so nothing to concern about. "
                      "But you have to change its name by hand.")


def merge_webtoon_directory_to_directory(
    source_webtoon_directory: Path,
    target_webtoon_directory: Path,
    merge_amount: int,
    manual_directory_state: ContainerStates | None = None,
    merge_last_bundle=True,
) -> None:
    """
    디렉토리를 하나로 합칩니다.
    만약 source_webtoon_directory와 target_webtoon_directory가 같다면 merge_webtoon를 사용하는 것을 권장합니다.
    """
    # base_webtoon_directory와 alt_webtoon_directory가 같으면 코드가 망가짐.
    if source_webtoon_directory == target_webtoon_directory:
        # logging.warning('base_webtoon_directory and alt_webtoon_directory are same. Use merge_webtoon_episodes instead.')
        return merge_webtoon(source_webtoon_directory, merge_amount)

    if manual_directory_state is None:
        directory_state = fast_check_container_state(source_webtoon_directory)
    else:
        directory_state = manual_directory_state

    if directory_state == MERGED_WEBTOON_DIRECTORY and merge_amount == 1:
        print('Value of episode_bundle is 1, so automatically revert directory state to original.')
        restore_webtoon(source_webtoon_directory)
        return
    if directory_state in {MERGED_WEBTOON_DIRECTORY, NOT_MATCHED, WEBTOON_DIRECTORY_CONTAINER}:
        raise DirectoryStateUnmatchedError(f'State of directory is {directory_state}, which cannot be merged.\n'
                                           f'sorce webtoon directory: {source_webtoon_directory}')

    # exist_ok=True는 옮기다 중간에 interrupt를 받아 끊긴 뒤 나중에 다시 재개할 때 도움이 된다.
    target_webtoon_directory.mkdir(parents=True, exist_ok=True)

    move_thumbnail_only(source_webtoon_directory, target_webtoon_directory)

    if directory_state == NORMAL_WEBTOON_DIRECTORY:
        _all_images_in_subdirectories_to_the_source_directory(source_webtoon_directory)
    elif directory_state == MERGED_WEBTOON_DIRECTORY:
        logging.info('Directory seems already unified, so skipping unifing.')

    episodes = os.listdir(source_webtoon_directory)

    # merge_last_bundle을 고려하지 않고 컬랙션을 제작함
    merged_images = defaultdict(list)
    for episode in episodes:
        episode_no = int(episode.split('.')[0])
        merged_images[(episode_no - 1) // merge_amount].append(episode)

    # merge_last_bundle을 적용함
    merged_images_name_list: list[tuple[int, list[str]]] = sorted(merged_images.items())
    _, last_images = merged_images_name_list[-1]
    if (
        merge_last_bundle
        and len(_find_episode_nos_of_unified_images(last_images)) < merge_amount
        and len(merged_images_name_list) >= 2
    ):
        merged_second_last_list = merged_images_name_list[-2][1]
        merged_second_last_list += merged_images_name_list.pop()[1]

    # 폴더에 넣는 과정
    for _, images in merged_images_name_list:
        alt_directory_name = _make_merged_directory_name(images)
        images_directory = target_webtoon_directory / alt_directory_name
        images_directory.mkdir(parents=True, exist_ok=True)
        for image in images:
            image_directory = source_webtoon_directory / image
            shutil.move(image_directory, images_directory)

    # 텅 빈 소스 디렉토리를 제거함
    os.rmdir(source_webtoon_directory)


def move_thumbnail_only(
    source_webtoon_directory: Path,
    target_webtoon_directory: Path,
    is_real_webtoon_directory=False,
    copy: bool = False,
    exclude_file_names: list[str] | None = None
) -> None:
    """
    is_real_webtoon_directory가 참이면 source_webtoon_directory의 이름에 기반해 썸네일을 찾습니다.
    하지만 기존 방식이 딱히 인식률이 좋지 않거나 단점이 있는 것이 아니라서 일반적인 환경에서는 굳이 이용할 이유가 없습니다.
    """
    if is_real_webtoon_directory:
        processed_webtoon_directory_name = webtoon_regexes[WEBTOON_DIRECTORY].match(source_webtoon_directory.name)
        if processed_webtoon_directory_name is not None:
            webtoon_name = processed_webtoon_directory_name.group('webtoon_name')
        else:
            logging.warning('Directory seems not following general rule. Use normal way to move thumbnail instead.')
            move_thumbnail_only(source_webtoon_directory, target_webtoon_directory, False)
            return

        for episode_or_thumbnail in os.listdir(source_webtoon_directory):
            if exclude_file_names and episode_or_thumbnail in exclude_file_names:
                continue
            processed_episode_or_thumbnail_directory_name = webtoon_regexes[WEBTOON_DIRECTORY].match(episode_or_thumbnail.removeprefix('TEMP-thumbnail-'))
            if processed_episode_or_thumbnail_directory_name is None or not processed_episode_or_thumbnail_directory_name.group('webtoon_name'):
                continue
            if processed_episode_or_thumbnail_directory_name.group(1) == webtoon_name:
                # 아래의 is_real_webtoon_directory가 False일 때의 코드와 동일함. 필요한 경우 있을 경우 따로 함수로 분리할 것.
                source_thumbnail_directory = source_webtoon_directory / episode_or_thumbnail
                target_thumbnail_directory = target_webtoon_directory / episode_or_thumbnail
                shutil.move(source_thumbnail_directory, target_thumbnail_directory)
                return
    else:
        for episode_or_thumbnail in os.listdir(source_webtoon_directory):
            if check_filename_state(episode_or_thumbnail) is NOT_MATCHED:
                source_thumbnail_directory = source_webtoon_directory / episode_or_thumbnail
                target_thumbnail_directory = target_webtoon_directory / episode_or_thumbnail
                if copy:
                    shutil.copyfile(source_thumbnail_directory, target_thumbnail_directory)
                else:
                    shutil.move(source_thumbnail_directory, target_thumbnail_directory)
                return


def _all_images_in_subdirectories_to_the_source_directory(source_directory: Path, rename=True) -> None:
    """모든 하위 디렉토리에 있는 이미지를 (rename이 True라면 이름 변경과 함께) 모두 소스 디렉토리로 옮깁니다. (rename이 True이면 Unifing이라고도 부릅니다.)"""
    episodes = os.listdir(source_directory)
    for episode in episodes:
        sub_episode_directory = source_directory / episode
        _move_folder_contents(sub_episode_directory, source_directory, episode, rename=rename)
        os.rmdir(sub_episode_directory)


def _move_folder_contents(
    source_directory: Path,
    target_directory: Path,
    episode_name: str | None = None,
    rename: bool = False,
) -> None:
    """
    이 함수는 soure_directory 안의 내용물을 target_directory로 보냅니다. 이때 rename이 True면 이름을 unifing에 알맞게 변경합니다.
    따라서 이 함수는 디렉토리 자체가 아닌 내용물을 옮기고 싶은 상황에서 유용합니다.
    """
    images = os.listdir(source_directory)

    for image in images:
        source_image_path = source_directory / image
        target_image_path = target_directory / (
            _get_merged_image_name(image, episode_name) if rename else image)
        shutil.move(source_image_path, target_image_path)


def _get_merged_image_name(image_name: str, episode_name: str) -> str:
    """merged 상태의 image가 가져야 할 이름을 내놓습니다."""
    image_name_processed: re.Match[str] | None = webtoon_regexes[NORMAL_IMAGE].match(image_name)
    episode_name_processed: re.Match[str] | None = webtoon_regexes[NORMAL_EPISODE_DIRECTORY].match(episode_name)
    if not episode_name_processed:
        if webtoon_regexes[MERGED_EPISODE_DIRECTORY].match(episode_name):
            raise ValueError(
                "Episode name is not valid. It's because you tried to merge already merged webtoon directory.")
        raise ValueError(f'Episode name is not valid. Episode name: {episode_name}')
    if not image_name_processed:
        raise ValueError(f'Image name is not vaild. Image name: {image_name}')

    image_no = image_name_processed.group('image_no')
    image_extension = image_name_processed.group('extension')
    episode_no = episode_name_processed.group('episode_no')
    episode_name = episode_name_processed.group('episode_name')

    return f'{episode_no}.{image_no}. {episode_name}.{image_extension}'


def _find_episode_nos_of_unified_images(image_names: Iterable[str]) -> set[int]:
    """Unified된 이미지들의 이름을 받아 거기 있는 episode_no를 뽑아냅니다."""
    unique_ids: set[int] = set()
    for image in image_names:
        result = webtoon_regexes[MERGED_IMAGE].match(image)
        if result is None:
            directory_state = check_filename_state(image)
            raise DirectoryStateUnmatchedError(
                f'State of directory is {FILE_TO_CONTAINER[directory_state]}, which cannot be merged.\nProblematic image name: {image}')
        unique_ids.add(int(result.group('episode_no')))
    return unique_ids


def _make_merged_directory_name(image_names: Iterable[str]) -> str:
    """merged 상태의 directory가 가져야 할 이름을 내놓습니다."""
    episode_id = _find_episode_nos_of_unified_images(image_names)
    return f'{min(episode_id):04d}~{max(episode_id):04d}'


############### CHECKING FUNCTIONALITY ###############


def _iterdir_seperating_directories_and_files(directory: PathOrStr) -> tuple[list[Path], list[Path]]:
    directories: list[Path] = []
    files: list[Path] = []
    for path in Path(directory).iterdir():
        if path.is_dir():
            directories.append(path)
        else:
            files.append(path)
    return directories, files


def check_filename_state(file_or_directory_name: str) -> FileStates:
    """한 파일(혹은 디렉토리) 이름의 상태를 확인합니다."""
    # sourcery skip: use-next; for simplicity and extensibility, decide not to apply 'use-next'
    for state_name, regex in webtoon_regexes.items():
        if regex.match(file_or_directory_name):
            return state_name
    return NOT_MATCHED


def fast_check_container_state(directory: PathOrStr) -> ContainerStates:
    """해당 path에 있는 디렉토리의 상태를 확인합니다."""
    directories, _ = _iterdir_seperating_directories_and_files(directory)

    if len(directories) == 0:  # sourcery skip: simplify-len-comparison; 일관성을 위해 사용하지 않음.
        logging.warning("It looks like the directory is empty. It cannot be something")
        return NOT_MATCHED

    for state_name, regex in webtoon_regexes.items():
        # 매치되지 '않은' 것의 개수를 세는 것을 주의!!!
        if not sum(
            not regex.match(episode_or_image.name)
            for episode_or_image in directories
        ):
            return FILE_TO_CONTAINER.get(state_name, NOT_MATCHED)

    return NOT_MATCHED


############### RESTORE FUNCTIONALITY ###############


def _get_directory_and_image_name_from_merged_image_name(merged_image_name: str):
    image_info = webtoon_regexes[MERGED_IMAGE].match(merged_image_name)
    assert image_info, "image name is not merged image."
    episode_no = image_info.group('episode_no')
    image_no = image_info.group('image_no')
    episode_name = image_info.group('episode_name')
    image_extension = image_info.group('extension')

    new_episode_directory_name = f'{episode_no}. {episode_name}'
    new_image_name = f'{image_no}.{image_extension}'
    return new_episode_directory_name, new_image_name


def fast_restore_webtoon(
    source_webtoon_directory: Path,
    target_webtoon_directory: Path,
    manual_directory_state: ContainerStates | None = None,
) -> None:
    """Merged된 웹툰 폴더의 상태를 되돌립니다."""
    directory_state = manual_directory_state or fast_check_container_state(source_webtoon_directory)
    if directory_state != MERGED_WEBTOON_DIRECTORY:
        raise DirectoryStateUnmatchedError(
            f'State of directory is {directory_state}, which cannot be restored.'
            + (' Maybe what you need was merge_webtoon.' if directory_state == NORMAL_WEBTOON_DIRECTORY else '')
            + f'\nsorce webtoon directory: {source_webtoon_directory}'
        )

    directories, files = _iterdir_seperating_directories_and_files(source_webtoon_directory)
    for directory in directories:
        for image_name in os.listdir(directory):
            target_episode_directory_name, target_image_name = _get_directory_and_image_name_from_merged_image_name(image_name)
            target_episode_directory = target_webtoon_directory / target_episode_directory_name
            os.renames(directory / image_name, target_episode_directory / target_image_name)

    # 남은 폴더가 아닌 파일들 옮기기
    if source_webtoon_directory != target_webtoon_directory and files:
        for file in files:
            os.renames(file, target_webtoon_directory / file.name)


def restore_webtoon_directory_to_directory(
    source_webtoon_directory: Path,
    target_webtoon_directory: Path,
    manual_directory_state: ContainerStates | None = None,
) -> None:
    restore_webtoon(source_webtoon_directory, manual_directory_state)
    target_webtoon_directory.parent.mkdir(exist_ok=True, parents=True)
    try:
        source_webtoon_directory.rename(target_webtoon_directory)
    except PermissionError:
        logging.error(f'Failed to rename {source_webtoon_directory.name} to {target_webtoon_directory.name}.\n'
                      "It's quite often situation so nothing to concern about. "
                      "But you have to change its name by hand.")


def restore_webtoon(directory: Path, manual_directory_state: ContainerStates | None = None) -> None:
    """Merged된 웹툰 폴더의 상태를 되돌립니다."""
    # Thumbnail 옮기기
    temp_thumbnail_path = directory.parent / f'TEMP-thumbnail-{directory.name}'
    temp_thumbnail_path.mkdir(parents=True)
    move_thumbnail_only(directory, temp_thumbnail_path)

    if manual_directory_state is None:
        directory_state = fast_check_container_state(directory)
        if directory_state == MERGED_WEBTOON_DIRECTORY:
            _all_images_in_subdirectories_to_the_source_directory(directory, rename=False)
        elif directory_state == UNIFIED_WEBTOON_DIRECTORY:
            ...  # 나중의 코드 처리를 위한 빈칸
        else:
            raise DirectoryStateUnmatchedError(
                f'State of directory is {directory_state}, which cannot be restored.\n'
                f'Directory name: {directory}'
            )
    else:
        directory_state = manual_directory_state

    images = os.listdir(directory)

    for image in images:
        image_info = webtoon_regexes[MERGED_IMAGE].match(image)
        assert image_info
        episode_no = image_info.group('episode_no')
        image_no = image_info.group('image_no')
        episode_name = image_info.group('episode_name')
        image_extension = image_info.group('extension')

        episode_directory = directory / f'{episode_no}. {episode_name}'
        alt_image_name = f'{image_no}.{image_extension}'
        episode_directory.mkdir(parents=True, exist_ok=True)
        source_image_path = directory / image
        target_image_path = episode_directory / alt_image_name
        shutil.move(source_image_path, target_image_path)

    move_thumbnail_only(temp_thumbnail_path, directory)
    temp_thumbnail_path.rmdir()
