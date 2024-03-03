"""Download webtoons automatiallly or easily"""

from __future__ import annotations

import time
from multiprocessing import pool
from pathlib import Path
from typing import Literal
import warnings

import hxsoup

from .exceptions import InvalidPlatformError, InvalidURLError, UnsupportedRatingError
from .miscs import EpisodeNoRange, WebtoonId, logger
from .scrapers import (
    BufftoonScraper,
    KakaopageScraper,
    KakaoWebtoonScraper,
    LezhinComicsScraper,
    NaverBlogScraper,
    NaverBlogWebtoonId,
    NaverGameScraper,
    NaverPostScraper,
    NaverPostWebtoonId,
    NaverWebtoonScraper,
    Scraper,
    TistoryScraper,
    TistoryWebtoonId,
    WebtoonsDotcomScraper,
)

NAVER_WEBTOON = "naver_webtoon"
WEBTOONS_DOTCOM = "webtoons_dotcom"
BUFFTOON = "bufftoon"
NAVER_POST = "naver_post"
NAVER_GAME = "naver_game"
LEZHIN_COMICS = "lezhin_comics"
KAKAOPAGE = "kakaopage"
NAVER_BLOG = "naver_blog"
TISTORY = "tistory"
KAKAO_WEBTOON = "kakao_webtoon"

WebtoonPlatforms = Literal[
    "naver_webtoon",
    "webtoons_dotcom",
    "bufftoon",
    "naver_post",
    "naver_game",
    "lezhin_comics",
    "kakaopage",
    "naver_blog",
    "tistory",
    "kakao_webtoon",
]

SHORT_NAMES: dict[str, WebtoonPlatforms] = {
    "nw": "naver_webtoon",
    "wd": "webtoons_dotcom",
    "bt": "bufftoon",
    "np": "naver_post",
    "ng": "naver_game",
    "lc": "lezhin_comics",
    "kp": "kakaopage",
    "nb": "naver_blog",
    "ti": "tistory",
    "kw": "kakao_webtoon",
}

PLATFORMS: dict[WebtoonPlatforms, type[Scraper]] = {
    NAVER_WEBTOON: NaverWebtoonScraper,
    WEBTOONS_DOTCOM: WebtoonsDotcomScraper,
    BUFFTOON: BufftoonScraper,
    NAVER_POST: NaverPostScraper,
    NAVER_GAME: NaverGameScraper,
    LEZHIN_COMICS: LezhinComicsScraper,
    KAKAOPAGE: KakaopageScraper,
    NAVER_BLOG: NaverBlogScraper,
    TISTORY: TistoryScraper,
    KAKAO_WEBTOON: KakaoWebtoonScraper,
}


def get_webtoon_platform(webtoon_id: WebtoonId) -> WebtoonPlatforms | None:
    """titleid가 어디에서 나왔는지 확인합니다. 적합하지 않은 titleid는 포함되지 않습니다. 잘못된 타입을 입력할 경우 결과가 제대로 나오지 않을 수 있습니다."""

    def get_platform(
        platform_name: WebtoonPlatforms,
    ) -> tuple[WebtoonPlatforms, str | None]:
        WebtoonScraperClass = get_scraper_class(platform_name)
        return (
            platform_name,
            WebtoonScraperClass(webtoon_id).check_if_legitimate_webtoon_id(),
        )

    test_queue: tuple[WebtoonPlatforms, ...]
    if isinstance(webtoon_id, tuple):
        if isinstance(webtoon_id[0], int):
            test_queue = (NAVER_POST,)
        elif isinstance(webtoon_id[1], int):
            test_queue = (NAVER_BLOG,)
        else:
            test_queue = (TISTORY,)
    elif isinstance(webtoon_id, str):
        test_queue = (LEZHIN_COMICS,)
    elif isinstance(webtoon_id, int):
        test_queue = (
            NAVER_WEBTOON,
            WEBTOONS_DOTCOM,
            BUFFTOON,
            NAVER_GAME,
            KAKAOPAGE,
            KAKAO_WEBTOON,
        )
    else:
        raise TypeError(f"Unknown type of titleid({type(webtoon_id)})")

    print(f"Checking these platforms: {', '.join(test_queue)}")

    with pool.ThreadPool(len(test_queue)) as p:
        results_raw = p.map(get_platform, test_queue)

    results = [(platform, title) for platform, title in results_raw if title is not None]

    if (webtoon_length := len(results)) == 1:
        print(f"Webtoon's platform is assumed to be {results[0][0]}")
        return results[0][0]
    if webtoon_length == 0:
        print(f"There's no webtoon that webtoon ID is {webtoon_id}.")
        return None

    for i, (platform, name) in enumerate(results, 1):
        print(f"#{i} {platform}: {name}")

    platform_no = input(
        "Multiple webtoon is found. Please type number of webtoon you want to download(enter nothing to select #1): "
    )

    try:
        platform_no = 1 if platform_no == "" else int(platform_no)
    except ValueError:
        raise ValueError(
            "Webtoon ID should be integer. " f"{platform_no!r} is cannot be converted to integer."
        ) from None

    try:
        selected_platform, selected_webtoon = results[platform_no - 1]
    except IndexError:
        raise ValueError(f"Exceeded the range of webtoons(length of results was {results}).") from None
    logger.info(f"Webtoon {selected_webtoon} is selected.")
    return selected_platform


def get_webtoon_platform_from_url(webtoon_url: str) -> Scraper | None:
    for platform_name, platform_class in PLATFORMS.items():
        try:
            platform = platform_class.from_url(webtoon_url)
        except InvalidURLError:
            continue
        return platform
    return None


def get_scraper_class(webtoon_platform: str | WebtoonPlatforms) -> type[Scraper]:
    platform_class: type[Scraper] | None = PLATFORMS.get(webtoon_platform.lower())  # type: ignore
    if platform_class is None:
        raise ValueError(f'webtoon_type should be among {", ".join(PLATFORMS)}')
    return platform_class


def download_webtoon(
    webtoon_id_or_url: WebtoonId,
    webtoon_platform: WebtoonPlatforms | None = None,
    merge_number: int | None = None,
    *,
    cookie: str | None = None,
    episode_no_range: EpisodeNoRange = None,
    bearer: str | None = None,
    list_episodes: bool = False,
    download_directory: str | Path = "webtoon",
    get_paid_episode: bool = False,
) -> None:
    # 스크래퍼 불러오기
    if webtoon_platform:
        webtoon_scraper = get_scraper_class(webtoon_platform)(webtoon_id_or_url)
    elif isinstance(webtoon_id_or_url, str) and "." in webtoon_id_or_url:  # URL인지 확인
        webtoon_scraper = get_webtoon_platform_from_url(webtoon_id_or_url)
        if webtoon_scraper is None:
            raise InvalidPlatformError(f"Cannot get webtoon platform from URL: {webtoon_id_or_url}")
        webtoon_scraper = webtoon_scraper
    else:
        warnings.warn(
            "Inferring webtoon platform is deprecated. set `-p` flag to explicitly set platform.", DeprecationWarning
        )
        webtoon_platform = get_webtoon_platform(webtoon_id_or_url)
        if webtoon_platform is None:
            raise InvalidPlatformError(f"Cannot get webtoon platform from webtoon ID: {webtoon_id_or_url}")
        webtoon_scraper = get_scraper_class(webtoon_platform)(webtoon_id_or_url)

    # 특정 스크래퍼에만 존재하는 부가 정보 불러오기
    if cookie:
        if not isinstance(webtoon_scraper, (LezhinComicsScraper, BufftoonScraper)):
            raise InvalidPlatformError(f"Webtoon scraper {webtoon_platform} does not accept cookie.")
        webtoon_scraper.cookie = cookie
    if bearer:
        if not isinstance(webtoon_scraper, LezhinComicsScraper):
            raise InvalidPlatformError(f"Webtoon scraper {webtoon_platform} does not accept cookie.")
        webtoon_scraper.bearer = bearer
    if get_paid_episode and isinstance(webtoon_scraper, LezhinComicsScraper):
        webtoon_scraper.get_paid_episode = get_paid_episode

    # list_episodes 출력하기
    if list_episodes:
        webtoon_scraper.list_episodes()
        return

    # 다운로드
    webtoon_scraper.base_directory = download_directory
    webtoon_scraper.download_webtoon(
        episode_no_range,
        merge_number=merge_number,
        add_viewer=True,
    )


def download_webtoons_getting_paid(
    noticeid: int,
    merge_number: int | None = 5,
) -> None:
    res = hxsoup.get(f"https://comic.naver.com/api/notice/detail?noticeId={noticeid}")
    raw_html = res.json().get("notice").get("content")

    titleids = (int(tag.get("href").removeprefix("https://comic.naver.com/webtoon/list?titleId=").partition("&")[0]) for tag in hxsoup.SoupTools(raw_html).soup_select("a"))  # type: ignore

    for titleid in titleids:
        try:
            download_webtoon(titleid, NAVER_WEBTOON, merge_number=merge_number)
        except UnsupportedRatingError as e:
            print(e)
        time.sleep(10)
