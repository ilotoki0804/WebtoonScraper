"""This module provides FolderMerger class."""
# 디렉토리 복구 함수 제작
from __future__ import annotations
import os
import shutil
import re
from collections import defaultdict
from pathlib import Path
import logging
from typing import Sequence, TypeAlias, Final, Literal, TypeVar

from .exceptions import DirectoryStateUnmatchedError, UserCanceledError, Unreachable

# container는 file을 담고 있는 것을 의미합니다.
# container에 들어가는 file이 directory일 수 있기 때문에
# directory라는 말을 사용할 경우 오해가 생길 수 있어 container라는 유사어로 대체하여 표현합니다.
# episode directory 같은 경우엔 image의 container이면서도 webtoon directory의 content입니다.
NORMAL_IMAGE: Final = "normal_image"
NORMAL_EPISODE_DIRECTORY: Final = "normal_episode_directory"
NORMAL_WEBTOON_DIRECTORY: Final = "normal_webtoon_directory"

MERGED_IMAGE: Final = "merged_image"
MERGED_EPISODE_DIRECTORY: Final = "merged_episode_directory"
MERGED_WEBTOON_DIRECTORY: Final = "merged_webtoon_directory"

# 만약 이름을 WEBTOONS_DIRECTORY로 한다면 매우 햇갈릴 가능성이 높기에 굳이 WEBTOON_DIRECTORY_CONTAINER라는 이름을 사용합니다.
WEBTOON_DIRECTORY: Final = "webtoon_directory"
WEBTOON_DIRECTORY_CONTAINER: Final = "webtoon_directory_container"

NOT_MATCHED: Final = "not_matched"

ContainerStates = Literal[
    "normal_webtoon_directory",
    "normal_episode_directory",
    "merged_webtoon_directory",
    "merged_episode_directory",
    "webtoon_directory_container",
    "not_matched",
]
FileStates = Literal[
    "normal_image",
    "normal_episode_directory",
    "merged_image",
    "merged_episode_directory",
    "webtoon_directory",
    "not_matched",
]
PathOrStr: TypeAlias = "str | Path"

# NOT_MATCHED를 제외한 모든 FileStates를 포함함.
FILE_TO_CONTAINER: Final[dict[FileStates, ContainerStates]] = {
    NORMAL_IMAGE: NORMAL_EPISODE_DIRECTORY,
    NORMAL_EPISODE_DIRECTORY: NORMAL_WEBTOON_DIRECTORY,
    MERGED_IMAGE: MERGED_EPISODE_DIRECTORY,
    MERGED_EPISODE_DIRECTORY: MERGED_WEBTOON_DIRECTORY,
    WEBTOON_DIRECTORY: WEBTOON_DIRECTORY_CONTAINER,
}

CONTAINER_TO_FILE: Final[dict[str, str]] = {
    value: key for key, value in FILE_TO_CONTAINER.items()
}


# 각 라인 끝 주석 처리된 부분: 덜 예민한 버전(거의 대부분 매치 개수 관련임)의 regex; 만약 현재 regex가 잘 작동하지 않을 경우 사용할 것. 없을 수도 있음.
webtoon_regexes: dict[FileStates, re.Pattern[str]] = {
    NORMAL_IMAGE: re.compile(
        r"^(?P<image_no>\d{3})[.](?P<extension>[a-zA-Z0-9]{3,4})$"
    ),  # 023.jpg
    # ^(?P<image_no>\d+)[.](?P<extension>[a-zA-Z0-9]+)$
    NORMAL_EPISODE_DIRECTORY: re.compile(
        r"^(?P<episode_no>\d{4})\. (?P<episode_name>.+)$"
    ),  # 0001. episode_name
    MERGED_IMAGE: re.compile(
        r"^(?P<episode_no>\d{4})[.](?P<image_no>\d{3})[.] (?P<episode_name>.+)[.](?P<extension>[a-zA-Z]{3,4})$"
    ),  # 0001.001. episode_name.jpg
    # ^(?P<episode_no>\d+)[.](?P<image_no>\d+)[.] (?P<episode_name>.+)[.](?P<extension>[a-zA-Z]+)$
    MERGED_EPISODE_DIRECTORY: re.compile(
        r"^(?P<from>\d{4})~(?P<to>\d{4})$"
    ),  # 0001~0005
    # ^(?P<from>\d+)~(?P<to>\d+)$
    WEBTOON_DIRECTORY: re.compile(
        r"^(?P<webtoon_name>.+)[(](?P<titleid>(?!merged).+?)[)](?:[(]merged[)])?$"
    ),  # webtoon_name(titleid)[(merged)]
}

T = TypeVar("T")


def _select_from_sequence(sequence_to_select: Sequence[T], message: str | None) -> T:
    if message is not None:
        print(message)
    if len(sequence_to_select) < 10:
        for i, item in enumerate(sequence_to_select, 1):
            print(f"{i}. {item}")
    else:
        for i, item in enumerate(sequence_to_select, 1):
            print(f"{i:02d}. {item}")

    user_answer = int(input("Enter number: "))
    return sequence_to_select[user_answer - 1]


def select_from_directory(
    source_parent_directory: Path,
    target_parent_directory: Path | None,
    merge_number: int | None = None,
):
    directories, files = _iterdir_seperating_directories_and_files(
        source_parent_directory, treat_underscored_directories_as_file=False
    )

    not_webtoon_directories: list[Path] = []
    normal_webtoon_directories: list[Path] = []
    merged_webtoon_directories: list[Path] = []
    for directory in directories:
        container_state = check_container_state(directory)
        if container_state == NORMAL_WEBTOON_DIRECTORY:
            normal_webtoon_directories.append(directory)
        elif container_state == MERGED_WEBTOON_DIRECTORY:
            merged_webtoon_directories.append(directory)
        else:
            not_webtoon_directories.append(directory)

    # 0을 몇 개 쓸 것인지를 결정
    number_length = len(
        str(
            (len(normal_webtoon_directories) > 1)
            + (len(merged_webtoon_directories) > 1)
            + len(merged_webtoon_directories)
            + len(normal_webtoon_directories)
        )
    )

    if not normal_webtoon_directories and not merged_webtoon_directories:
        print("There's no webtoon directories.")
        return

    options: dict[int, str | Path] = {}
    i = 1
    if len(normal_webtoon_directories) > 1:
        print(
            f"{i:0{number_length}}. Merge every {len(normal_webtoon_directories)} normal webtoons."
        )
        options[i] = "merge_all"
        i += 1
    for normal_webtoon_directory in normal_webtoon_directories:
        print(f"{i:0{number_length}}. Merge {normal_webtoon_directory.name}")
        options[i] = normal_webtoon_directory
        i += 1
    if len(normal_webtoon_directories) > 1 and len(merged_webtoon_directories) > 1:
        print("=" * 20)
    if len(merged_webtoon_directories) > 1:
        print(
            f"{i:0{number_length}}. Restore every {len(merged_webtoon_directories)} merged webtoons."
        )
        options[i] = "restore_all"
        i += 1
    for merged_webtoon_directory in merged_webtoon_directories:
        print(f"{i:0{number_length}}. Restore {merged_webtoon_directory.name}")
        options[i] = merged_webtoon_directory
        i += 1
    match len(not_webtoon_directories):
        case 0:
            pass
        case 1:
            print(
                f"(Directory {not_webtoon_directories[0].name} is hidden because it's not a webtoon directory.)"
            )
        case _:
            print(
                f"({len(not_webtoon_directories)} directories are hidden because they are not webtoon directories.)"
            )

    result = input("Enter number: ")
    try:
        selected = options[int(result)]
    except (IndexError, ValueError) as e:
        raise ValueError("User input is invalid.") from e

    def get_merge_number():
        # 혹시 merge_number가 0일 경우를 대비해 is None 사용.
        return int(input("merge number: ")) if merge_number is None else merge_number

    match selected:
        case "merge_all":
            for merged_webtoon_directory in merged_webtoon_directories:
                merge_webtoon(
                    merged_webtoon_directory,
                    target_parent_directory
                    and target_parent_directory / merged_webtoon_directory.name,
                    get_merge_number(),
                )
        case "restore_all":
            for normal_webtoon_directory in normal_webtoon_directories:
                restore_webtoon(
                    normal_webtoon_directory,
                    target_parent_directory
                    and target_parent_directory / normal_webtoon_directory.name,
                )
        case path:
            assert not isinstance(path, str)
            # check_container_state를 두 번 하는 게 비효율적일 수 있음.
            container_state = check_container_state(path)

            if container_state == NORMAL_WEBTOON_DIRECTORY:
                merge_webtoon(
                    path,
                    target_parent_directory and target_parent_directory / path.name,
                    get_merge_number(),
                )
            elif container_state == MERGED_WEBTOON_DIRECTORY:
                restore_webtoon(
                    path,
                    target_parent_directory and target_parent_directory / path.name,
                )
            else:
                # container_state는 기존에 다 확인하고 저 두 상태 중 하나가 보장된 상태이기에
                # 여기에 걸릴 확률은 없음.
                raise Unreachable()


def _get_episode_no(directory_name: str) -> int:
    directory_name_matched = webtoon_regexes[NORMAL_EPISODE_DIRECTORY].match(
        directory_name
    )
    assert (
        directory_name_matched is not None
    ), f"Directory state is invalid. {directory_name = }"
    return int(directory_name_matched.group("episode_no"))


def merge_webtoon(
    source_webtoon_directory: Path,
    target_webtoon_directory: Path | None,
    merge_number: int,
    manual_directory_state: ContainerStates | None = None,
    merge_last_bundle: bool = True,
) -> None:
    """
    Args:
        source_webtoon_directory: 소스가 되는 웹툰이 들어있는 디렉토리입니다.
        target_webtoon_directory: 웹툰은 merge한 결과가 있을 디렉토리입니다. \
            만약 None이면 source_webtoon_directory와 같은 경로로 지정됩니다.
        merge_number: 한 merged episode에 들어갈 에피소드의 개수입니다.
        manual_directory_state: \
            디렉토리 상태는 기본적으로 자동으로 감지되도록 되어 있습니다. \
            그러나 자동 감지 결과를 무시하고 직접 디렉토리 상태를 설정하고 싶을 경우 이 인자를 통해 \
            자신이 원하는 디렉토리 상태를 설정할 수 있습니다. 권장되지는 않습니다.
        merge_last_bundle: \
            마지막 merged episode의 크기는 merge number에 비해 작을 수 있습니다. \
            이 인자가 참일 경우 마지막 merged episode를 그 전의 merged episode와 통합합니다.
    """
    target_webtoon_directory = target_webtoon_directory or source_webtoon_directory

    directory_state = manual_directory_state or check_container_state(
        source_webtoon_directory
    )
    if directory_state != NORMAL_WEBTOON_DIRECTORY:
        raise DirectoryStateUnmatchedError(
            f"State of directory is {directory_state}, which cannot be merged."
            + (
                " Maybe what you need was restore_webtoon."
                if directory_state == MERGED_WEBTOON_DIRECTORY
                else ""
            )
            + f"\nsource webtoon directory: {source_webtoon_directory}"
        )

    # source_webtoon_directory == target_webtoon_directory인 경우 때문에 exist_ok는 True여야 한다.
    target_webtoon_directory.mkdir(parents=True, exist_ok=True)

    directories, files = _iterdir_seperating_directories_and_files(
        source_webtoon_directory
    )

    # 디렉토리 그룹핑
    grouped_directories: defaultdict[int, list[Path]] = defaultdict(list)
    for directory in directories:
        episode_no = _get_episode_no(directory.name)
        grouped_directories[(episode_no - 1) // merge_number].append(directory)

    # 마지막 번들 묶기
    last_bundle = max(grouped_directories)
    if merge_last_bundle and len(grouped_directories[last_bundle]) < merge_number:
        last_bundle_items = grouped_directories.pop(last_bundle)
        grouped_directories[max(grouped_directories)] += last_bundle_items

    # 그루핑 끝난 디렉토리들 실제로 옮김
    for directories in grouped_directories.values():
        # 디렉토리명 만듦
        episode_no_range = sorted(
            _get_episode_no(directory.name) for directory in directories
        )
        new_directory_name = f"{episode_no_range[0]:04d}~{episode_no_range[-1]:04d}"
        target_episode_directory = target_webtoon_directory / new_directory_name
        target_episode_directory.mkdir()

        for directory in directories:
            for image_name in os.listdir(directory):
                merged_name = _get_merged_image_name(image_name, directory.name)
                os.rename(
                    directory / image_name, target_episode_directory / merged_name
                )
            directory.rmdir()

    # 남은 폴더가 아닌 파일들 옮기기
    if source_webtoon_directory != target_webtoon_directory and files:
        for file in files:
            os.rename(file, target_webtoon_directory / file.name)
        if not os.listdir(source_webtoon_directory):
            source_webtoon_directory.rmdir()


def move_thumbnail_only(
    source_webtoon_directory: Path,
    target_webtoon_directory: Path,
    is_real_webtoon_directory=False,
    copy: bool = False,
    exclude_file_names: list[str] | None = None,
) -> None:
    """
    is_real_webtoon_directory가 참이면 source_webtoon_directory의 이름에 기반해 썸네일을 찾습니다.
    하지만 기존 방식이 딱히 인식률이 좋지 않거나 단점이 있는 것이 아니라서 일반적인 환경에서는 굳이 이용할 이유가 없습니다.
    """
    if is_real_webtoon_directory:
        processed_webtoon_directory_name = webtoon_regexes[WEBTOON_DIRECTORY].match(
            source_webtoon_directory.name
        )
        if processed_webtoon_directory_name is not None:
            webtoon_name = processed_webtoon_directory_name.group("webtoon_name")
        else:
            logging.warning(
                "Directory seems not following general rule. Use normal way to move thumbnail instead."
            )
            move_thumbnail_only(
                source_webtoon_directory, target_webtoon_directory, False
            )
            return

        for episode_or_thumbnail in os.listdir(source_webtoon_directory):
            if exclude_file_names and episode_or_thumbnail in exclude_file_names:
                continue
            processed_episode_or_thumbnail_directory_name = webtoon_regexes[
                WEBTOON_DIRECTORY
            ].match(episode_or_thumbnail.removeprefix("TEMP-thumbnail-"))
            if (
                processed_episode_or_thumbnail_directory_name is None
                or not processed_episode_or_thumbnail_directory_name.group(
                    "webtoon_name"
                )
            ):
                continue
            if processed_episode_or_thumbnail_directory_name.group(1) == webtoon_name:
                # 아래의 is_real_webtoon_directory가 False일 때의 코드와 동일함. 필요한 경우 있을 경우 따로 함수로 분리할 것.
                source_thumbnail_directory = (
                    source_webtoon_directory / episode_or_thumbnail
                )
                target_thumbnail_directory = (
                    target_webtoon_directory / episode_or_thumbnail
                )
                shutil.move(source_thumbnail_directory, target_thumbnail_directory)
                return
    else:
        for episode_or_thumbnail in os.listdir(source_webtoon_directory):
            if check_filename_state(episode_or_thumbnail) is NOT_MATCHED:
                source_thumbnail_directory = (
                    source_webtoon_directory / episode_or_thumbnail
                )
                target_thumbnail_directory = (
                    target_webtoon_directory / episode_or_thumbnail
                )
                if copy:
                    shutil.copyfile(
                        source_thumbnail_directory, target_thumbnail_directory
                    )
                else:
                    shutil.move(source_thumbnail_directory, target_thumbnail_directory)
                return


def _get_merged_image_name(image_name: str, episode_name: str) -> str:
    """merged 상태의 image가 가져야 할 이름을 내놓습니다."""
    image_name_processed: re.Match[str] | None = webtoon_regexes[NORMAL_IMAGE].match(
        image_name
    )
    episode_name_processed: re.Match[str] | None = webtoon_regexes[
        NORMAL_EPISODE_DIRECTORY
    ].match(episode_name)
    if not episode_name_processed:
        if webtoon_regexes[MERGED_EPISODE_DIRECTORY].match(episode_name):
            raise ValueError(
                "Episode name is not valid. It's because you tried to merge already merged webtoon directory."
            )
        raise ValueError(f"Episode name is not valid. Episode name: {episode_name}")
    if not image_name_processed:
        raise ValueError(f"Image name is not vaild. Image name: {image_name}")

    image_no = image_name_processed.group("image_no")
    image_extension = image_name_processed.group("extension")
    episode_no = episode_name_processed.group("episode_no")
    episode_name = episode_name_processed.group("episode_name")

    return f"{episode_no}.{image_no}. {episode_name}.{image_extension}"


############### CHECKING FUNCTIONALITY ###############


def _iterdir_seperating_directories_and_files(
    directory: PathOrStr,
    treat_underscored_directories_as_file: bool = True,
) -> tuple[list[Path], list[Path]]:
    directories: list[Path] = []
    files: list[Path] = []
    for path in Path(directory).iterdir():
        if path.is_dir() and not (
            treat_underscored_directories_as_file
            and path.name.startswith("_")
            and not path.name.startswith("__")
        ):
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


def check_container_state(
    directory: PathOrStr, *, warn: bool = True
) -> ContainerStates:
    """해당 path에 있는 디렉토리의 상태를 확인합니다."""
    directory = Path(directory)
    if not directory.exists():
        if warn:
            logging.warning(f"It looks like the directory({directory}) doesn't exist.")
        return NOT_MATCHED

    if directory.is_file():
        if warn:
            logging.warning(f"It looks like the file({directory}) is not a directory.")
        return NOT_MATCHED

    directories, _ = _iterdir_seperating_directories_and_files(directory)

    if not directories:
        if warn:
            logging.warning(
                f"It looks like the directory({directory}) is empty. It cannot be something"
            )
        return NOT_MATCHED

    for state_name, regex in webtoon_regexes.items():
        # 매치되지 '않은' 것의 개수를 세는 것을 주의!!!
        if not sum(
            not regex.match(episode_or_image.name) for episode_or_image in directories
        ):
            return FILE_TO_CONTAINER.get(state_name, NOT_MATCHED)

    return NOT_MATCHED


############### RESTORE FUNCTIONALITY ###############


def _get_directory_and_image_name_from_merged_image_name(merged_image_name: str):
    image_info = webtoon_regexes[MERGED_IMAGE].match(merged_image_name)
    assert image_info, "image name is not merged image."
    episode_no = image_info.group("episode_no")
    image_no = image_info.group("image_no")
    episode_name = image_info.group("episode_name")
    image_extension = image_info.group("extension")

    new_episode_directory_name = f"{episode_no}. {episode_name}"
    new_image_name = f"{image_no}.{image_extension}"
    return new_episode_directory_name, new_image_name


def restore_webtoon(
    source_webtoon_directory: Path,
    target_webtoon_directory: Path | None,
    manual_directory_state: ContainerStates | None = None,
) -> None:
    """Merged된 웹툰 폴더의 상태를 되돌립니다."""
    target_webtoon_directory = target_webtoon_directory or source_webtoon_directory

    directory_state = manual_directory_state or check_container_state(
        source_webtoon_directory
    )
    if directory_state != MERGED_WEBTOON_DIRECTORY:
        raise DirectoryStateUnmatchedError(
            f"State of directory is {directory_state}, which cannot be restored."
            + (
                " Maybe what you need was merge_webtoon."
                if directory_state == NORMAL_WEBTOON_DIRECTORY
                else ""
            )
            + f"\nsorce webtoon directory: {source_webtoon_directory}"
        )

    directories, files = _iterdir_seperating_directories_and_files(
        source_webtoon_directory
    )
    for directory in directories:
        for image_name in os.listdir(directory):
            (
                target_episode_directory_name,
                target_image_name,
            ) = _get_directory_and_image_name_from_merged_image_name(image_name)
            target_episode_directory = (
                target_webtoon_directory / target_episode_directory_name
            )
            target_episode_directory.mkdir(exist_ok=True)
            os.rename(
                directory / image_name, target_episode_directory / target_image_name
            )
        directory.rmdir()

    # 남은 폴더가 아닌 파일들 옮기기
    if source_webtoon_directory != target_webtoon_directory and files:
        for file in files:
            os.rename(file, target_webtoon_directory / file.name)
        if not os.listdir(source_webtoon_directory):
            source_webtoon_directory.rmdir()
