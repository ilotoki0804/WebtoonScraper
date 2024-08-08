"""WebtoonScraper의 CLI 구현을 위한 코드들"""

from __future__ import annotations

from multiprocessing import pool
from pathlib import Path
from typing import Literal

from ..base import logger
from ..exceptions import InvalidPlatformError, InvalidURLError
from ..scrapers import (
    BufftoonScraper,
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


def instantiate(webtoon_platform: str | WebtoonPlatforms, webtoon_id: str) -> Scraper:
    """웹툰 플랫폼 코드와 웹툰 ID로부터 스크레퍼를 인스턴스화하여 반환합니다. cookie, bearer 등의 추가적인 설정이 필요할 수도 있습니다."""

    Scraper: type[Scraper] | None = PLATFORMS.get(webtoon_platform.lower())  # type: ignore
    if Scraper is None:
        raise ValueError(f"Invalid webtoon platform: {webtoon_platform}")
    return Scraper._from_string(webtoon_id)


def instantiate_from_url(webtoon_url: str) -> Scraper:
    """웹툰 URL로부터 자동으로 알맞은 스크래퍼를 인스턴스화합니다. cookie, bearer 등의 추가적인 설정이 필요할 수 있습니다."""

    for PlatformClass in PLATFORMS.values():
        try:
            platform = PlatformClass.from_url(webtoon_url)
        except InvalidURLError:
            continue
        return platform
    raise InvalidPlatformError(f"Failed to retrieve webtoon platform from URL: {webtoon_url}")


def setup_instance(
    webtoon_id_or_url: str,
    webtoon_platform: WebtoonPlatforms | Literal["url"],
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
