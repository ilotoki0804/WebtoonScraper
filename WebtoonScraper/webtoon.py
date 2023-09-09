"""Download webtoons automatiallly or easily"""
# pylint: disable=logging-fstring-interpolation

from __future__ import annotations
import asyncio
import logging
from typing import Iterable, Literal, TYPE_CHECKING

from requests_utils import requests, souptools

if __name__ in {"__main__", "webtoon"}:
    # from directory_merger import DirectoryMerger
    from scrapers.A_scraper import Scraper
    from scrapers.B_naver_webtoon import NaverWebtoonScraper
    from scrapers.C_best_challenge import BestChallengeScraper
    from scrapers.D_webtoon_originals import WebtoonOriginalsScraper
    from scrapers.E_webtoon_canvas import WebtoonCanvasScraper
    from scrapers.G_bufftoon import BufftoonScraper
    from scrapers.H_naver_post import NaverPostScraper, NaverPostWebtoonId
    from scrapers.I_naver_game import NaverGameScraper
    from scrapers.J_lezhin_comics import LezhinComicsScraper
    from scrapers.K_kakaopage import KakaopageScraper
else:
    # from .directory_merger import DirectoryMerger
    from .scrapers.A_scraper import Scraper
    from .scrapers.B_naver_webtoon import NaverWebtoonScraper
    from .scrapers.C_best_challenge import BestChallengeScraper
    from .scrapers.D_webtoon_originals import WebtoonOriginalsScraper
    from .scrapers.E_webtoon_canvas import WebtoonCanvasScraper
    from .scrapers.G_bufftoon import BufftoonScraper
    from .scrapers.H_naver_post import NaverPostScraper, NaverPostWebtoonId
    from .scrapers.I_naver_game import NaverGameScraper
    from .scrapers.J_lezhin_comics import LezhinComicsScraper
    from .scrapers.K_kakaopage import KakaopageScraper

TitleId = int | tuple[int, int] | str

N = NAVER_WEBTOON = 'naver_webtoon'
B = BEST_CHALLENGE = 'best_challenge'
O = ORIGINALS = 'originals'  # noqa
C = CANVAS = 'canvas'
BF = BUFFTOON = 'bufftoon'
P = POST = NAVER_POST = 'naver_post'
G = NAVER_GAME = 'naver_game'
L = LEZHIN = 'lezhin'
KP = KAKAOPAGE = 'kakaopage'

PLATFORMS = (
    'naver_webtoon',
    'best_challenge',
    'originals',
    'canvas',
    'bufftoon',
    'naver_post',
    'naver_game',
    'lezhin',
    'kakaopage',
)

WebtoonPlatforms = Literal[
    'naver_webtoon',
    'best_challenge',
    'originals',
    'canvas',
    'bufftoon',
    'naver_post',
    'naver_game',
    'lezhin',
    'kakaopage',
]


def get_webtoon_platform(webtoon_id: TitleId, is_auto_select: bool = False) -> WebtoonPlatforms | None:
    """titleid가 어디에서 나왔는지 확인합니다. 적합하지 않은 titleid는 포함되지 않습니다."""
    def get_platform(platform_name: WebtoonPlatforms):
        WebtoonScraperClass = get_scraper_class(platform_name)
        return platform_name, WebtoonScraperClass(webtoon_id).check_if_legitimate_webtoon_id()

    test_queue: Iterable[WebtoonPlatforms]
    if isinstance(webtoon_id, tuple):
        test_queue = (
            'naver_post',
        )
    elif isinstance(webtoon_id, str):
        test_queue = (
            'lezhin',
        )
    elif isinstance(webtoon_id, int):
        test_queue = (
            'naver_webtoon',
            'best_challenge',
            'originals',
            'canvas',
            'bufftoon',
            'naver_game',
            'kakaopage',
        )
    else:
        raise TypeError(f'Unknown type of titleid({type(webtoon_id)})')

    results_raw: list[tuple[WebtoonPlatforms, str | None]] = [get_platform(platform) for platform in test_queue]

    results: list[tuple[WebtoonPlatforms, str]] = []
    if TYPE_CHECKING:
        for platform, name_or_none in results_raw:  # 리스트 컴프리헨션을 이용하면 타입 힌트가 제대로 작동하지 않음
            if name_or_none is not None:
                results.append((platform, name_or_none))
    else:
        # 타입 힌트가 없을 경우 더 효율적인 동일한 코드
        # results = list(filter(lambda x: x[1] is not None, results_raw))
        # filter보다 리스트 컴프레헨션이 더 빠름.
        results = [result for result in results_raw if result[1] is not None]

    if (webtoon_length := len(results)) == 1:
        print(f"Webtoon's platform is assumed to be {results[0][0]}")
        return results[0][0]
    if webtoon_length == 0:
        print(f"There's no webtoon that webtoon ID is {webtoon_id}.")
        return None

    for i, (platform, name) in enumerate(results, 1):
        print(f'{i}. {platform}: {name}')

    platform_no = '' if is_auto_select else input(
        'Multiple webtoon is searched. Please type number of webtoon you want to download(enter nothing to select no.1): '
    )

    try:
        platform_no = 1 if platform_no == '' else int(platform_no)
    except ValueError as e:
        raise ValueError('Webtoon ID should be integer.') from e

    try:
        selected_platform, selected_webtoon = results[platform_no - 1]
    except IndexError as e:
        raise ValueError('Exceeded the range of webtoons.') from e
    logging.info(f'Webtoon {selected_webtoon} is selected.')
    return selected_platform


def get_scraper_class(webtoon_type: WebtoonPlatforms) -> type[Scraper]:
    if webtoon_type.lower() == NAVER_WEBTOON:
        webtoonscraper = NaverWebtoonScraper
    elif webtoon_type.lower() == BEST_CHALLENGE:
        webtoonscraper = BestChallengeScraper
    elif webtoon_type.lower() == ORIGINALS:
        webtoonscraper = WebtoonOriginalsScraper
    elif webtoon_type.lower() == CANVAS:
        webtoonscraper = WebtoonCanvasScraper
    elif webtoon_type.lower() == BUFFTOON:
        webtoonscraper = BufftoonScraper
    elif webtoon_type.lower() == NAVER_POST:
        webtoonscraper = NaverPostScraper
    elif webtoon_type.lower() == NAVER_GAME:
        webtoonscraper = NaverGameScraper
    elif webtoon_type.lower() == LEZHIN:
        webtoonscraper = LezhinComicsScraper
    elif webtoon_type.lower() == KAKAOPAGE:
        webtoonscraper = KakaopageScraper
    else:
        raise ValueError('webtoon_type should be among naver_webtoon, best_challenge, originals, '
                         'canvas, bufftoon, telescope, naver_post, naver_game, lezhin, and kakaopage.')
    return webtoonscraper


def download_webtoon(
        webtoon_id: TitleId,
        webtoon_type: WebtoonPlatforms | None = None,
        merge_amount: int | None = None,
        *,
        cookie: str | None = None,
        is_auto_select: bool = False,
        episode_no_range: tuple[int, int] | int | None = None,
        authkey: str | None = None
) -> None:
    if cookie is not None:
        webtoon_scraper = BufftoonScraper(webtoon_id)
        webtoon_scraper.cookie = cookie
    elif authkey is not None and isinstance(webtoon_id, str):
        webtoon_scraper = LezhinComicsScraper(webtoon_id)
        webtoon_scraper.authkey = authkey
    else:
        webtoon_type = webtoon_type or get_webtoon_platform(webtoon_id, is_auto_select)

        if webtoon_type is None:
            raise ValueError('You must select item.')

        webtoon_scraper = get_scraper_class(webtoon_type)(webtoon_id)
        if isinstance(webtoon_scraper, BufftoonScraper):  # == webtoon_type.lower() == BUFFTOON
            logging.warning("Proceed without cookie. It'll limit the number of episodes can be downloaded of Bufftoon.")

    webtoon_scraper.download_webtoon(episode_no_range, merge_amount=merge_amount)


def download_webtoons_getting_paid(
        noticeid: int,
        merge_amount: int | None = None,
) -> None:
    res = requests.get(f'https://comic.naver.com/api/notice/detail?noticeId={noticeid}', headers={})  # type: ignore
    raw_soup = res.json().get('notice').get('content')

    titleids = (int(tag.get('href').removeprefix('https://comic.naver.com/webtoon/list?titleId='))  # type: ignore
                for tag in souptools.soup_select(raw_soup, 'p span a'))

    for titleid in titleids:
        download_webtoon(titleid, NAVER_WEBTOON, merge_amount=merge_amount)
