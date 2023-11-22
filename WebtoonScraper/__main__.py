from __future__ import annotations

import argparse
import logging
from pathlib import Path
import sys
import os
import re
from typing import Literal

path = os.path.realpath(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(path))

from . import webtoon, __version__  # noqa
from .miscs import WebtoonId, EpisodeNoRange  # noqa

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


def str_to_episode_no_range(episode_no_range: str) -> int | tuple[int | None, int | None] | None:
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


parser = argparse.ArgumentParser(prog='WebtoonScraper', usage='Download webtoons in CLI', description='Download webtoons with ease!')
parser.add_argument('--mock', action='store_true',
                    help='No actual download.')
parser.add_argument('--version', action='version', version=f'WebtoonScraper {__version__} of Python {sys.version}')
subparsers = parser.add_subparsers(title='Commands',
                                   # description='valid commands',
                                   help='Choose command you want. Currently download is only valid option.')

# 'download' subparsers
download_subparser = subparsers.add_parser('download', help='Download webtoons.')
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


def main(argv=None) -> Literal[0, 1]:
    args = parser.parse_args(argv)  # 주어진 argv가 None이면 sys.argv[1:]을 기본값으로 삼음

    if args.mock:
        print('Arguments:', str(args).removeprefix('Namespace(').removesuffix(')'))
        return 0

    if not hasattr(args, 'webtoon_id'):
        logging.error("Invalid state. Maybe you forgot to write 'download'?")
        return 1

    print(f'Download has started{str(args).removeprefix("Namespace")}.')

    # 만약 다른 타입의 튜플인데 NAVER_BLOG라면 자동으로 (str, int)로 변환한다.
    if args.platform == webtoon.NAVER_BLOG and isinstance(args.webtoon_id[0], int):
        args.webtoon_id = str(args.webtoon_id[0]), int(args.webtoon_id[1])

    # 만약 다른 타입의 튜플인데 TISTORY라면 자동으로 (str, str)로 변환한다.
    if args.platform == webtoon.TISTORY and isinstance(args.webtoon_id[0], int):
        args.webtoon_id = str(args.webtoon_id[0]), str(args.webtoon_id[1])

    try:
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
    except Exception as e:
        logging.error(f'An error accured. Error: {e}')
        return 1
    else:
        return 0


if __name__ == '__main__':
    sys.exit(main())
