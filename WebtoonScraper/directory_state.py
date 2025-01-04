"""웹툰 디렉토리의 상태를 파악합니다."""

from __future__ import annotations

import json
import re
import typing
from collections import defaultdict
from contextlib import suppress
from pathlib import Path

from fieldenum import Variant, fieldenum

from WebtoonScraper.base import logger

PathOrStr = str | Path


# @typing.dataclass_transform()
@fieldenum
class DirectoryState:
    if typing.TYPE_CHECKING:
        class NotMatched(DirectoryState):  # type: ignore
            resumable: bool | None

            def __init__(self, resumable: bool | None): ...
            def to_container(self, default: DirectoryState | None = None) -> DirectoryState: ...
            def is_container(self) -> bool: ...
            def pattern(self, tolerant: bool = False) -> re.Pattern[str]: ...

        class Image(DirectoryState):  # type: ignore
            is_merged: bool

            def __init__(self, is_merged: bool): ...
            def to_container(self, default: DirectoryState | None = None) -> DirectoryState: ...
            def is_container(self) -> bool: ...
            def pattern(self, tolerant: bool = False) -> re.Pattern[str]: ...

        class EpisodeDirectory(DirectoryState):  # type: ignore
            is_merged: bool | None

            def __init__(self, is_merged: bool | None): ...
            def to_container(self, default: DirectoryState | None = None) -> DirectoryState: ...
            def is_container(self) -> bool: ...
            def pattern(self, tolerant: bool = False) -> re.Pattern[str]: ...

        class WebtoonDirectory(DirectoryState):  # type: ignore
            is_merged: bool | None

            def __init__(self, is_merged: bool | None): ...
            def to_container(self, default: DirectoryState | None = None) -> DirectoryState: ...
            def is_container(self) -> bool: ...
            def pattern(self, tolerant: bool = False) -> re.Pattern[str]: ...

        class WebtoonDirectoryContainer(DirectoryState):  # type: ignore
            def __init__(self): ...
            def to_container(self, default: DirectoryState | None = None) -> DirectoryState: ...
            def is_container(self) -> bool: ...
            def pattern(self, tolerant: bool = False) -> re.Pattern[str]: ...

    else:
        NotMatched = Variant(resumable=bool | None)
        Image = Variant(is_merged=bool)
        EpisodeDirectory = Variant(is_merged=bool | None)
        WebtoonDirectory = Variant(is_merged=bool | None)
        WebtoonDirectoryContainer = Variant()

    # fmt: off
    PATTERNS: typing.ClassVar = (
        (re.compile(r"^(?P<image_no>\d{3})[.](?P<extension>[a-zA-Z0-9]{3,4})$"), re.compile(r"^(?P<image_no>\d+)[.](?P<extension>[a-zA-Z0-9]+)$")),
        (re.compile(r"^(?P<episode_no>\d{4})\. (?P<episode_name>.+)$"), re.compile(r"^(?P<episode_no>\d+)\. (?P<episode_name>.+)$")),
        (re.compile(r"^(?P<episode_no>\d{4})[.](?P<image_no>\d{3})[.] (?P<episode_name>.+)[.](?P<extension>[a-zA-Z]{3,4})$"), re.compile(r"^(?P<episode_no>\d+)[.](?P<image_no>\d+)[.] (?P<episode_name>.+)[.](?P<extension>[a-zA-Z]+)$")),
        (re.compile(r"^(?P<from>\d{4})~(?P<to>\d{4})$"), re.compile(r"^(?P<from>\d+)~(?P<to>\d+)$")),
        (re.compile(r"^(?P<webtoon_name>.+)[(](?P<webtoon_id>.+?)(?:, (?:HD|shuffled|concatenated))*[)]$"), re.compile(r"^(?P<webtoon_name>.+)[(](?P<webtoon_id>.+?)(?:, (?:\w+))*[)]$")),
    )
    # fmt: on

    def to_container(self, default: DirectoryState | None = None) -> DirectoryState:
        match self:
            case DirectoryState.Image(is_merged=is_merged):
                return DirectoryState.EpisodeDirectory(is_merged=is_merged)
            case DirectoryState.EpisodeDirectory(is_merged=is_merged):
                return DirectoryState.WebtoonDirectory(is_merged=is_merged)
            case DirectoryState.WebtoonDirectory(is_merged=is_merged):
                return DirectoryState.WebtoonDirectoryContainer()
            case _ if default is not None:
                return default
            case other:
                raise ValueError(f"{other} is not a content state.")

    def is_container(self) -> bool:
        match self:
            case (
                DirectoryState.EpisodeDirectory(),
                DirectoryState.WebtoonDirectory(),
                DirectoryState.WebtoonDirectoryContainer(),
            ):
                return True
            case _:
                return False

    def pattern(self, tolerant: bool = False) -> re.Pattern[str]:
        match self:
            case DirectoryState.Image(is_merged=False):
                return self.PATTERNS[0][tolerant]
            case DirectoryState.EpisodeDirectory(is_merged=False):
                return self.PATTERNS[1][tolerant]
            case DirectoryState.Image(is_merged=True):
                return self.PATTERNS[2][tolerant]
            case DirectoryState.EpisodeDirectory(is_merged=True):
                return self.PATTERNS[3][tolerant]
            case DirectoryState.WebtoonDirectory():
                return self.PATTERNS[4][tolerant]
            case _:
                raise ValueError(f"{self} is not a container state.")


DIRECTORY_STATES = (
    DirectoryState.Image(is_merged=False),
    DirectoryState.Image(is_merged=True),
    DirectoryState.EpisodeDirectory(is_merged=False),
    DirectoryState.EpisodeDirectory(is_merged=True),
    DirectoryState.WebtoonDirectory(is_merged=None),
)


def _directories_and_files_of(
    directory: PathOrStr,
    treat_underscored_directories_as_file: bool = True,
    ignore_snapshot: bool = True,
) -> tuple[list[Path], list[Path]]:
    directories: list[Path] = []
    files: list[Path] = []
    for path in Path(directory).iterdir():
        if ignore_snapshot and path.name.endswith(".snapshots"):
            continue
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


def check_filename_state(file_or_directory_name: str) -> DirectoryState:
    """한 파일(혹은 디렉토리) 이름의 상태를 확인합니다."""
    for state in DIRECTORY_STATES:
        if state.pattern().match(file_or_directory_name):
            return state
    return DirectoryState.NotMatched(resumable=None)


def check_container_state(directory: PathOrStr, *, warn: bool = False) -> DirectoryState:
    """해당 path에 있는 디렉토리의 상태를 확인합니다."""
    directory = Path(directory)
    if not directory.exists():
        return DirectoryState.NotMatched(resumable=True)

    if directory.is_file():
        if warn:
            logger.warning(f"It looks like the file({directory}) is not a directory.")
        return DirectoryState.NotMatched(resumable=False)

    directories, files = _directories_and_files_of(directory)

    # 빈 디렉토리의 경우와 파일만 있는 경우 모두를 포괄함함
    if not directories:
        return DirectoryState.NotMatched(resumable=True)

    for state in DIRECTORY_STATES:
        # 매치되지 '않은' 것의 개수를 세니 주의!!!
        if not sum(not state.pattern().match(episode_or_image.name) for episode_or_image in directories):
            return state.to_container()

    return DirectoryState.NotMatched(resumable=None)


def guess_merge_number(webtoon_directory: Path) -> int | None:
    """웹툰 디렉토리가 어떤 값으로 묶였는지 추측합니다. 에피소드 일부가 다운로드되지 않았더라도 그럭저럭 잘 찾아낼 수 있습니다."""
    directories, _ = _directories_and_files_of(webtoon_directory)
    regex = DirectoryState.EpisodeDirectory(is_merged=True).pattern()
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
