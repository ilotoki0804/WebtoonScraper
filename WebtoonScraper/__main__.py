from __future__ import annotations

import argparse
import contextlib
import logging
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
from WebtoonScraper import __version__
from WebtoonScraper.processing import _webtoon as webtoon, concat_webtoon, BatchMode
from WebtoonScraper.processing.directory_merger import (
    NORMAL_WEBTOON_DIRECTORY,
    _directories_and_files_of,
    merge_or_restore_webtoon,
    merge_webtoon,
    select_from_directory,
)
from WebtoonScraper.base import logger
from WebtoonScraper.scrapers import EpisodeRange


class LazyVersionAction(argparse._VersionAction):
    version: Callable[[], str] | str | None

    def __call__(
        self,
        parser: ArgumentParser,
        namespace: Namespace,
        values: str | Sequence[Any] | None,
        option_string: str | None = None,
    ) -> None:
        if callable(self.version):
            self.version = self.version()
        return super().__call__(parser, namespace, values, option_string)


def _version_info() -> str:
    def check_dependency():
        ALL_DEPENDENCIES = {
            "naver_post": "download Naver Post",
            "lezhin_comics": "download Lezhin Comics (partially)",
            "kakao_webtoon": "download Kakao Webtoon",
            "concat": "use concatenation feature"
        }
        installed = set()

        # fmt: off  # 맥락상 import와 installed가 서로 붙어있는 편이 어울림

        with contextlib.suppress(Exception):
            import demjson3  # noqa
            installed.add("naver_post")

        with contextlib.suppress(Exception):
            from PIL import Image  # noqa
            installed.add("lezhin_comics")
            installed.add("concat")

        with contextlib.suppress(Exception):
            from Cryptodome.Cipher import AES  # noqa
            installed.add("kakao_webtoon")

        # fmt: on

        missing_dependencies = ALL_DEPENDENCIES.keys() - installed
        match len(missing_dependencies):
            case 0:
                return "✅ All extra dependencies are installed!"

            case 1:
                missing = missing_dependencies.pop()
                return (
                    f"⚠️  Extra dependency '{missing}' is not installed. "
                    f"You won't be able to {ALL_DEPENDENCIES[missing]}.\n"
                    "Download a missing dependency via `pip install -U WebtoonScraper[full]`"
                )

            case _:
                SEP = "', '"
                return (
                    f"⚠️  Extra dependencies '{SEP.join(missing_dependencies)}' are not installed.\n"
                    f"You won't be able to {', '.join(ALL_DEPENDENCIES[missing] for missing in missing_dependencies)}.\n"
                    "Download missing dependencies via `pip install -U WebtoonScraper[full]`"
                )

    return f"WebtoonScraper {__version__} of Python {sys.version} at {str(files(WebtoonScraper))}\n{check_dependency()}"


def _parse_options(value: str):
    try:
        key, value = value.split("=")
        return key.strip(), value.strip()
    except ValueError:
        return value.strip(), None


parser = argparse.ArgumentParser(
    prog="WebtoonScraper",
    formatter_class=argparse.RawTextHelpFormatter,
)
parser.register("action", "version", LazyVersionAction)

parser.add_argument("--mock", action="store_true", help="Print argument parsing result and exit. Exist for debug or practice purpose")
parser.add_argument(
    "--version",
    action="version",
    version=_version_info,  # type: ignore
)
parser.add_argument(
    "-v",
    "--verbose",
    action="store_true",
    help="Set logger level to DEBUG and show detailed error",
)
subparsers = parser.add_subparsers(title="Commands")

# download subparser
download_subparser = subparsers.add_parser("download", help="Download webtoons")
download_subparser.set_defaults(subparser_name="download")
download_subparser.add_argument(
    "webtoon_ids",
    help="URL or webtoon ID. You can provide multiple URLs or webtoon IDs",
    nargs="+",
)
download_subparser.add_argument(
    "-p",
    "--platform",
    type=lambda x: str(x).lower(),
    choices=("url", *webtoon.PLATFORMS),
    metavar="PLATFORM",
    default="url",
    help="Webtoon platform to download. Refer to docs to check all supported platforms. Defaults to 'url'",
)
download_subparser.add_argument(
    "-m",
    "--merge-number",
    type=int,
    help="Merge number when you want to merge directories. Don't specify if you don't want to merge",
)
download_subparser.add_argument("--cookie")
download_subparser.add_argument(
    "-r",
    "--range",
    type=EpisodeRange.from_string,
    help="Episode number range you want to download.",
)
download_subparser.add_argument(
    "-d",
    "--base-directory",
    type=Path,
    default=Path.cwd(),
    help="Where 'webtoon directory' is stored",
)
download_subparser.add_argument("--list-episodes", action="store_true", help="List all episodes")
download_subparser.add_argument(
    "-o",
    "--options",
    type=_parse_options,
    nargs="+",
    help="Additional options for scraper",
)
download_subparser.add_argument(
    "--concat",
    help="Concatenating webtoon images. Full specification is on docs",
    nargs="+",
)
download_subparser.add_argument(
    "--existing-episode",
    choices=["skip", "raise", "download_again", "hard_check"],
    default="skip",
    help="Determine what to do when episode directory already exists",
)

# merge subparser
merge_subparser = subparsers.add_parser("merge", help="Merge episode directories")
merge_subparser.set_defaults(subparser_name="merge")
merge_subparser.add_argument(
    "webtoon_directory_path",
    type=Path,
    help="A webtoon folder to merge or restore",
)
merge_subparser.add_argument(
    "-m",
    "--merge-number",
    type=int,
    metavar="merge_number",
    default=None,
    help="Merge number when merge",
)
merge_subparser.add_argument(
    "-t",
    "--target-webtoon-directory",
    type=Path,
    metavar="target_webtoon_directory",
    default=None,
    help="The destination of output webtoon directory",
)
merge_subparser.add_argument(
    "-s",
    "--select",
    action="store_true",
    help="Instead of typing the webtoon directory directly, open the webtoon directory selector",
)
merge_subparser.add_argument(
    "-a",
    "--action",
    choices={"merge", "restore", "auto"},
    default="auto",
    help=(
        "Determines whether to merge or restore the directories. "
        "The 'merge' option will merge the webtoon directory. "
        "The 'restore' option restores the webtoon directory. "
        "The 'auto' option restores the directory, "
        "merging it if it is already in the default state. "
        "Ignored if the `s` option is used"
    ),
)

# concat subparser
concat_subparser = subparsers.add_parser("concat", help="Concatenate images of episodes")
concat_subparser.set_defaults(subparser_name="concat")
concat_subparser.add_argument(
    "webtoon_directory_path",
    type=Path,
    metavar="webtoon_directory_path",
    help="The name of folder that contains webtoon folders to concatenate",
)
concat_subparser.add_argument(
    "-s",
    "--select",
    action="store_true",
    help="Instead of typing the webtoon directory directly, open the webtoon directory selector",
)
concat_subparser.add_argument("--all", action="store_true", help="Merge all images of each episode")
concat_subparser.add_argument(
    "-C",
    "--count",
    type=int,
    help="Concatenate based on image count",
)
concat_subparser.add_argument(
    "-H",
    "--height",
    type=int,
    help="Concatenate based on the height of concatenated images",
)
concat_subparser.add_argument(
    "-R",
    "--ratio",
    type=float,
    help="Concatenate based on the ratio of concatenated images",
)
concat_subparser.add_argument(
    "-t",
    "--target-webtoon-directory",
    type=Path,
    metavar="target_webtoon_directory",
    default=None,
    help="The destination of output webtoon directory",
)
concat_subparser.add_argument("-p", "--process-number", type=int, default=None, help="Multiprocessing process number")
concat_subparser.add_argument("-m", "--merge-number", type=int, default=None, help="Merge after concatenation")


def parse_download(args: argparse.Namespace) -> None:
    for webtoon_id in args.webtoon_ids:
        concat: BatchMode | None
        if args.concat is None:
            concat = None
        else:
            match args.concat:
                case "a" | "all":
                    concat = "all"
                case "c" | "count", value:
                    concat = "count", int(value)
                case "h" | "height", value:
                    concat = "height", int(value)
                case "r" | "ratio", value:
                    concat = "ratio", float(value)
                case other:
                    raise ValueError(f"Invalid concatenation arguments: {' '.join(map(repr, other))}")

        scraper = webtoon.setup_instance(
            webtoon_id,
            args.platform,
            cookie=args.cookie,
            download_directory=args.base_directory,
            options=dict(args.options or {}),
            existing_episode_policy=args.existing_episode
        )

        if args.list_episodes:
            scraper.fetch_all()
            table = Table(show_header=True, header_style="bold blue", box=None)
            table.add_column("Episode number [dim](ID)[/dim]", width=12)
            table.add_column("Episode Title", style="bold")
            for i, (episode_id, episode_title) in enumerate(zip(scraper.episode_ids, scraper.episode_titles), 1):
                table.add_row(
                    f"[red][bold]{i:04d}[/bold][/red] [dim]({episode_id})[/dim]",
                    str(episode_title),
                )
            Console().print(table)
            return

        scraper.download_webtoon(
            args.range,
            merge_number=args.merge_number,
            concat=concat,
            add_viewer=True,
        )


def parse_merge(args: argparse.Namespace) -> None:
    if args.select:
        select_from_directory(
            args.webtoon_directory_path,
            args.target_webtoon_directory,
            True,
            args.merge_number,
        )
    else:
        action = {"r": "restore", "m": "merge", "a": "auto"}.get(args.action, args.action)
        merge_or_restore_webtoon(
            args.webtoon_directory_path,
            args.target_webtoon_directory or args.webtoon_directory_path.parent,
            args.merge_number,
            action,  # type: ignore
        )


def _directory_selector(source_parent_directory: Path) -> Path:
    directories, _ = _directories_and_files_of(source_parent_directory, False)
    number_length = len(str(len(directories)))
    for i, directory in enumerate(directories, 1):
        print(f"{i:0{number_length}}. Concat {directory.name}")
    choice = int(input("Enter number: "))
    return directories[choice - 1]


def parse_concat(args: argparse.Namespace) -> None:
    if args.all:
        batch_mode = "all"
    elif args.count:
        batch_mode = "count", args.count
    elif args.height:
        batch_mode = "height", args.height
    elif args.ratio:
        batch_mode = "ratio", args.ratio
    else:
        raise ValueError("You must provide one of following options: --all/--count/--height/--ratio")

    if args.select:
        webtoon_dir = _directory_selector(args.webtoon_directory_path)
        target_dir = args.target_webtoon_directory
    else:
        webtoon_dir = args.webtoon_directory_path
        target_dir = args.target_webtoon_directory

    concatenated_webtoon_directory = concat_webtoon(
        webtoon_dir, target_dir, batch_mode, process_number=args.process_number
    )
    assert concatenated_webtoon_directory is not None

    if args.merge_number:
        logger.info(f"merging {concatenated_webtoon_directory}...")
        merge_webtoon(
            concatenated_webtoon_directory,
            None,
            args.merge_number,
            NORMAL_WEBTOON_DIRECTORY,
        )


def main(argv=None) -> Literal[0, 1]:
    """모든 CLI 명령어를 처리하는 함수입니다.

    Arguments:
        argv: 커맨드라인 명령어입니다. None이라면 자동으로 인자를 인식합니다.

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
        elif args.subparser_name == "concat":
            parse_concat(args)
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
