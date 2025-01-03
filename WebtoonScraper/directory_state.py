"""웹툰 디렉토리의 상태를 파악합니다."""

from __future__ import annotations

from contextlib import suppress
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Final, Literal, TypeAlias

from .base import logger

NORMAL_IMAGE: Final = "normal_image"
NORMAL_EPISODE_DIRECTORY: Final = "normal_episode_directory"
NORMAL_WEBTOON_DIRECTORY: Final = "normal_webtoon_directory"

MERGED_IMAGE: Final = "merged_image"
MERGED_EPISODE_DIRECTORY: Final = "merged_episode_directory"
MERGED_WEBTOON_DIRECTORY: Final = "merged_webtoon_directory"

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
PathOrStr = str | Path

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


def load_information_json(directory: Path) -> dict | None:
    information = directory / "information.json"
    with suppress(Exception):
        with open(information, encoding="utf-8") as f:
            return json.load(f)

    snapshot = directory.parent / f"{directory.name}.snapshots"
    with suppress(Exception):
        with open(snapshot, encoding="utf-8") as f:
            data = json.load(f)
        latest_snapshot_no = data["selected_snapshots"][-1]
        snapshot = data["snapshots"][latest_snapshot_no]
        metadata = snapshot["meta"]
        return metadata

    return None


def check_filename_state(file_or_directory_name: str) -> FileStates:
    """한 파일(혹은 디렉토리) 이름의 상태를 확인합니다."""
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
