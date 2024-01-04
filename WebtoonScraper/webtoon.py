"""Download webtoons automatiallly or easily"""

from __future__ import annotations
import logging
from pathlib import Path
from typing import Literal
from multiprocessing import pool
import hxsoup

from .scrapers import (
    Scraper,
    NaverWebtoonScraper,
    WebtoonsEnglishScraper,
    BufftoonScraper,
    NaverPostScraper,
    NaverPostWebtoonId,
    NaverGameScraper,
    LezhinComicsScraper,
    KakaopageScraper,
    NaverBlogScraper,
    NaverBlogWebtoonId,
    TistoryScraper,
    TistoryWebtoonId,
)
from .exceptions import InvalidPlatformError, UnsupportedWebtoonRatingError
from .miscs import WebtoonId, EpisodeNoRange

NAVER_WEBTOON = "naver_webtoon"
WEBTOONS_ENGLISH = "originals"
BUFFTOON = "bufftoon"
NAVER_POST = "naver_post"
NAVER_GAME = "naver_game"
LEZHIN = "lezhin"
KAKAOPAGE = "kakaopage"
NAVER_BLOG = "naver_blog"
TISTORY = "tistory"

WebtoonPlatforms = Literal[
    "naver_webtoon",
    "originals",
    "canvas",
    "bufftoon",
    "naver_post",
    "naver_game",
    "lezhin",
    "kakaopage",
    "naver_blog",
    "tistory",
]

SHORT_NAMES: dict[str, WebtoonPlatforms] = {
    "nw": "naver_webtoon",
    "or": "originals",
    "bf": "bufftoon",
    "np": "naver_post",
    "ng": "naver_game",
    "lz": "lezhin",
    "kp": "kakaopage",
    "nb": "naver_blog",
    "ti": "tistory",
}

PLATFORMS: dict[WebtoonPlatforms, type[Scraper]] = {
    NAVER_WEBTOON: NaverWebtoonScraper,
    WEBTOONS_ENGLISH: WebtoonsEnglishScraper,
    BUFFTOON: BufftoonScraper,
    NAVER_POST: NaverPostScraper,
    NAVER_GAME: NaverGameScraper,
    LEZHIN: LezhinComicsScraper,
    KAKAOPAGE: KakaopageScraper,
    NAVER_BLOG: NaverBlogScraper,
    TISTORY: TistoryScraper,
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
        test_queue = (LEZHIN,)
    elif isinstance(webtoon_id, int):
        test_queue = (
            NAVER_WEBTOON,
            WEBTOONS_ENGLISH,
            BUFFTOON,
            NAVER_GAME,
            KAKAOPAGE,
        )
    else:
        raise TypeError(f"Unknown type of titleid({type(webtoon_id)})")

    print(f"Checking these platforms: {', '.join(test_queue)}")

    with pool.ThreadPool(len(test_queue)) as p:
        results_raw = p.map(get_platform, test_queue)

    results = [
        (platform, title) for platform, title in results_raw if title is not None
    ]

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
            "Webtoon ID should be integer. "
            f"{platform_no!r} is cannot be converted to integer."
        ) from None

    try:
        selected_platform, selected_webtoon = results[platform_no - 1]
    except IndexError:
        raise ValueError(
            f"Exceeded the range of webtoons(length of results was {results})."
        ) from None
    logging.info(f"Webtoon {selected_webtoon} is selected.")
    return selected_platform


def get_scraper_class(webtoon_platform: str | WebtoonPlatforms) -> type[Scraper]:
    platform_class: type[Scraper] | None = PLATFORMS.get(webtoon_platform.lower())  # type: ignore
    if platform_class is None:
        raise ValueError(f'webtoon_type should be among {", ".join(PLATFORMS)}')
    return platform_class


def download_webtoon(
    webtoon_id: WebtoonId,
    webtoon_platform: WebtoonPlatforms | None = None,
    merge_amount: int | None = None,
    *,
    cookie: str | None = None,
    episode_no_range: EpisodeNoRange = None,
    bearer: str | None = None,
    is_list_episodes: bool = False,
    download_directory: str | Path = "webtoon",
    get_paid_episode: bool = False,
) -> None:
    if bearer is not None and isinstance(webtoon_id, str):
        webtoon_scraper = LezhinComicsScraper(webtoon_id)
        webtoon_scraper.bearer = bearer
        if cookie is not None:
            webtoon_scraper.cookie = cookie
        webtoon_scraper.get_paid_episode = get_paid_episode
    elif cookie is not None:
        webtoon_scraper = BufftoonScraper(webtoon_id)
        webtoon_scraper.cookie = cookie
    webtoon_platform = webtoon_platform or get_webtoon_platform(webtoon_id)
    if webtoon_platform is None:
        raise ValueError(
            "You didn't select a valid item, or webtoon id was inappropriate. "
            "Select a valid item or webtoon id."
        )

    if cookie is not None:
        if webtoon_platform != BUFFTOON:
            raise ValueError(
                "Cookie is not required unless you are downloading Bufftoon. "
                "Use bearer if platform what you want to download is Lezhin."
            )
        webtoon_scraper = BufftoonScraper(webtoon_id, cookie=cookie)
    elif bearer is not None:
        if webtoon_platform != LEZHIN:
            raise ValueError(
                "bearer is not required unless you are downloading Lezhin. "
                "Use cookie if platform what you want to download is Bufftoon."
            )
        assert isinstance(webtoon_id, str)
        webtoon_scraper = LezhinComicsScraper(webtoon_id, bearer=bearer)
    else:
        webtoon_scraper = get_scraper_class(webtoon_platform)(webtoon_id)
        if isinstance(webtoon_scraper, BufftoonScraper):
            logging.warning(
                "Proceed without cookie. It'll limit the number of episodes can be downloaded of Bufftoon."
            )
        if isinstance(webtoon_scraper, LezhinComicsScraper):
            logging.warning(
                "Proceed without bearer. It'll limit the number of episodes can be downloaded of Lezhin Comics."
            )

    if is_list_episodes:
        webtoon_scraper.list_episodes()
        return

    webtoon_scraper.base_directory = download_directory
    webtoon_scraper.download_webtoon(episode_no_range, merge_amount=merge_amount)


def download_webtoons_getting_paid(
    noticeid: int,
    merge_amount: int | None = 5,
) -> None:
    res = hxsoup.get(f"https://comic.naver.com/api/notice/detail?noticeId={noticeid}")
    raw_html = res.json().get("notice").get("content")

    titleids = (
        int(tag.get("href").removeprefix("https://comic.naver.com/webtoon/list?titleId=").partition("&")[0])  # type: ignore
        for tag in hxsoup.SoupTools(raw_html).soup_select("a")
    )

    for titleid in titleids:
        try:
            download_webtoon(titleid, NAVER_WEBTOON, merge_amount=merge_amount)
        except UnsupportedWebtoonRatingError as e:
            print(e)
