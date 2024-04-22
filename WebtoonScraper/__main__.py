from __future__ import annotations

import argparse
import contextlib
import functools
import logging
import os
import re
import sys
from argparse import ArgumentParser, Namespace
from collections.abc import Sequence
from importlib.resources import files
from pathlib import Path
from typing import Any, Callable, Literal

from rich.console import Console
from rich.table import Table

import WebtoonScraper
from WebtoonScraper import __version__, webtoon
from WebtoonScraper.directory_merger import (
    MERGED_WEBTOON_DIRECTORY,
    NORMAL_WEBTOON_DIRECTORY,
    ContainerStates,
    check_container_state,
    merge_webtoon,
    restore_webtoon,
    select_from_directory,
)
from WebtoonScraper.exceptions import DirectoryStateUnmatchedError
from WebtoonScraper.miscs import EpisodeNoRange, WebtoonId, logger
from WebtoonScraper.scrapers import CommentsDownloadOption

# currently Lezhin uses only lower case alphabet, numbers, and underscore. Rest of them are added for just in case.
ACCEPTABLE_CHARS = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_")


def _to_webtoon_id(webtoon_id: str) -> WebtoonId:
    """CLI로 입력된 문자열 webtoon ID를 실재하는 타입이 있는 webtoon ID로 변경합니다.

    Arguments:
        webtoon_id: 실재하는 webtoon ID로 변경할 문자열입니다.

    Raises:
        ValueError: webtoon ID로 해석될 수 없는 문자열이 webtoon_id를 통해 전달되었을 때 발현합니다.

    Returns:
        WebtoonId 타입을 리턴합니다.
    """

    # URL인 경우
    if "." in webtoon_id:
        return webtoon_id

    if webtoon_id.isdigit():
        # all others
        return int(webtoon_id)
    if all(char in ACCEPTABLE_CHARS for char in webtoon_id):
        # Lezhin
        return webtoon_id
    if "," not in webtoon_id:
        raise ValueError(f"Failed to interpret webtoon ID: `{webtoon_id}`")

    match_result = re.match(
        r""" *[(]? *(?P<id1>['"]?.+?['"]?) *, *(?P<id2>['"]?.+?['"]?) *[)]? *$""",
        webtoon_id,
    )
    if not match_result:
        raise ValueError(f"Failed to interpret webtoon ID: `{webtoon_id}`")

    id1 = match_result["id1"]
    id2 = match_result["id2"]

    if id1.isdigit() and id2.isdigit():
        # 네이버 포스트
        return int(id1), int(id2)
    elif id2.isdigit():
        # 네이버 블로그
        return id1, int(id2)

    # quote 제거
    if id1[0] == id1[-1] == "'" or id1[0] == id1[-1] == '"':
        id1 = id1[1:-1]
    elif id2[0] == id2[-1] == "'" or id2[0] == id2[-1] == '"':
        id2 = id2[1:-1]

    # 티스토리
    return id1, id2


def _to_range(episode_no_range: str) -> EpisodeNoRange:
    """CLI로 입력된 문자열로 된 웹툰 회차 범위를 실재적인 타입으로 변환합니다."""

    def nonesafe_int(value):
        return int(value) if value and value.lower() != "none" else None

    with contextlib.suppress(ValueError):
        return int(episode_no_range)

    start, end = (nonesafe_int(i.strip()) for i in episode_no_range.split("~"))

    return start, end


class LazyVersionAction(argparse._VersionAction):
    version: Callable[[], str] | str | None
    def __call__(self, parser: ArgumentParser, namespace: Namespace, values: str | Sequence[Any] | None, option_string: str | None = None) -> None:
        if callable(self.version):
            self.version = self.version()
        return super().__call__(parser, namespace, values, option_string)


def _version_info() -> str:
    def check_imported():
        ALL_DEPENDENCIES = {"naver_post": "Naver Post", "lezhin_comics": "Lezhin Comics (partially)", "kakao_webtoon": "Kakao Webtoon"}
        installed = set()

        with contextlib.suppress(Exception):
            import demjson3
            installed.add("naver_post")

        with contextlib.suppress(Exception):
            from PIL import Image
            installed.add("lezhin_comics")

        with contextlib.suppress(Exception):
            from Cryptodome.Cipher import AES
            installed.add("kakao_webtoon")

        missing_dependencies = ALL_DEPENDENCIES.keys() - installed
        match len(missing_dependencies):
            case 0:
                return "✅ Every extra dependencies are installed!"

            case 1:
                missing = missing_dependencies.pop()
                return (
                    f"⚠️  Extra dependency '{missing}' is not installed. "
                    f"You won't be able to download webtoons from {ALL_DEPENDENCIES[missing]}."
                )

            case _:
                SEP = "', '"
                return (
                    f"⚠️  Extra dependencies '{SEP.join(missing_dependencies)}' are not installed.\n"
                    "You won't be able to download webtoons from following platforms: "
                    f"'{SEP.join(ALL_DEPENDENCIES[missing] for missing in missing_dependencies)}'."
                )

    return f"WebtoonScraper {__version__} of Python {sys.version} at {str(files(WebtoonScraper))}\n{check_imported()}"

parser = argparse.ArgumentParser(
    prog="WebtoonScraper",
    usage="Download or merge webtoons in CLI",
    description="Download webtoons with ease!",
    formatter_class=argparse.RawTextHelpFormatter,
)
parser.register('action', 'version', LazyVersionAction)

parser.add_argument("--mock", action="store_true", help="No actual action.")
parser.add_argument(
    "--version",
    action="version",
    version=_version_info,  # type: ignore
)
parser.add_argument(
    "-v",
    "--verbose",
    action="store_true",
    help="Set logger level to INFO and show detailed error.",
)
subparsers = parser.add_subparsers(title="Commands", help="Choose command you want.")

# 'download' subparsers
download_subparser = subparsers.add_parser("download", help="Download webtoons.")
download_subparser.set_defaults(subparser_name="download")
download_subparser.add_argument(
    "webtoon_ids",
    type=_to_webtoon_id,
    metavar="webtoon_ids",
    help="Webtoon ID or URL.",
    nargs="+",
)
download_subparser.add_argument(
    "-p",
    "--platform",
    type=lambda x: str(x).lower(),
    metavar="webtoon_platform",
    choices=set(webtoon.PLATFORMS) | set(webtoon.SHORT_NAMES),
    help="Webtoon platform to download. No need to specify if you don't want to. "
    f"All choices: {', '.join(f'{webtoon.SHORT_NAMES[short_name]}({short_name})' for short_name in webtoon.SHORT_NAMES)}",
)
download_subparser.add_argument(
    "-m",
    "--merge-number",
    type=int,
    metavar="merge_number",
    help="Merge number when you want to merge directories. Don't specify if you don't want to merge.",
)
download_subparser.add_argument(
    "--cookie",
    type=str,
    metavar="cookie",
    help="Set cookie when you download Bufftoon.",
)
download_subparser.add_argument(
    "--bearer",
    type=str,
    metavar="bearer",
    help="Set bearer when you download Lezhin.",
)
download_subparser.add_argument(
    "-r",
    "--range",
    type=_to_range,
    metavar="[start]~[end]",
    help="Episode number range you want to download.",
)
download_subparser.add_argument(
    "-d",
    "--download-directory",
    type=Path,
    metavar="directory",
    default="webtoon",
    help="The directory you want to download to.",
)
download_subparser.add_argument("--list-episodes", action="store_true", help="List all episodes.")
download_subparser.add_argument(
    "--get-paid-episode",
    action="store_true",
    help="Get paid episode. Lezhin Comics only.",
)
download_subparser.add_argument(
    "-c",
    "--comments",
    "--comment",
    metavar="option",
    help="Download comments.",
    nargs="*",
    choices=["all", "reply"],
)

merge_subparser = subparsers.add_parser("merge", help="Merge/Restore webtoon directory.")
merge_subparser.set_defaults(subparser_name="merge")
merge_subparser.add_argument(
    "webtoons_directory_name",
    type=str,
    metavar="webtoons_directory_name",
    help="The name of folder that contains webtoon folders to merge or restore.",
)
merge_subparser.add_argument(
    "-m",
    "--merge-number",
    type=int,
    metavar="merge_number",
    default=None,
    help="Merge number when merge.",
)
merge_subparser.add_argument(
    "-t",
    "--target-parent-directory",
    type=Path,
    metavar="target_parent_directory",
    default=None,
    help="The directory that the result of merge/restore will be located. Defaults to source directory itself.",
)


def parse_download(args: argparse.Namespace) -> None:
    # 축약형 플랫폼명을 일반적인 플랫폼명으로 변환 (nw -> naver_webtoon)
    args.platform = webtoon.SHORT_NAMES.get(args.platform, args.platform)

    for webtoon_id in args.webtoon_ids:
        # 만약 다른 타입의 튜플인데 NAVER_BLOG라면 자동으로 (str, int)로 변환한다.
        if args.platform == webtoon.NAVER_BLOG and isinstance(webtoon_id[0], int):
            webtoon_id = str(webtoon_id[0]), int(webtoon_id[1])

        # 만약 다른 타입의 튜플인데 TISTORY라면 자동으로 (str, str)로 변환한다.
        if args.platform == webtoon.TISTORY and isinstance(webtoon_id[0], int):
            webtoon_id = str(webtoon_id[0]), str(webtoon_id[1])

        if args.comments is None:
            # 사용자가 -c 옵션을 넘기지 않았다면 옵션을 None으로 둠.
            comment_download_option = None
        else:
            options = set(args.comments)
            comment_download_option = CommentsDownloadOption(
                top_comments_only="all" not in options,
                reply="reply" in options,
            )

        scraper = webtoon.setup_instance(
            webtoon_id,
            args.platform,
            cookie=args.cookie,
            bearer=args.bearer,
            download_directory=args.download_directory,
            get_paid_episode=args.get_paid_episode,
            comments_option=comment_download_option,
        )

        if args.list_episodes:
            scraper.list_episodes()
            return

        scraper.download_webtoon(
            args.range,
            merge_number=args.merge_number,
            add_viewer=True,
        )


CONTAINER_STATE_PER_ARGS: dict[str, ContainerStates] = {
    "m": NORMAL_WEBTOON_DIRECTORY,
    "merge": NORMAL_WEBTOON_DIRECTORY,
    "r": MERGED_WEBTOON_DIRECTORY,
    "restore": MERGED_WEBTOON_DIRECTORY,
}

ABBR_TO_FULL_STATE: dict[str, Literal["merge", "restore", "auto"]] = {
    "m": "merge",
    "r": "restore",
    "a": "auto",
}


CONTAINER_STATE_TO_DO_STATE: dict[ContainerStates, Literal["merge", "restore"]] = {
    NORMAL_WEBTOON_DIRECTORY: "merge",
    MERGED_WEBTOON_DIRECTORY: "restore",
}


def get_state(source_directory: Path) -> ContainerStates:
    states: dict[Path, ContainerStates] = {
        webtoon_directory: check_container_state(webtoon_directory) for webtoon_directory in source_directory.iterdir()
    }
    all_unique_states = set(states.values())
    if len(all_unique_states) != 1:
        raise ValueError(
            "All webtoons in source directory should have same state when using 'auto' action.\n"
            "Please specify --action(-a) or check directory state."
            f"States: {all_unique_states}"
        )

    (directories_state,) = all_unique_states
    return directories_state


def get_string_todo(state: ContainerStates) -> Literal["merge", "restore"]:
    try:
        return CONTAINER_STATE_TO_DO_STATE[state]
    except KeyError:
        raise ValueError(f"State {state} is not supported.")


def list_directories(parent_directory: Path) -> None:
    table = Table(show_header=True, header_style="bold blue", box=None)
    table.add_column("Webtoon Directory Name", style="bold")
    table.add_column("Directory State")
    table.add_column("Action If Auto")
    for webtoon_directory in parent_directory.iterdir():
        directory_state = check_container_state(webtoon_directory)
        table.add_row(
            webtoon_directory.name,
            directory_state,
            CONTAINER_STATE_TO_DO_STATE.get(directory_state),
        )
    Console().print(table)


def parse_merge(args: argparse.Namespace) -> None:
    select_from_directory(
        args.webtoons_directory_name,
        args.target_parent_directory,
        True,
        args.merge_number,
    )


def main(argv=None) -> Literal[0, 1]:
    """모든 CLI 명령어를 처리하는 함수입니다.

    Arguments:
        argv: 커맨드라인 명령어입니다. None이라면 sys.argv[1:]를 값으로 삼습니다.

    Returns:
        정상적으로 프로그램이 종료했다면 0을, 비정상적으로 종료되었다면 1을 반환합니다.

    Raises:
        이 함수는 KeyboardInterrupt를 제외한 어떠한 오류도 발생시키지 않습니다.
        그 대신 성공했을 때는 0을, 실패했을 때에는 1을 반환합니다.
    """
    args = parser.parse_args(argv)  # 주어진 argv가 None이면 sys.argv[1:]을 기본값으로 삼음

    # --mock 인자가 포함된 경우 실제 다운로드까지 가지 않고 표현된 인자를 보여주고 종료.
    if args.mock:
        print("Arguments:", str(args).removeprefix("Namespace(").removesuffix(")"))
        return 0

    # 어떠한 command도 입력하지 않았을 경우 도움말을 표시함.
    if not hasattr(args, "subparser_name"):
        return main(argv=["--help"])

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    try:
        if args.subparser_name == "download":
            parse_download(args)
        elif args.subparser_name == "merge":
            parse_merge(args)
        else:
            raise NotImplementedError(f"Subparser {args.subparser_name} is not implemented.")
    except BaseException as e:
        logger.error(f"{type(e).__name__}: {e}")
        if args.verbose:
            Console().print_exception()
        return 1
    else:
        return 0


if __name__ == "__main__":
    sys.exit(main())
