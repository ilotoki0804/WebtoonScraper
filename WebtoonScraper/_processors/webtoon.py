"""WebtoonScraper의 CLI 구현을 위한 코드들"""

from __future__ import annotations

from multiprocessing import pool
from pathlib import Path
from typing import Literal

from ..base import WebtoonId, logger
from ..exceptions import InvalidPlatformError, InvalidURLError
from ..scrapers import (
    BufftoonScraper,
    CommentsDownloadOption,
    KakaopageScraper,
    KakaoWebtoonScraper,
    LezhinComicsScraper,
    NaverBlogScraper,
    NaverGameScraper,
    NaverPostScraper,
    NaverWebtoonScraper,
    Scraper,
    TistoryScraper,
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


def instantiate(webtoon_platform: str | WebtoonPlatforms, webtoon_id: WebtoonId) -> Scraper:
    """웹툰 플랫폼 코드와 웹툰 ID로부터 스크레퍼를 인스턴스화하여 반환합니다. cookie, bearer 등의 추가적인 설정이 필요할 수도 있습니다."""

    Scraper: type[Scraper] | None = PLATFORMS.get(webtoon_platform.lower())  # type: ignore
    if Scraper is None:
        raise ValueError(f"Invalid webtoon platform: {webtoon_platform}")
    return Scraper(webtoon_id)


def instantiate_from_url(webtoon_url: str) -> Scraper:
    """웹툰 URL로부터 자동으로 알맞은 스크래퍼를 인스턴스화합니다. cookie, bearer 등의 추가적인 설정이 필요할 수 있습니다."""

    for platform_name, PlatformClass in PLATFORMS.items():
        try:
            platform = PlatformClass.from_url(webtoon_url)
        except InvalidURLError:
            continue
        return platform
    raise InvalidPlatformError(f"Failed to retrieve webtoon platform from URL: {webtoon_url}")


def check_platform(webtoon_id, platform_name: WebtoonPlatforms) -> tuple[WebtoonPlatforms, str | None]:
    if not PLATFORMS[platform_name]._check_webtoon_id_type(webtoon_id):
        return platform_name, None

    logger.debug(f"Checking {platform_name}...")
    scraper = instantiate(platform_name, webtoon_id)
    return (
        platform_name,
        scraper.check_if_legitimate_webtoon_id(),
    )


def get_webtoon_platform(webtoon_id: WebtoonId) -> WebtoonPlatforms | None:
    """웹툰 ID를 추측합니다.

    Threading을 활용해 빠르게 모든 플랫폼의 결과를 확인합니다.
    잘못된 타입을 입력할 경우 결과가 제대로 나오지 않을 수 있습니다.

    Raises:
        TypeError: WebtoonId에 해당하지 않는 타입이 webtoon_id 인자에 왔을 때 발생합니다.
        ValueError: 사용자가 정수가 아닌 인덱스를 사용했을 때 발생합니다.
        IndexError: 사용자가 범위를 벗어나는 선택을 했을 때 발생합니다.
    """

    # 테스트 실행
    with pool.ThreadPool(len(PLATFORMS)) as p:
        results_raw = p.starmap(check_platform, ((webtoon_id, platform) for platform in PLATFORMS))
    results: list[tuple[WebtoonPlatforms, str | None]] = [(platform, title) for platform, title in results_raw if title is not None]

    # 같은 웹툰 ID의 서로 다른 웹툰을 가지고 있는 플랫폼들의 개수에 따라 결과 결정
    if not results:
        return None
    if len(results) == 1:
        return results[0][0]

    # 같은 웹툰 ID를 서로 다른 플랫폼에서 각자 가지고 있을 경우 사용자에게 질문해서 플랫폼 결정
    for i, (platform, name) in enumerate(results, 1):
        print(f"#{i} {platform}: {name}")

    platform_no = input("Multiple webtoon is found. Please type number of webtoon you want to download: ")
    platform_no = int(platform_no)

    selected_platform, selected_webtoon = results[platform_no - 1]
    logger.info(f"Webtoon {selected_webtoon} is selected.")
    return selected_platform


def setup_instance(
    webtoon_id_or_url: WebtoonId,
    webtoon_platform: WebtoonPlatforms | Literal["url"],
    *,
    cookie: str | None = None,
    bearer: str | None = None,
    download_directory: str | Path = "webtoon",
    get_paid_episode: bool = False,
    comments_option: CommentsDownloadOption | None = None,
) -> Scraper:
    """여러 설정으로부터 적절한 스크래퍼 인스턴스를 반환합니다. CLI 사용을 위해 디자인되었습니다."""

    # 스크래퍼 불러오기
    if isinstance(webtoon_id_or_url, str) and (webtoon_platform == "url" or "." in webtoon_id_or_url):  # URL인지 확인
        scraper = instantiate_from_url(webtoon_id_or_url)
    elif webtoon_platform == "url":
        raise TypeError(f"{type(webtoon_id_or_url).__name__!r} is not valid type of URL.")
    elif webtoon_platform:
        scraper = instantiate(webtoon_platform, webtoon_id_or_url)
    else:
        raise InvalidPlatformError(f"Unknown platform: {webtoon_platform}")

    # 부가 정보 불러오기
    if cookie:
        scraper.cookie = cookie
    if bearer and isinstance(scraper, LezhinComicsScraper):
        scraper.bearer = bearer
    if get_paid_episode and isinstance(scraper, LezhinComicsScraper):
        scraper.get_paid_episode = get_paid_episode

    # attribute 형식 설정 설정
    scraper.comments_option = comments_option
    scraper.base_directory = download_directory

    return scraper
