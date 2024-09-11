"""Scrape Webtoons from Naver Webtoon."""

from __future__ import annotations

import re
from itertools import count
from json.decoder import JSONDecodeError
from typing import TYPE_CHECKING, ClassVar, Literal
from venv import logger

import hxsoup
from yarl import URL

from ..exceptions import (
    InvalidPlatformError,
    InvalidURLError,
    UnsupportedRatingError,
)
from ._scraper import Scraper, reload_manager
from ._naver_webtoon_extra import NaverWebtoonCommentsDownloadOption, NaverWebtoonMetaInfoScraper


class AbstractNaverWebtoonScraper(Scraper[int]):
    """Scrape webtoons from Naver Webtoon."""

    BASE_URL: str
    TEST_WEBTOON_ID: int
    WEBTOON_TYPE: ClassVar[Literal["WEBTOON", "BEST_CHALLENGE", "CHALLENGE"]]
    EPISODE_IMAGES_URL_SELECTOR: ClassVar[str]
    PATH_NAME: str
    DOWNLOAD_INTERVAL = 0.5
    COMMENTS_DOWNLOAD_SUPPORTED = True
    extra_info_scraper: NaverWebtoonMetaInfoScraper
    INFORMATION_VARS = Scraper.INFORMATION_VARS | dict(comments_data=None)

    def __init__(self, webtoon_id: int, /, *, cookie: str | None = None) -> None:
        super().__init__(webtoon_id)
        self.headers.update(Referer="https://comic.naver.com/webtoon/")
        if self.extra_info_scraper is None:
            self.extra_info_scraper = NaverWebtoonMetaInfoScraper()
        if cookie is not None:
            self.cookie = cookie

    @reload_manager
    def fetch_webtoon_information(self, *, reload: bool = False, no_invalid_webtoon_type_error: bool = False) -> None:
        url = f"https://comic.naver.com/api/article/list/info?titleId={self.webtoon_id}"
        try:
            webtoon_json_info = self.hxoptions.get(url, headers=self.headers | dict(Accept="application/json, text/plain, */*")).json()
        except JSONDecodeError:
            raise InvalidPlatformError(f"{self.webtoon_id} is invalid webtoon ID.") from None
        # webtoon_json_info['thumbnailUrl']  # 정사각형 썸네일
        webtoon_thumbnail = webtoon_json_info["sharedThumbnailUrl"]  # 실제로 웹툰 페이지에 사용되는 썸네일
        title = webtoon_json_info["titleName"]  # 제목
        webtoon_type = webtoon_json_info["webtoonLevelCode"]  # BEST_CHALLENGE or WEBTOON
        authors = "/".join(author["name"] for author in webtoon_json_info["communityArtists"])

        if not self.cookie and webtoon_json_info["age"]["type"] == "RATE_18":
            raise UnsupportedRatingError(
                f"In order to download adult webtoon {title}, you need valid cookie. Refer to docs to get additional info"
            )

        self.webtoon_thumbnail_url = webtoon_thumbnail
        self.title = title
        self.webtoon_type = webtoon_type
        self.author = authors

        if not no_invalid_webtoon_type_error and self.WEBTOON_TYPE != webtoon_type:
            platform_name = {
                "WEBTOON": "Naver Webtoon",
                "BEST_CHALLENGE": "Best Challenge",
                "CHALLENGE": "Challenge",
            }.get(webtoon_type, "(Unknown)")
            raise InvalidPlatformError(f"Use {platform_name} Scraper to download {platform_name}.")

    @reload_manager
    def fetch_episode_information(self, *, reload: bool = False) -> None:
        prev_articleList = []
        subtitles = []
        episode_ids = []
        for i in count(1):
            url = f"https://comic.naver.com/api/article/list?titleId={self.webtoon_id}&page={i}&sort=ASC"
            try:
                res = self.hxoptions.get(url).json()
            except JSONDecodeError:
                # fetch_webtoon_information은 지원하지 않는 rating일 때 오류를 낸다.
                # 만약 fetch_webtoon_information보다 fetch_episode_information가 먼저
                # 실행되었을 경우 UnsupportedWebtoonRatingError를 미처 내지 못했을 수 있다.
                # 그런 경우인지 확인한 후 만약 지원하지 않는 rating에 대한 오류가 아니었다면
                # 다른 버그로 간주하고 다시 raise한다.
                self.fetch_webtoon_information()
                raise

            curr_articleList = res["articleList"]
            if prev_articleList == curr_articleList:
                break
            for article in curr_articleList:
                subtitles.append(article["subtitle"])
                episode_ids.append(article["no"])

            prev_articleList = curr_articleList

        self.episode_titles = subtitles
        self.episode_ids = episode_ids

    def get_episode_image_urls(self, episode_no: int) -> list[str]:
        # sourcery skip: de-morgan
        episode_id = self.episode_ids[episode_no]
        url = f"{self.BASE_URL}/detail?titleId={self.webtoon_id}&no={episode_id}"
        response = self.hxoptions.get(url)
        episode_image_urls_raw = response.soup_select(self.EPISODE_IMAGES_URL_SELECTOR)
        episode_image_urls = [
            element["src"]
            for element in episode_image_urls_raw
            if not ("agerate" in element["src"] or "ctguide" in element["src"])  # cspell: ignore agerate ctguide
        ]

        if TYPE_CHECKING:
            episode_image_urls = [url for url in episode_image_urls if isinstance(url, str)]

        self.extra_info_scraper.gather_author_comment(episode_no, response)

        return episode_image_urls

    def get_episode_extra(self, episode_no) -> None:
        self.extra_info_scraper.fetch_episode_comments(episode_no, self)

    def check_webtoon_id(self) -> str | None:
        return super().check_webtoon_id((InvalidPlatformError, UnsupportedRatingError))

    @property
    def cookie(self) -> str | None:
        """브라우저에서 값을 확인할 수 있는 쿠키 값입니다. 로그인 등에서 이용됩니다."""
        try:
            return self.headers["Cookie"]
        except KeyError:
            return None

    @cookie.setter
    def cookie(self, value: str) -> None:
        matched = re.search(r"XSRF-TOKEN=([^;]+);", value)
        if not matched:
            raise ValueError("Cookie does not contain required data.")
        self.headers.update({"Cookie": value, "X-Xsrf-Token": matched[1]})

    @property
    def comments_data(self):
        return self.extra_info_scraper.comments_data

    @classmethod
    def _extract_webtoon_id(cls, url) -> int | None:
        if url.host not in {"comic.naver.com", "m.comic.naver.com"}:
            return None
        if url.path != f"/{cls.PATH_NAME}/list":
            return None
        webtoon_id_str = url.query.get("titleId")
        if not webtoon_id_str:
            return None
        return int(webtoon_id_str)

    def _apply_options(self, options: dict[str, str], /) -> None:
        for option, raw_value in options.items():
            option = option.upper().replace("-", "_").strip()
            if option == "COMMENTS":
                if raw_value is None or raw_value == "TOP":
                    self.extra_info_scraper.comments_option = NaverWebtoonCommentsDownloadOption(top_comments_only=True)
                elif raw_value == "FULL":
                    self.extra_info_scraper.comments_option = NaverWebtoonCommentsDownloadOption(top_comments_only=False)
            else:
                logger.warning(f"Unknown option for {type(self).__name__}: {option!r}. value: {raw_value!r}")


class NaverWebtoonSpecificScraper(AbstractNaverWebtoonScraper):
    """네이버 정식 연재만 다운로드받을 수 있는 스크래퍼입니다.

    네이버 베스트 도전, 네이버 도전만화는 이것으로 다운로드받을 수 없습니다.
    만약 자동으로 네이버 관련 플랫폼을 확인할 수 있는 스크래퍼를 사용하고 싶다면
    NaverWebtoonScraper를 이용하세요.
    """

    BASE_URL = "https://comic.naver.com/webtoon"
    PLATFORM = "naver_webtoon_specific"
    TEST_WEBTOON_ID = 809590  # 이번 생
    WEBTOON_TYPE = "WEBTOON"
    EPISODE_IMAGES_URL_SELECTOR = "#sectionContWide > img"
    PATH_NAME = "webtoon"


class BestChallengeSpecificScraper(AbstractNaverWebtoonScraper):
    """네이버 베스트 도전만 다운로드받을 수 있는 스크래퍼입니다.

    네이버 정식 연재, 네이버 도전만화는 이것으로 다운로드받을 수 없습니다.
    만약 자동으로 네이버 관련 플랫폼을 확인할 수 있는 스크래퍼를 사용하고 싶다면
    NaverWebtoonScraper를 이용하세요.
    """

    BASE_URL = "https://comic.naver.com/bestChallenge"
    PLATFORM = "best_challenge"
    TEST_WEBTOON_ID = 816046  # 집
    WEBTOON_TYPE = "BEST_CHALLENGE"
    EPISODE_IMAGES_URL_SELECTOR = "#comic_view_area > div > img"
    PATH_NAME = "bestChallenge"


class ChallengeSpecificScraper(AbstractNaverWebtoonScraper):
    """네이버 도전만화만 다운로드받을 수 있는 스크래퍼입니다.

    네이버 정식 연재, 네이버 베스트 도전은 이것으로 다운로드받을 수 없습니다.
    만약 자동으로 네이버 관련 플랫폼을 확인할 수 있는 스크래퍼를 사용하고 싶다면
    NaverWebtoonScraper를 이용하세요.
    """

    BASE_URL = "https://comic.naver.com/challenge"
    PLATFORM = "challenge"
    TEST_WEBTOON_ID = 818058  # T/F
    WEBTOON_TYPE = "CHALLENGE"
    EPISODE_IMAGES_URL_SELECTOR = "#comic_view_area > div > img"
    PATH_NAME = "challenge"


class NaverWebtoonScraper(
    NaverWebtoonSpecificScraper,
    BestChallengeSpecificScraper,
    ChallengeSpecificScraper,
):
    """네이버 웹툰(네이버 웹툰/베스트 도전/도전 만화 무관) 스크래퍼입니다."""

    PLATFORM = "naver_webtoon"
    TEST_WEBTOON_IDS = (
        NaverWebtoonSpecificScraper.TEST_WEBTOON_ID,
        BestChallengeSpecificScraper.TEST_WEBTOON_ID,
        ChallengeSpecificScraper.TEST_WEBTOON_ID,
    )

    def __new__(
        cls, *args, **kwargs
    ) -> NaverWebtoonSpecificScraper | BestChallengeSpecificScraper | ChallengeSpecificScraper:
        scraper = NaverWebtoonSpecificScraper(*args, **kwargs)
        scraper.fetch_webtoon_information(no_invalid_webtoon_type_error=True)
        match scraper.webtoon_type:
            case "WEBTOON":
                return scraper
            case "BEST_CHALLENGE":
                return BestChallengeSpecificScraper(*args, **kwargs)
            case "CHALLENGE":
                return ChallengeSpecificScraper(*args, **kwargs)
            case webtoon_type:
                raise ValueError(f"Unexpected webtoon type {webtoon_type}. Please contact developer.")

    @classmethod
    def from_url(
        cls,
        url: str,
        /,
        *,
        cookie: str | None = None,
    ) -> NaverWebtoonSpecificScraper | BestChallengeSpecificScraper | ChallengeSpecificScraper:
        yarl_ = URL(url)
        try:
            webtoon_id, platform = cls._extract_webtoon_id(yarl_)
        except Exception as e:
            raise InvalidURLError.from_url(url, cls) from e

        if webtoon_id is None or platform is None:
            raise InvalidURLError.from_url(url, cls)

        match platform:
            case "webtoon":
                return NaverWebtoonSpecificScraper(webtoon_id, cookie=cookie)
            case "bestChallenge":
                return BestChallengeSpecificScraper(webtoon_id, cookie=cookie)
            case "challenge":
                return ChallengeSpecificScraper(webtoon_id, cookie=cookie)
            case _:
                raise ValueError(f"Unexpected webtoon type {platform}.")

    @classmethod
    def _extract_webtoon_id(cls, url: URL) -> tuple[int | None, str | None]:
        url = cls._extract_naver_me(url) or url
        if url.host not in ("comic.naver.com", "m.comic.naver.com"):
            raise
            return None, None
        matched = re.match(r"/(?P<platform>\w+)/list", str(url.path))
        if not matched:
            raise
            return None, None
        platform = matched["platform"]
        webtoon_id_str = url.query.get("titleId")
        if not webtoon_id_str:
            raise
            return None, None
        return int(webtoon_id_str), platform

    @classmethod
    def _extract_naver_me(cls, url: URL) -> URL | None:
        if url.host != "naver.me":
            return None
        full_url = hxsoup.get(f"https://naver.me{url.path}").headers["location"]
        return URL(full_url)
