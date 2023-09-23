from __future__ import annotations

import argparse
import logging
from pathlib import Path
import sys
import os
from typing import Literal

path = os.path.realpath(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(path))

from WebtoonScraper import webtoon, __version__  # noqa

# currently Lezhin uses only lower case alphabet, numbers, and underscore. Rest of them are added for just in case.
acceptable_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_')

remove_space_and_parentheses = lambda value: value.replace(' ', '').removeprefix('(').removesuffix(')')  # noqa


def str_to_webtoon_id(webtoon_id: str) -> int | str | tuple[int, int]:
    if webtoon_id.isdigit():
        # all others
        return int(webtoon_id)
    if all(char in acceptable_chars for char in webtoon_id):
        # Lezhin
        return webtoon_id
    if ',' in webtoon_id:
        # If failed, check you type webtoon id currectly. example:
        # python -m WebtoonScraper 614921,19803452    >> valid
        # python -m WebtoonScraper 614921, 19803452   >> invalid due to space
        # python -m WebtoonScraper "614921, 19803452" >> valid
        series_no, member_no = [int(remove_space_and_parentheses(i)) for i in webtoon_id.split(',')]

        return series_no, member_no
    raise ValueError("Invalid webtoon id.")


def str_to_episode_no_range(episode_no_range: str) -> int | tuple[int | None, int | None] | None:
    if ',' not in episode_no_range:
        try:
            return int(episode_no_range)
        except ValueError:
            logging.warning('Failed to convert range statement; Download all episodes.')
            return None

    make_none_if_value_is_none_or_make_int = lambda value: int(value) if value and value.lower() != 'none' else None  # noqa

    start, end = [make_none_if_value_is_none_or_make_int(remove_space_and_parentheses(i)) for i in episode_no_range.split(',')]

    return start, end


parser = argparse.ArgumentParser(prog='WebtoonScraper', usage='Download webtoons in CLI', description='Download webtoons with ease!')
parser.add_argument('--mock', action='store_true',
                    help='No actual download.')
parser.add_argument('--version', action='version', version=__version__)

subparsers = parser.add_subparsers(title='Commands',
                                   # description='valid commands',
                                   help='Choose command you want. Currently download is only valid option.')

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
                                help="Episode number range you want to download.")
download_subparser.add_argument('--list-episodes', action='store_true',
                                help='List all episodes.')
# 사용자들이 햇갈릴 염려가 있어 사용하지 않음.
# download_subparser.add_argument('--naver-post', type=int, nargs=2, metavar=('seriesNo', 'memberNo'),
#                     help="Naver Post needs two arguments, so if you want to download Naver Post, you can use this for download. "
#                          "You don't need to specify webtoon platform if you use this.")


def main(argv=None) -> Literal[0, 1]:
    args = parser.parse_args(argv)

    if args.mock:
        print('Arguments:', str(args).removeprefix('Namespace(').removesuffix(')'))
        return 0

    if hasattr(args, 'webtoon_id'):
        print('Download has started.', str(args).removeprefix('Namespace'))
        try:
            webtoon.download_webtoon(
                args.webtoon_id,
                args.platform,
                args.merge_amount,
                cookie=args.cookie,
                authkey=args.authkey,
                episode_no_range=args.range,
                download_directory=args.download_directory,
                list_episodes=args.list_episodes
            )
        except Exception as e:
            logging.error(f'An error accured. Error: {e}')
            return 1
        else:
            return 0

    logging.error("Invalid state. Maybe you forgot to write 'download'?")
    return 1


if __name__ == '__main__':
    sys.exit(main())
