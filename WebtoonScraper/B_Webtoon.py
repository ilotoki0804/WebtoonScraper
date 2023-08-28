"""Download webtoons automatiallly or easily"""

from __future__ import annotations
import asyncio
import contextlib
from itertools import starmap
import logging
from typing import Coroutine, Literal

if __name__ in ("__main__", "B_Webtoon"):
    # from A_FolderMerger import FolderMerger
    from C_Scraper import Scraper
    from D_NaverWebtoonScraper import NaverWebtoonScraper
    from E_BestChallengeScraper import BestChallengeScraper
    from F_WebtoonOriginalsScraper import WebtoonOriginalsScraper
    from G_WebtoonCanvasScraper import WebtoonCanvasScraper
    from H_TelescopeScraper import TelescopeScraper
    from I_BufftoonScraper import BufftoonScraper
    from J_NaverPostScraper import NaverPostScraper
    from K_NaverGameScraper import NaverGameScraper
    from L_LezhinComicsScraper import LezhinComicsScraper
    from M_KakaopageWebtoonScraper import KakaopageWebtoonScraper
else:
    # from .A_FolderMerger import FolderMerger
    from .C_Scraper import Scraper
    from .D_NaverWebtoonScraper import NaverWebtoonScraper
    from .E_BestChallengeScraper import BestChallengeScraper
    from .F_WebtoonOriginalsScraper import WebtoonOriginalsScraper
    from .G_WebtoonCanvasScraper import WebtoonCanvasScraper
    from .H_TelescopeScraper import TelescopeScraper
    from .I_BufftoonScraper import BufftoonScraper
    from .J_NaverPostScraper import NaverPostScraper
    from .K_NaverGameScraper import NaverGameScraper
    from .L_LezhinComicsScraper import LezhinComicsScraper
    from .M_KakaopageWebtoonScraper import KakaopageWebtoonScraper

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

# sourcery skip: low-code-quality
async def get_webtoon_platform(titleid: TitleId, is_auto_select=False) -> WebtoonPlatforms | None:    # noqa
    """titleid가 어디에서 나왔는지 확인합니다. 적합하지 않은 titleid는 포함되지 않습니다."""
    # TODO: 네이버 포스트 추가하기
    """If webtoon is best challenge, this returns True. Otherwise, False."""
    async def get_platform(platform_name: WebtoonPlatforms):
        try:
            scraper = await get_scraper_instance(platform_name)
            return platform_name, await scraper.check_if_legitimate_titleid(titleid)
        except Exception as e:
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

    platforms = [get_platform(platform) for platform in test_queue]
    results_raw: list[tuple[WebtoonPlatforms, str | None]] = await asyncio.gather(*platforms)
    results: list[tuple[WebtoonPlatforms, str]] = []
    for result in results_raw:  # 리스트 컴프리헨션을 이용하면 타입 힌트가 제대로 작동하지 않음
        name_or_none = result[1]
        if name_or_none is not None:
            results.append((result[0], name_or_none))
    # results: list[tuple[str, str]] = [result for result in results_raw if result[1] is not None]
    assert all(isinstance(result[1], str) for result in results)  # type ensure

    if (webtoon_length := len(results)) == 1:
        logging.warning(f'Webtoon\'s platform is assumed to be {results[0][0]}')
        return results[0][0]
    elif webtoon_length == 0:
        logging.warning(f'There\'s no webtoon that webtoon ID is {titleid}.')
    else:
        for i, (platform, name) in enumerate(results, 1):
            logging.warning(f'{i}. {platform}: {name}')
        if not is_auto_select:
            platform_no = input('Multiple webtoon is searched. Please type number of webtoon you want to download(enter nothing to select no.1): ')
        else:
            platform_no = ''

        try:
            platform_no = 1 if platform_no == '' else int(platform_no)
        except ValueError as e:
            raise ValueError('Webtoon ID should be integer.') from e

        try:
            selected_platform, selected_webtoon = results[platform_no - 1]
        except IndexError:
            raise ValueError('Exceeded the range of webtoons.')
        logging.info(f'Webtoon {selected_webtoon} is selected.')
        return selected_platform


async def get_scraper_instance(webtoon_type: WebtoonPlatforms) -> Scraper:
    if webtoon_type.lower() == NAVER_WEBTOON:
        webtoonscraper = NaverWebtoonScraper()
    elif webtoon_type.lower() == BEST_CHALLENGE:
        webtoonscraper = BestChallengeScraper()
    elif webtoon_type.lower() == ORIGINALS:
        webtoonscraper = WebtoonOriginalsScraper()
    elif webtoon_type.lower() == CANVAS:
        webtoonscraper = WebtoonCanvasScraper()
    elif webtoon_type.lower() == TELESCOPE:
        webtoonscraper = TelescopeScraper()
    elif webtoon_type.lower() == BUFFTOON:
        webtoonscraper = BufftoonScraper()
    elif webtoon_type.lower() == NAVER_POST:
        webtoonscraper = NaverPostScraper()
    elif webtoon_type.lower() == NAVER_GAME:
        webtoonscraper = NaverGameScraper()
    elif webtoon_type.lower() == LEZHIN:
        webtoonscraper = LezhinComicsScraper()
    elif webtoon_type.lower() == KAKAOPAGE:
        webtoonscraper = KakaopageWebtoonScraper()
    else:
        raise ValueError('webtoon_type should be among naver_webtoon, best_challenge, originals, '
                         'canvas, bufftoon, telescope, naver_post, naver_game, lezhin, and kakaopage.')
    return webtoonscraper


async def get_webtoon_async(
        titleid: TitleId,
        webtoon_type: WebtoonPlatforms | None= None,
        *,
        merge: int | None = None,
        cookie: str | None = None,
        is_auto_select: bool = False,
        episode_no_range: tuple[int, int] | int | None = None,
        authorization: str | None = None
) -> None:
    def set_cookie(cookie):
        webtoonscraper = BufftoonScraper()
        if cookie:
            webtoonscraper.COOKIE = cookie
        else:
            webtoonscraper.COOKIE = input(f'Enter cookie of {titleid} (Enter nothing to proceed without cookie): ')
        return webtoonscraper

    if cookie is None and authorization is None:
        webtoon_type = await get_webtoon_platform(titleid, is_auto_select)

        if webtoon_type is None:
            raise ValueError('You must select item.')

        if webtoon_type.lower() == BUFFTOON:
            webtoonscraper = set_cookie(cookie)
        else:
            webtoonscraper = await get_scraper_instance(webtoon_type)

    elif cookie is not None:
        webtoonscraper = set_cookie(cookie)
    elif authorization is not None:
        webtoonscraper = LezhinComicsScraper()
        webtoonscraper.AUTHORIZATION = authorization
    else:
        raise ValueError('Placeholder for later new ones.')

    await webtoonscraper.download_one_webtoon_async(titleid, episode_no_range, merge=merge)


def get_webtoon(
        titleid: TitleId,
        webtoon_type: WebtoonPlatforms | None= None,
        *,
        merge: int | None = None,
        cookie: str | None = None,
        is_auto_select: bool = False,
        episode_no_range: tuple[int, int] | int | None = None,
        authorization: str | None = None
) -> None:
    asyncio.run(get_webtoon_async(titleid, webtoon_type, merge=merge, cookie=cookie, is_auto_select=is_auto_select,
                                  episode_no_range=episode_no_range, authorization=authorization))


if __name__ == '__main__':
    ...
