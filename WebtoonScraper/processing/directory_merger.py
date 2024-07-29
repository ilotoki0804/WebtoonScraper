"""This module provides FolderMerger class."""

from __future__ import annotations

import os
import re
from collections import defaultdict
from contextlib import contextmanager
from pathlib import Path
from typing import Final, Literal, TypeAlias

from ..base import logger
from ..exceptions import DirectoryStateUnmatchedError, Unreachable

NORMAL_IMAGE: Final = "normal_image"
NORMAL_EPISODE_DIRECTORY: Final = "normal_episode_directory"
NORMAL_WEBTOON_DIRECTORY: Final = "normal_webtoon_directory"

MERGED_IMAGE: Final = "merged_image"
MERGED_EPISODE_DIRECTORY: Final = "merged_episode_directory"
MERGED_WEBTOON_DIRECTORY: Final = "merged_webtoon_directory"

WEBTOON_DIRECTORY: Final = "webtoon_directory"
# 만약 이름을 WEBTOONS_DIRECTORY로 한다면 매우 햇갈릴 가능성이 높기에 대신 WEBTOON_DIRECTORY_CONTAINER라는 이름을 사용함
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


# fmt: off
DIRECTORY_PATTERNS: dict[FileStates, re.Pattern[str]] = {
    # 023.jpg
    NORMAL_IMAGE: re.compile(r"^(?P<image_no>\d{3})[.](?P<extension>[a-zA-Z0-9]{3,4})$"),
    # 0001. episode_name
    NORMAL_EPISODE_DIRECTORY: re.compile(r"^(?P<episode_no>\d{4})\. (?P<episode_name>.+)$"),
    # 0001.001. episode_name.jpg
    MERGED_IMAGE: re.compile(r"^(?P<episode_no>\d{4})[.](?P<image_no>\d{3})[.] (?P<episode_name>.+)[.](?P<extension>[a-zA-Z]{3,4})$"),
    # 0001~0005
    MERGED_EPISODE_DIRECTORY: re.compile(r"^(?P<from>\d{4})~(?P<to>\d{4})$"),
    # webtoon_name(webtoon_id[, HD][, shuffled])
    WEBTOON_DIRECTORY: re.compile(r"^(?P<webtoon_name>.+)[(](?P<webtoon_id>.+?)(?:, (?:HD|shuffled|concatenated))*[)]$"),
}
DIRECTORY_PATTERNS_TOLERANT: dict[FileStates, re.Pattern[str]] = {
    # 023.jpg
    NORMAL_IMAGE: re.compile(r"^(?P<image_no>\d+)[.](?P<extension>[a-zA-Z0-9]+)$"),
    # 0001. episode_name
    NORMAL_EPISODE_DIRECTORY: re.compile(r"^(?P<episode_no>\d+)\. (?P<episode_name>.+)$"),
    # 0001.001. episode_name.jpg
    MERGED_IMAGE: re.compile(r"^(?P<episode_no>\d+)[.](?P<image_no>\d+)[.] (?P<episode_name>.+)[.](?P<extension>[a-zA-Z]+)$"),
    # 0001~0005
    MERGED_EPISODE_DIRECTORY: re.compile(r"^(?P<from>\d+)~(?P<to>\d+)$"),
    # webtoon_name(webtoon_id[, meta]*)
    WEBTOON_DIRECTORY: re.compile(r"^(?P<webtoon_name>.+)[(](?P<webtoon_id>.+?)(?:, (?:\w+))*[)]$"),
}
# fmt: on


def _directories_and_files_of(
    directory: PathOrStr,
    treat_underscored_directories_as_file: bool = True,
    /,
) -> tuple[list[Path], list[Path]]:
    directories: list[Path] = []
    files: list[Path] = []
    for path in Path(directory).iterdir():
        is_underscored = (
            treat_underscored_directories_as_file and path.name.startswith("_") and not path.name.startswith("__")
        )
        if path.is_dir() and not is_underscored:
            directories.append(path)
        else:
            files.append(path)
    return sorted(directories), sorted(files)


def select_from_directory(
    source_parent_directory: Path,
    target_parent_directory: Path | None,
    rebuild_webtoon_viewer: bool,
    merge_number: int | None = None,
) -> None:
    directories, files = _directories_and_files_of(source_parent_directory, False)

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
        logger.warning("There's no webtoon directories.")
        return

    options: dict[int, str | Path] = {}
    i = 1
    if len(normal_webtoon_directories) > 1:
        print(f"{i:0{number_length}}. Merge every {len(normal_webtoon_directories)} normal webtoons.")
        options[i] = "merge_all"
        i += 1
    for normal_webtoon_directory in normal_webtoon_directories:
        print(f"{i:0{number_length}}. Merge {normal_webtoon_directory.name}")
        options[i] = normal_webtoon_directory
        i += 1
    if len(normal_webtoon_directories) > 1 and len(merged_webtoon_directories) > 1:
        print("=" * 20)
    if len(merged_webtoon_directories) > 1:
        print(f"{i:0{number_length}}. Restore every {len(merged_webtoon_directories)} merged webtoons.")
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
            print(f"(Directory {not_webtoon_directories[0].name} is hidden because it's not a webtoon directory.)")
        case _:
            print(f"({len(not_webtoon_directories)} directories are hidden because they are not webtoon directories.)")

    choice = input("Enter number: ")
    try:
        selected = options[int(choice)]
    except (IndexError, ValueError) as e:
        raise ValueError("User input is invalid.") from e

    def get_merge_number():
        # 혹시 merge_number가 0일 경우를 대비해 is None 사용.
        return int(input("merge number: ")) if merge_number is None else merge_number

    operated_paths: list[Path] = []
    match selected:
        case "merge_all":
            merge_number = get_merge_number()
            for normal_webtoon_directory in normal_webtoon_directories:
                logger.info(f"Merging {normal_webtoon_directory.name}...")
                operated_paths.append(normal_webtoon_directory)
                merge_webtoon(
                    normal_webtoon_directory,
                    target_parent_directory and target_parent_directory / normal_webtoon_directory.name,
                    merge_number,
                )
        case "restore_all":
            for merged_webtoon_directory in merged_webtoon_directories:
                logger.info(f"Restoring {merged_webtoon_directory.name}...")
                operated_paths.append(merged_webtoon_directory)
                restore_webtoon(
                    merged_webtoon_directory,
                    target_parent_directory and target_parent_directory / merged_webtoon_directory.name,
                )
        case path:
            assert not isinstance(path, str)
            # check_container_state를 두 번 하는 게 비효율적일 수 있음.
            container_state = check_container_state(path)
            operated_paths.append(path)

            if container_state == NORMAL_WEBTOON_DIRECTORY:
                merge_number = get_merge_number()
                logger.info(f"Merging {path.name}...")
                merge_webtoon(
                    path,
                    target_parent_directory and target_parent_directory / path.name,
                    merge_number,
                )
            elif container_state == MERGED_WEBTOON_DIRECTORY:
                logger.info(f"Restoring {path.name}...")
                restore_webtoon(
                    path,
                    target_parent_directory and target_parent_directory / path.name,
                )
            else:
                # container_state는 기존에 다 확인하고 저 두 상태 중 하나가 보장된 상태이기에
                # 여기에 걸릴 확률은 없음.
                raise Unreachable()

    if rebuild_webtoon_viewer:
        # webtoon_viewer 모듈이 이 모듈을 의존하고 있기에 시작 시 import가 불가함.
        from ._webtoon_viewer import add_html_webtoon_viewer

        for operated_path in operated_paths:
            if (operated_path / "webtoon.html").exists():
                add_html_webtoon_viewer(operated_path)


def merge_or_restore_webtoon(
    source_webtoon_directory: Path,
    target_webtoon_directory: Path | None,
    merge_number: int,
    action: Literal["merge", "restore", "auto"],
):
    def get_merge_number():
        # 혹시 merge_number가 0일 경우를 대비해 is None 사용.
        return int(input("merge number: ")) if merge_number is None else merge_number

    if action == "auto":
        container_state = check_container_state(source_webtoon_directory)
    elif action == "merge":
        container_state = NORMAL_WEBTOON_DIRECTORY
    elif action == "restore":
        container_state = MERGED_WEBTOON_DIRECTORY
    else:
        raise ValueError(f"Invalid action: {action}")

    if container_state == NORMAL_WEBTOON_DIRECTORY:
        merge_number = get_merge_number()
        logger.info(f"Merging {source_webtoon_directory.name}...")
        merge_webtoon(
            source_webtoon_directory,
            target_webtoon_directory and target_webtoon_directory / source_webtoon_directory.name,
            merge_number,
        )
    elif container_state == MERGED_WEBTOON_DIRECTORY:
        logger.info(f"Restoring {source_webtoon_directory.name}...")
        restore_webtoon(
            source_webtoon_directory,
            target_webtoon_directory and target_webtoon_directory / source_webtoon_directory.name,
        )
    else:
        raise DirectoryStateUnmatchedError.from_state(container_state, source_webtoon_directory)


def _get_episode_no(directory_name: str) -> int:
    directory_name_matched = DIRECTORY_PATTERNS[NORMAL_EPISODE_DIRECTORY].match(directory_name)
    assert directory_name_matched is not None, f"Directory state is invalid. {directory_name = }"
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

    directory_state = manual_directory_state or check_container_state(source_webtoon_directory)
    if directory_state != NORMAL_WEBTOON_DIRECTORY:
        raise DirectoryStateUnmatchedError(
            f"State of directory is {directory_state}, which cannot be merged."
            + (" Maybe what you need was restore_webtoon." if directory_state == MERGED_WEBTOON_DIRECTORY else "")
            + f"\nsource webtoon directory: {source_webtoon_directory}"
        )

    # source_webtoon_directory == target_webtoon_directory인 경우 때문에 exist_ok는 True여야 한다.
    target_webtoon_directory.mkdir(parents=True, exist_ok=True)

    directories, files = _directories_and_files_of(source_webtoon_directory)

    # 디렉토리 그룹핑
    grouped_directories: defaultdict[int, list[Path]] = defaultdict(list)
    for directory in directories:
        episode_no = _get_episode_no(directory.name)
        grouped_directories[(episode_no - 1) // merge_number].append(directory)

    # 마지막 번들 묶기
    last_bundle = max(grouped_directories)
    if merge_last_bundle and len(grouped_directories[last_bundle]) < merge_number and len(grouped_directories) > 1:
        last_bundle_items = grouped_directories.pop(last_bundle)
        grouped_directories[max(grouped_directories)] += last_bundle_items

    # 그루핑 끝난 디렉토리들 실제로 옮김
    for directories in grouped_directories.values():
        # 디렉토리명 만듦
        episode_no_range = sorted(_get_episode_no(directory.name) for directory in directories)
        new_directory_name = f"{episode_no_range[0]:04d}~{episode_no_range[-1]:04d}"
        target_episode_directory = target_webtoon_directory / new_directory_name
        target_episode_directory.mkdir()

        for directory in directories:
            for image_name in os.listdir(directory):
                merged_name = _get_merged_image_name(image_name, directory.name)
                os.rename(directory / image_name, target_episode_directory / merged_name)
            directory.rmdir()

    # 남은 폴더가 아닌 파일들 옮기기
    if source_webtoon_directory != target_webtoon_directory and files:
        for file in files:
            os.rename(file, target_webtoon_directory / file.name)
        if not os.listdir(source_webtoon_directory):
            source_webtoon_directory.rmdir()


def _get_merged_image_name(image_name: str, episode_name: str) -> str:
    """merged 상태의 image가 가져야 할 이름을 내놓습니다."""
    image_name_processed: re.Match[str] | None = DIRECTORY_PATTERNS[NORMAL_IMAGE].match(image_name)
    episode_name_processed: re.Match[str] | None = DIRECTORY_PATTERNS[NORMAL_EPISODE_DIRECTORY].match(episode_name)
    if not episode_name_processed:
        if DIRECTORY_PATTERNS[MERGED_EPISODE_DIRECTORY].match(episode_name):
            raise ValueError(
                "Episode name is not valid. It's because you tried to merge already merged webtoon directory."
            )
        raise ValueError(f"Episode name is not valid. Episode name: {episode_name}")
    if not image_name_processed:
        raise ValueError(f"Image name is not valid. Image name: {image_name}")

    image_no = image_name_processed.group("image_no")
    image_extension = image_name_processed.group("extension")
    episode_no = episode_name_processed.group("episode_no")
    episode_name = episode_name_processed.group("episode_name")

    return f"{episode_no}.{image_no}. {episode_name}.{image_extension}"


############### CHECKING FUNCTIONALITY ###############


def check_filename_state(file_or_directory_name: str) -> FileStates:
    """한 파일(혹은 디렉토리) 이름의 상태를 확인합니다."""
    # sourcery skip: use-next; for simplicity and extensibility, I decide to not apply 'use-next'
    for state_name, regex in DIRECTORY_PATTERNS.items():
        if regex.match(file_or_directory_name):
            return state_name
    return NOT_MATCHED


def check_container_state(directory: PathOrStr, *, warn: bool = False) -> ContainerStates:
    """해당 path에 있는 디렉토리의 상태를 확인합니다."""
    directory = Path(directory)
    if not directory.exists():
        if warn:
            logger.warning(f"It looks like the directory({directory}) doesn't exist.")
        return NOT_MATCHED

    if directory.is_file():
        if warn:
            logger.warning(f"It looks like the file({directory}) is not a directory.")
        return NOT_MATCHED

    directories, files = _directories_and_files_of(directory)

    if not directories:
        states: set[FileStates] = {check_filename_state(file.name) for file in files if not file.name.startswith("_")}
        if len(states) == 1:
            return FILE_TO_CONTAINER.get(states.pop(), NOT_MATCHED)
        return NOT_MATCHED

    for state_name, regex in DIRECTORY_PATTERNS.items():
        # 매치되지 '않은' 것의 개수를 세는 것을 주의!!!
        if not sum(not regex.match(episode_or_image.name) for episode_or_image in directories):
            return FILE_TO_CONTAINER.get(state_name, NOT_MATCHED)

    return NOT_MATCHED


def guess_merge_number(webtoon_directory: Path) -> int | None:
    """웹툰 디렉토리가 어떤 값으로 묶였는지 추측합니다. 에피소드 일부가 다운로드되지 않았더라도 그럭저럭 잘 찾아낼 수 있습니다."""
    directories, _ = _directories_and_files_of(webtoon_directory)
    regex = DIRECTORY_PATTERNS[MERGED_EPISODE_DIRECTORY]
    counter = defaultdict(int)
    for directory in directories:
        matched = regex.match(directory.name)
        if not matched:
            continue

        try:
            diff = int(matched["to"]) - int(matched["from"])
        except ValueError:
            continue
        else:
            counter[diff] += 1

    most_occurred_value = max(counter.values())
    if not most_occurred_value:
        # raise ValueError(f"Can't guess merge number of {webtoon_directory}. Maybe it's not merged directory?")
        return None
    most_occurred = next(key for key, value in counter.items() if value == most_occurred_value)
    return most_occurred


############### RESTORE FUNCTIONALITY ###############


def restore_name(merged_image_name: str):
    image_info = DIRECTORY_PATTERNS[MERGED_IMAGE].match(merged_image_name)
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

    directory_state = manual_directory_state or check_container_state(source_webtoon_directory)
    if directory_state != MERGED_WEBTOON_DIRECTORY:
        raise DirectoryStateUnmatchedError(
            f"State of directory is {directory_state}, which cannot be restored."
            + (" Maybe what you need was merge_webtoon." if directory_state == NORMAL_WEBTOON_DIRECTORY else "")
            + f"\nsource webtoon directory: {source_webtoon_directory}"
        )

    directories, files = _directories_and_files_of(source_webtoon_directory)
    for directory in directories:
        for image_name in os.listdir(directory):
            target_episode_directory_name, target_image_name = restore_name(image_name)
            target_episode_directory = target_webtoon_directory / target_episode_directory_name
            target_episode_directory.mkdir(exist_ok=True)
            os.rename(directory / image_name, target_episode_directory / target_image_name)
        directory.rmdir()

    # 남은 폴더가 아닌 파일들 옮기기
    if source_webtoon_directory != target_webtoon_directory and files:
        for file in files:
            os.rename(file, target_webtoon_directory / file.name)
        if not os.listdir(source_webtoon_directory):
            source_webtoon_directory.rmdir()


def ensure_normal(
    source_webtoon_directory: Path,
    empty_ok: bool,
    allow_unknown_state: bool = False,
    manual_container_state: ContainerStates | None = None,
    mkdir_if_empty: bool = True,
) -> bool:
    """웹툰 디렉토리가 merge되어 있다면 되돌리고 아니라면 그대로 둡니다. 디렉토리가 merge되어 있었다면 True, 아니라면 False를 리턴합니다."""
    if source_webtoon_directory.exists() and os.listdir(source_webtoon_directory):
        if manual_container_state is None:
            container_state = check_container_state(source_webtoon_directory)
        else:
            container_state = manual_container_state

        if container_state == MERGED_WEBTOON_DIRECTORY:
            logger.warning("Webtoon directory was merged. Restoring...")
            restore_webtoon(source_webtoon_directory, None)
            return True
        elif container_state != NORMAL_WEBTOON_DIRECTORY and allow_unknown_state:
            raise DirectoryStateUnmatchedError.from_state(container_state, source_webtoon_directory)
    elif not empty_ok:
        raise ValueError(f"The directory was empty. Directory: {source_webtoon_directory}")
    elif mkdir_if_empty:
        source_webtoon_directory.mkdir(parents=True, exist_ok=True)

    return False


@contextmanager
def restore_after_finished(
    source_webtoon_directory: Path,
    empty_ok: bool,
    allow_unknown_state: bool = False,
    manual_container_state: ContainerStates | None = None,
    mkdir_if_empty: bool = True,
):
    merge_number = guess_merge_number(source_webtoon_directory)
    is_restored = ensure_normal(
        source_webtoon_directory=source_webtoon_directory,
        empty_ok=empty_ok,
        allow_unknown_state=allow_unknown_state,
        manual_container_state=manual_container_state,
        mkdir_if_empty=mkdir_if_empty,
    )
    if bool(merge_number) ^ is_restored:
        logger.warning(f"Two values are different each other: {bool(merge_number)=}, {is_restored=}")

    yield

    if merge_number:
        merge_webtoon(source_webtoon_directory, None, merge_number=merge_number)
