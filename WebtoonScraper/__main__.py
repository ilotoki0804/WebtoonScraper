from __future__ import annotations

import argparse
import functools
import logging
from pathlib import Path
import sys
import os
import re
from typing import Literal
from rich.table import Table
from rich.console import Console

from WebtoonScraper import webtoon, __version__
from WebtoonScraper.exceptions import DirectoryStateUnmatchedError
from WebtoonScraper.miscs import WebtoonId, EpisodeNoRange
from WebtoonScraper.directory_merger import (
    DirectoryMerger,
    NORMAL_WEBTOON_DIRECTORY,
    MERGED_WEBTOON_DIRECTORY,
    ContainerStates,
    merge_webtoon_directory_to_directory,
    restore_webtoon_directory_to_directory,
    detailed_check_directory_state,
    fast_check_container_state,
)

SHOW_ERROR = False

# currently Lezhin uses only lower case alphabet, numbers, and underscore. Rest of them are added for just in case.
acceptable_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_')

remove_space_and_parentheses = lambda value: value.replace(' ', '').removeprefix('(').removesuffix(')')  # noqa


def str_to_webtoon_id(webtoon_id: str) -> WebtoonId:
    if webtoon_id.isdigit():
        # all others
        return int(webtoon_id)
    if all(char in acceptable_chars for char in webtoon_id):
        # Lezhin
        return webtoon_id
    if ',' not in webtoon_id:
        raise ValueError("Invalid webtoon id.")

    match_result = re.match(r""" * *[(]? *(['"]?(.+?)['"]?) *, *(['"]?(.+?)['"]?) *[)]? *$""", webtoon_id)
    assert match_result is not None, 'Invalid webtoon id.'
    is_arg1_quoted, is_arg2_quoted = match_result.group(2)[0] in {'"', "'"}, match_result.group(3)[0] in {'"', "'"}
    arg1, arg2 = match_result.group(2), match_result.group(4)

    if arg1.isdigit() and not is_arg1_quoted:
        # 네이버 포스트
        return int(arg1), int(arg2)
    elif arg2.isdigit() and not is_arg2_quoted:
        # 네이버 블로그
        blog_id = match_result.group(2)
        assert isinstance(blog_id, str)
        return blog_id, int(arg2)
    else:
        # 티스토리
        assert isinstance(arg1, str)
        assert isinstance(arg2, str)
        return arg1, arg2


def str_to_episode_no_range(episode_no_range: str) -> EpisodeNoRange:
    if ',' not in episode_no_range:
        try:
            return int(episode_no_range)
        except ValueError:
            logging.warning('Failed to convert range statement; Download all episodes.')
            return None

    make_none_if_value_is_none_or_make_int = lambda value: int(value) if value and value.lower() != 'none' else None  # noqa

    start, end = (make_none_if_value_is_none_or_make_int(remove_space_and_parentheses(i))
                  for i in episode_no_range.split(','))

    return start, end


def case_insensitive(string: str) -> str:
    return string.lower()


parser = argparse.ArgumentParser(prog='WebtoonScraper', usage='Download or merge webtoons in CLI', description='Download webtoons with ease!')
parser.add_argument('--mock', action='store_true',
                    help='No actual download.')
parser.add_argument('--version', action='version', version=f'WebtoonScraper {__version__} of Python {sys.version}')
subparsers = parser.add_subparsers(title='Commands',
                                   # description='valid commands',
                                   help='Choose command you want. Currently download is only valid option.')

# 'download' subparsers
download_subparser = subparsers.add_parser('download', help='Download webtoons.')
download_subparser.set_defaults(subparser_name='download')
download_subparser.add_argument('webtoon_id', type=str_to_webtoon_id, metavar='webtoon_id',
                                help='Webtoon ID. If you want to download Naver Post, you should follow this format: '
                                '"seriesNo,memberNo", for example: "614921,19803452". '
                                # 'Check docs to detailed way to do.'
                                )
download_subparser.add_argument('-p', '--platform', type=str, metavar='webtoon_platform', choices=webtoon.PLATFORMS,
                                help="Webtoon platform to download. No need to specify if you don't want to. "
                                     # "You should not specify if you want to download webtoons from various platform. "
                                     # "Platform name is full string. For example, Naver Webtoon is 'naver_webtoon', Lezhin is 'lezhin'. "
                                     # "Type --help to see all of platform strings."
                                     f"All choices: {', '.join(webtoon.PLATFORMS)}"
                                )
download_subparser.add_argument('-m', '--merge-amount', type=int, metavar='merge_amount',
                                help="Merge amount when you want to merge directories. Don't specify if you don't want to merge.")
download_subparser.add_argument('--cookie', type=str, metavar='cookie',
                                help="Set cookie when you download Bufftoon.")
download_subparser.add_argument('--authkey', type=str, metavar='authkey',
                                help="Set authkey when you download Lezhin.")
download_subparser.add_argument('-r', '--range', type=str_to_episode_no_range, metavar='[start],[end]',
                                help="Episode number range you want to download.")
download_subparser.add_argument('-d', '--download-directory', type=Path, metavar='directory', default='webtoon',
                                help="The directory you want to download to.")
download_subparser.add_argument('--list-episodes', action='store_true',
                                help='List all episodes.')
download_subparser.add_argument('--get-paid-episode', action='store_true',
                                help='Get paid episode. Lezhin Comics only.')

# TODO: 'merge' parser 추가하기
merge_subparser = subparsers.add_parser('merge', help="Merge/Restore webtoon directory.")
merge_subparser.set_defaults(subparser_name='merge')
merge_subparser.add_argument('webtoon_directory_name', nargs='?', type=str, metavar='webtoon_directory_name', default=None,
                             help="The name of webtoon folder to merge or restore.")
merge_subparser.add_argument('--all', action='store_true',
                             help='Merge/Restore all webtoons in root directory. If state of webtoons not equal, you cannot use auto action.')
merge_subparser.add_argument('-a', '--action', type=case_insensitive, metavar='[a]uto|[m]erge|[r]estore', default='auto',
                             choices=['m', 'merge', 'r', 'restore', 'a', 'auto'],
                             help="Merge/Restore. If this is auto, it'll flip state(merge > restore, restore > merge).")
merge_subparser.add_argument('-m', '--merge-amount', type=int, metavar='merge_amount', default=None,
                             help="Merge amount when merge.")
merge_subparser.add_argument('-s', '--source-directory', '--source-parent-directory', type=Path, metavar='source_parent_directory', default=Path('webtoon'),
                             help="The directory that the folders of webtoons are located.")
merge_subparser.add_argument('-t', '--target-directory', '--target-parent-directory', type=Path, metavar='target_parent_directory', default=None,
                             help="The directory that the result of merge/restore will be located. Defaults to soure directory itself.")
merge_subparser.add_argument('--list', action='store_true',
                             help='List all directories and states.')


def parse_download(args: argparse.Namespace) -> None:
    # 만약 다른 타입의 튜플인데 NAVER_BLOG라면 자동으로 (str, int)로 변환한다.
    if args.platform == webtoon.NAVER_BLOG and isinstance(args.webtoon_id[0], int):
        args.webtoon_id = str(args.webtoon_id[0]), int(args.webtoon_id[1])

    # 만약 다른 타입의 튜플인데 TISTORY라면 자동으로 (str, str)로 변환한다.
    if args.platform == webtoon.TISTORY and isinstance(args.webtoon_id[0], int):
        args.webtoon_id = str(args.webtoon_id[0]), str(args.webtoon_id[1])

    webtoon.download_webtoon(
        args.webtoon_id,
        args.platform,
        args.merge_amount,
        cookie=args.cookie,
        authkey=args.authkey,
        episode_no_range=args.range,
        download_directory=args.download_directory,
        is_list_episodes=args.list_episodes,
        get_paid_episode=args.get_paid_episode,
    )


CONTAINER_STATE_PER_ARGS: dict[str, ContainerStates] = {
    'm': NORMAL_WEBTOON_DIRECTORY,
    'merge': NORMAL_WEBTOON_DIRECTORY,
    'r': MERGED_WEBTOON_DIRECTORY,
    'restore': MERGED_WEBTOON_DIRECTORY,
}

ABBR_TO_FULL_STATE: dict[str, Literal['merge', 'restore', 'auto']] = {
    'm': 'merge',
    'merge': 'merge',
    'r': 'restore',
    'restore': 'restore',
    'a': 'auto',
    'auto': 'auto',
}


CONTAINER_STATE_TO_DO_STATE: dict[ContainerStates, Literal['merge', 'restore']] = {
    NORMAL_WEBTOON_DIRECTORY: 'merge',
    MERGED_WEBTOON_DIRECTORY: 'restore',
}


def get_state(source_directory: Path) -> ContainerStates:
    states: dict[Path, ContainerStates] = {
        webtoon_directory: detailed_check_directory_state(webtoon_directory)
        for webtoon_directory in source_directory.iterdir()
    }
    all_unique_states = set(states.values())
    if len(all_unique_states) != 1:
        raise ValueError(
            "All webtoons in source directory should have same state when using 'auto' action.\n"
            "Please specify --action(-a) or check directory state."
            f"States: {all_unique_states}"
        )

    directories_state, = all_unique_states
    return directories_state


def get_string_todo(state: ContainerStates) -> Literal['merge', 'restore']:
    try:
        return CONTAINER_STATE_TO_DO_STATE[state]
    except KeyError:
        raise ValueError(f"State {state} is not supported.")


def list_directories(parent_directory: Path) -> None:
    table = Table(show_header=True, header_style="bold blue", box=None)
    table.add_column("Webtoon Directory Name", style='bold')
    table.add_column("Directory State")
    table.add_column("Action If Auto")
    for webtoon_directory in parent_directory.iterdir():
        directory_state = fast_check_container_state(webtoon_directory)
        table.add_row(webtoon_directory.name, directory_state, CONTAINER_STATE_TO_DO_STATE.get(directory_state))
    # self.rich_console.print(table)
    Console().print(table)


def parse_merge(args: argparse.Namespace) -> None:
    if args.list:
        return list_directories(args.source_directory)

    if args.webtoon_directory_name is not None and args.all:
        raise ValueError('--all option and webtoon_directory_name cannot coexist. Did you mean --root-directory?')

    args.target_directory = args.target_directory or args.source_directory
    args.action = ABBR_TO_FULL_STATE[args.action]

    if args.webtoon_directory_name is None and not args.all:
        dm = DirectoryMerger()
        dm.source_directory = args.source_directory
        dm.target_directory = args.target_directory or args.source_directory
        dm.select(args.merge_amount, manual_container_state=CONTAINER_STATE_PER_ARGS.get(args.action))
        return

    if args.action == 'auto':
        if args.all:
            args.action = get_string_todo(get_state(args.source_directory))
        else:
            args.action = get_string_todo(
                detailed_check_directory_state(args.source_directory / args.webtoon_directory_name))

    if args.action == 'merge' and args.merge_amount is None:
        raise ValueError('merge_amount is required. Use option `-m <int>` to specify merge amount.')

    if args.action == 'merge':
        function_to_use = functools.partial(merge_webtoon_directory_to_directory, merge_amount=args.merge_amount)
        logging.warning("Merging...")
    elif args.action == 'restore':
        function_to_use = restore_webtoon_directory_to_directory
        logging.warning("Restoring...")
    else:
        raise NotImplementedError("Cannot reach here.")

    if args.all:
        for webtoon_directory in args.source_directory.iterdir():
            try:
                function_to_use(webtoon_directory, args.target_directory / webtoon_directory.name)
            except (DirectoryStateUnmatchedError, KeyError):
                logging.warning(f'Skipping {webtoon_directory.name} directory.')
    else:
        function_to_use(args.source_directory / args.webtoon_directory_name,
                        args.target_directory / args.webtoon_directory_name)


def main(argv=None) -> Literal[0, 1]:
    args = parser.parse_args(argv)  # 주어진 argv가 None이면 sys.argv[1:]을 기본값으로 삼음

    if args.mock:
        print('Arguments:', str(args).removeprefix('Namespace(').removesuffix(')'))
        return 0

    if not hasattr(args, 'subparser_name'):
        return main(argv=['--help'])

    print(f'{"Downloading" if args.subparser_name == "download" else "Merging"} has started'
          f'{str(args).removeprefix("Namespace")}.')

    try:
        if args.subparser_name == 'download':
            parse_download(args)
        elif args.subparser_name == 'merge':
            parse_merge(args)
        else:
            raise NotImplementedError(f'Subparser {args.subparser_name} is not implemented.')
        parse_download(args)
    except Exception as e:
        if SHOW_ERROR:
            raise
        logging.error(e)
        return 1
    else:
        return 0


if __name__ == '__main__':
    sys.exit(main())
