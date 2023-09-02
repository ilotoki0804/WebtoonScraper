"""Download webtoons automatiallly or easily"""
# pylint: disable=logging-fstring-interpolation

from __future__ import annotations
import asyncio
import logging
from typing import Literal, TYPE_CHECKING

from requests_utils import requests, souptools

if __name__ in {"__main__", "webtoon"}:
    # from directory_merger import FolderMerger
    # import webtoon
    from scrapers.A_scraper import Scraper
    from scrapers.B_naver_webtoon import NaverWebtoonScraper
    from scrapers.C_best_challenge import BestChallengeScraper
    from scrapers.D_webtoon_originals import WebtoonOriginalsScraper
    from scrapers.E_webtoon_canvas import WebtoonCanvasScraper
    from scrapers.F_telescope import TelescopeScraper
    from scrapers.G_bufftoon import BufftoonScraper
    from scrapers.H_naver_post import NaverPostScraper
    from scrapers.I_naver_game import NaverGameScraper
    from scrapers.J_lezhin_comics import LezhinComicsScraper
    from scrapers.K_kakaopage import KakaopageScraper
else:
    # from .directory_merger import FolderMerger
    # from . import webtoon
    from .scrapers.A_scraper import Scraper
    from .scrapers.B_naver_webtoon import NaverWebtoonScraper
    from .scrapers.C_best_challenge import BestChallengeScraper
    from .scrapers.D_webtoon_originals import WebtoonOriginalsScraper
    from .scrapers.E_webtoon_canvas import WebtoonCanvasScraper
    from .scrapers.F_telescope import TelescopeScraper
    from .scrapers.G_bufftoon import BufftoonScraper
    from .scrapers.H_naver_post import NaverPostScraper
    from .scrapers.I_naver_game import NaverGameScraper
    from .scrapers.J_lezhin_comics import LezhinComicsScraper
    from .scrapers.K_kakaopage import KakaopageScraper

TitleId = int | tuple[int, int] | str

N = NAVER_WEBTOON = 'naver_webtoon'
B = BEST_CHALLENGE = 'best_challenge'
O = ORIGINALS = 'originals'  # noqa
C = CANVAS = 'canvas'
T = M = TELESCOPE = 'telescope'
BF = BUFFTOON = 'bufftoon'
P = POST = NAVER_POST = 'naver_post'
G = NAVER_GAME = 'naver_game'
L = LEZHIN = 'lezhin'
K = KAKAOPAGE = 'kakaopage'

PLATFORMS = (
    'naver_webtoon',
    'best_challenge',
    'originals',
    'canvas',
    'telescope',
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
    'telescope',
    'bufftoon',
    'naver_post',
    'naver_game',
    'lezhin',
    'kakaopage',
]


async def get_webtoon_platform(titleid: TitleId, is_auto_select: bool = False) -> WebtoonPlatforms | None:
    """titleid가 어디에서 나왔는지 확인합니다. 적합하지 않은 titleid는 포함되지 않습니다."""
    async def get_platform(platform_name: WebtoonPlatforms):
        try:
            WebtoonScraperClass = await get_scraper_class(platform_name)
            return platform_name, await WebtoonScraperClass().check_if_legitimate_titleid(titleid)
        except Exception as e:  # pylint: disable=broad-exception-caught
            logging.warning(f'An error occured. Skipping {platform_name}')
            logging.warning(f'error: {e}')
            return platform_name, None

    test_queue: tuple[str, ...]
    if isinstance(titleid, tuple):
        test_queue = (
            'naver_post',
        )
    elif isinstance(titleid, str):
        test_queue = (
            'lezhin',
        )
    elif isinstance(titleid, int):
        test_queue = (
            'naver_webtoon',
            'best_challenge',
            'originals',
            'canvas',
            'telescope',
            'bufftoon',
            'naver_game',
            'kakaopage',
        )
    else:
        raise TypeError(f'Unknown type of titleid({type(titleid)})')

    results_raw: list[tuple[WebtoonPlatforms, str | None]] = await asyncio.gather(*map(get_platform, test_queue))

    if TYPE_CHECKING:
        results: list[tuple[WebtoonPlatforms, str]] = []
        for result in results_raw:  # 리스트 컴프리헨션을 이용하면 타입 힌트가 제대로 작동하지 않음
            name_or_none = result[1]
            if name_or_none is not None:
                results.append((result[0], name_or_none))
    else:
        # 타입 힌트가 없을 경우 더 효율적인 동일한 코드
        # results: list[tuple[WebtoonPlatforms, str]] = list(filter(lambda x: x[1] is not None, results_raw))
        results: list[tuple[WebtoonPlatforms, str]] = [result for result in results_raw if result[1] is not None]
    if (webtoon_length := len(results)) == 1:
        logging.warning(f"Webtoon's platform is assumed to be {results[0][0]}")
        return results[0][0]
    if webtoon_length == 0:
        logging.warning(f"There's no webtoon that webtoon ID is {titleid}.")
        return None

    for i, (platform, name) in enumerate(results, 1):
        logging.warning(f'{i}. {platform}: {name}')

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


async def get_scraper_class(webtoon_type: WebtoonPlatforms) -> type[Scraper]:
    if webtoon_type.lower() == NAVER_WEBTOON:
        webtoonscraper = NaverWebtoonScraper
    elif webtoon_type.lower() == BEST_CHALLENGE:
        webtoonscraper = BestChallengeScraper
    elif webtoon_type.lower() == ORIGINALS:
        webtoonscraper = WebtoonOriginalsScraper
    elif webtoon_type.lower() == CANVAS:
        webtoonscraper = WebtoonCanvasScraper
    elif webtoon_type.lower() == TELESCOPE:
        webtoonscraper = TelescopeScraper
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


async def get_webtoon_async(
        titleid: TitleId,
        webtoon_type: WebtoonPlatforms | None = None,
        *,
        merge: int | None = None,
        cookie: str | None = None,
        is_auto_select: bool = False,
        episode_no_range: tuple[int, int] | int | None = None,
        authorization: str | None = None
) -> None:
    if cookie is not None:
        webtoon_scraper = BufftoonScraper()
        webtoon_scraper.COOKIE = cookie
    elif authorization is not None:
        webtoon_scraper = LezhinComicsScraper()
        webtoon_scraper.AUTHORIZATION = authorization
    else:
        webtoon_type = webtoon_type or await get_webtoon_platform(titleid, is_auto_select)

        if webtoon_type is None:
            raise ValueError('You must select item.')

        webtoon_scraper = (await get_scraper_class(webtoon_type))()
        if isinstance(webtoon_scraper, BufftoonScraper):  # == webtoon_type.lower() == BUFFTOON
            logging.warning("Proceed without cookie. It'll limit the number of episodes can be downloaded of Bufftoon.")

    await webtoon_scraper.download_one_webtoon_async(titleid, episode_no_range, merge=merge)


def get_webtoon(
        titleid: TitleId,
        webtoon_type: WebtoonPlatforms | None = None,
        *,
        merge: int | None = None,
        cookie: str | None = None,
        is_auto_select: bool = False,
        episode_no_range: tuple[int, int] | int | None = None,
        authorization: str | None = None
) -> None:
    asyncio.run(get_webtoon_async(titleid, webtoon_type, merge=merge, cookie=cookie, is_auto_select=is_auto_select,
                                  episode_no_range=episode_no_range, authorization=authorization))


async def get_webtoons_getting_paid_async(
        noticeid: int,
        merge: int | None = None,
) -> None:
    res = requests.get(
        f'https://comic.naver.com/api/notice/detail?noticeId={noticeid}', headers={})
    raw_soup = res.json().get('notice').get('content')

    titleids = map(int, souptools.soup_select(raw_soup, 'p span a').get(
        'href').removeprefix('https://comic.naver.com/webtoon/list?titleId='))

    for titleid in titleids:
        await get_webtoon_async(titleid, NAVER_WEBTOON, merge=merge)

if __name__ == '__main__':
    ...
