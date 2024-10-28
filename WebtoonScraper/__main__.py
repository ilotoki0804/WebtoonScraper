from __future__ import annotations

import argparse
import asyncio
import contextlib
import logging
import re
import sys
from argparse import ArgumentParser, Namespace
from collections.abc import Sequence
from importlib.resources import files
from pathlib import Path
from typing import Any, Literal
from collections.abc import Callable, Iterable

from WebtoonScraper.exceptions import InvalidPlatformError, InvalidURLError
from rich.console import Console
from rich.table import Table

import WebtoonScraper
from WebtoonScraper import __version__
from WebtoonScraper.base import logger, platforms
from WebtoonScraper.scrapers import EpisodeRange, Scraper


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
            "lezhin_comics": "download Lezhin Comics (partially)",
        }
        installed = set()

        # fmt: off  # 맥락상 import와 installed가 서로 붙어있는 편이 어울림
        with contextlib.suppress(Exception):
            from PIL import Image  # noqa
            installed.add("lezhin_comics")
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

    return f"WebtoonScraper {__version__} of Python {sys.version} at {str(files(WebtoonScraper))}"


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

parser.add_argument(
    "--mock", action="store_true", help="Print argument parsing result and exit. Exist for debug or practice purpose"
)
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
parser.add_argument("--no-progress-bar", action="store_true", help="Use log instead progress bar to display status")
subparsers = parser.add_subparsers(title="Commands")
parser.add_argument(
    "-N",
    "--thread-number",
    type=int,
    default=None,
    help="Set concurrent thread number. You can also use `THREAD_NUMBER` to set thread numbers to use.",
)

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
    choices=("url", *platforms),
    metavar="PLATFORM",
    default="url",
    help=(
        "Webtoon platform to download. Only specify when you want to use webtoon id rather than url. "
        f"Supported platforms: {', '.join(platforms)}"
    ),
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
    "-O",
    "--options",
    type=_parse_options,
    help="Additional options for scraper",
    metavar='OPTION_NAME="OPTION_VALUE"',
    nargs="+",
)
download_subparser.add_argument(
    "--existing-episode",
    choices=["skip", "raise", "download_again", "hard_check"],
    default="skip",
    help="Determine what to do when episode directory already exists",
)


def _register(platform_name: str, scraper=None):
    if scraper is None:
        return lambda scraper: _register(platform_name, scraper)

    platforms[platform_name] = scraper
    return scraper


def instantiate(webtoon_platform: str, webtoon_id: str) -> Scraper:
    """웹툰 플랫폼 코드와 웹툰 ID로부터 스크레퍼를 인스턴스화하여 반환합니다. cookie, bearer 등의 추가적인 설정이 필요할 수도 있습니다."""

    Scraper: type[Scraper] | None = platforms.get(webtoon_platform.lower())  # type: ignore
    if Scraper is None:
        raise ValueError(f"Invalid webtoon platform: {webtoon_platform}")
    return Scraper._from_string(webtoon_id)


def instantiate_from_url(webtoon_url: str) -> Scraper:
    """웹툰 URL로부터 자동으로 알맞은 스크래퍼를 인스턴스화합니다. cookie, bearer 등의 추가적인 설정이 필요할 수 있습니다."""

    for PlatformClass in platforms.values():
        try:
            platform = PlatformClass.from_url(webtoon_url)
        except InvalidURLError:
            continue
        return platform
    raise InvalidPlatformError(f"Platform not detected: {webtoon_url}")


def setup_instance(
    webtoon_id_or_url: str,
    webtoon_platform: str | Literal["url"],
    *,
    existing_episode_policy: Literal["skip", "raise", "download_again", "hard_check"] = "skip",
    cookie: str | None = None,
    download_directory: str | Path | None = None,
    options: dict[str, str] | None = None,
) -> Scraper:
    """여러 설정으로부터 적절한 스크래퍼 인스턴스를 반환합니다. CLI 사용을 위해 디자인되었습니다."""

    # 스크래퍼 불러오기
    if webtoon_platform == "url" or "." in webtoon_id_or_url:  # URL인지 확인
        scraper = instantiate_from_url(webtoon_id_or_url)
    else:
        scraper = instantiate(webtoon_platform, webtoon_id_or_url)

    # 부가 정보 불러오기
    if cookie:
        scraper.cookie = cookie
    if options:
        scraper._apply_options(options)

    # attribute 형식 설정 설정
    if download_directory:
        scraper.base_directory = download_directory
    scraper.existing_episode_policy = existing_episode_policy

    return scraper


async def parse_download(args: argparse.Namespace) -> None:
    for webtoon_id in args.webtoon_ids:
        scraper = setup_instance(
            webtoon_id,
            args.platform,
            cookie=args.cookie,
            download_directory=args.base_directory,
            options=dict(args.options or {}),
            existing_episode_policy=args.existing_episode,
        )

        if args.list_episodes:
            await scraper.fetch_all()
            table = Table(show_header=True, header_style="bold blue", box=None)
            table.add_column("Episode number [dim](ID)[/dim]", width=12)
            table.add_column("Episode Title", style="bold")
            for i, (episode_id, episode_title) in enumerate(
                zip(scraper.episode_ids, scraper.episode_titles, strict=True), 1
            ):
                table.add_row(
                    f"[red][bold]{i:04d}[/bold][/red] [dim]({episode_id})[/dim]",
                    str(episode_title),
                )
            Console().print(table)
            return

        if args.no_progress_bar:
            scraper.use_progress_bar = False

        if hasattr(scraper, "thread_number"):
            scraper.thread_number = args.thread_number  # type: ignore

        await scraper.async_download_webtoon(args.range)


def main(argv=None) -> Literal[0, 1]:
    return asyncio.run(async_main(argv))


async def async_main(argv=None) -> Literal[0, 1]:
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
        match args.subparser_name:
            case "download":
                await parse_download(args)
            case unknown_subparser:
                raise NotImplementedError(f"{unknown_subparser} is not a valid command.")
    except KeyboardInterrupt as exc:
        logger.error("Aborted.")
        return 1
    except SystemExit as exc:
        return exc.code  # type: ignore
    except BaseException as exc:
        logger.error(f"{type(exc).__name__}: {exc}")
        Console().print_exception()
        return 1
    else:
        return 0


if __name__ == "__main__":
    sys.exit(main())
