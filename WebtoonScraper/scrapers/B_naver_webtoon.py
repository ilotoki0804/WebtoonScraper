"""Scrape Webtoons from Naver Webtoon."""

from __future__ import annotations
from itertools import count
from json.decoder import JSONDecodeError
from typing import TYPE_CHECKING, ClassVar, Literal

from .A_scraper import Scraper, reload_manager
from ..exceptions import InvalidPlatformError, UnsupportedWebtoonRatingError


class AbstractNaverWebtoonScraper(Scraper[int]):
    """Scrape webtoons from Naver Webtoon."""

    BASE_URL: str
    TEST_WEBTOON_ID: int
    WEBTOON_TYPE: ClassVar[Literal["WEBTOON", "BEST_CHALLENGE", "CHALLENGE"]]
    URL_REGEX: str
    EPISODE_IMAGES_URL_SELECTOR: ClassVar[str]
    IS_CONNECTION_STABLE = True

    @reload_manager
    def fetch_webtoon_information(
        self, *, reload: bool = False, no_invalid_webtoon_type_error: bool = False
    ) -> None:
        url = f"https://comic.naver.com/api/article/list/info?titleId={self.webtoon_id}"
        try:
            webtoon_json_info = self.hxoptions.get(url).json()
        except JSONDecodeError:
            raise InvalidPlatformError(
                f"{self.webtoon_id} is invalid webtoon ID."
            ) from None
        # webtoon_json_info['thumbnailUrl']  # 정사각형 썸네일
        webtoon_thumbnail = webtoon_json_info[
            "sharedThumbnailUrl"
        ]  # 실제로 웹툰 페이지에 사용되는 썸네일
        title = webtoon_json_info["titleName"]  # 제목
        webtoon_type = webtoon_json_info[
            "webtoonLevelCode"
        ]  # BEST_CHALLENGE or WEBTOON

        if webtoon_json_info["age"]["type"] == "RATE_18":
            raise UnsupportedWebtoonRatingError(
                f"Webtoon {title} is adult webtoon, "
                "which is not supported in NaverWebtoonScraper. "
                f"Thus cannot download {title}."
            )

        self.webtoon_thumbnail_url = webtoon_thumbnail
        self.title = title
        self.webtoon_type = webtoon_type

        if not no_invalid_webtoon_type_error and self.WEBTOON_TYPE != webtoon_type:
            platform_name = {
                "WEBTOON": "Naver Webtoon",
                "BEST_CHALLENGE": "Best Challenge",
                "CHALLENGE": "Challenge",
            }.get(webtoon_type, "(Unknown)")
            raise InvalidPlatformError(
                f"Use {platform_name} Scraper to download {platform_name}."
            )

    @reload_manager
    def fetch_episode_informations(self, *, reload: bool = False) -> None:
        prev_articleList = []
        subtitles = []
        episode_ids = []
        for i in count(1):
            url = f"https://comic.naver.com/api/article/list?titleId={self.webtoon_id}&page={i}&sort=ASC"
            try:
                res = self.hxoptions.get(url).json()
            except JSONDecodeError:
                # fetch_webtoon_information은 지원하지 않는 rating일 때 오류를 낸다.
                # 만약 fetch_webtoon_information보다 fetch_episode_informations가 먼저
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

    def get_episode_image_urls(self, episode_no) -> list[str]:
        # sourcery skip: de-morgan
        episode_id = self.episode_ids[episode_no]
        url = f"{self.BASE_URL}/detail?titleId={self.webtoon_id}&no={episode_id}"
        episode_image_urls_raw = self.hxoptions.get(url).soup_select(
            self.EPISODE_IMAGES_URL_SELECTOR
        )
        episode_image_urls = [
            element["src"]
            for element in episode_image_urls_raw
            if not ("agerate" in element["src"] or "ctguide" in element["src"])
        ]

        if TYPE_CHECKING:
            episode_image_urls = [
                url for url in episode_image_urls if isinstance(url, str)
            ]

        return episode_image_urls

    def check_if_legitimate_webtoon_id(self) -> str | None:
        return super().check_if_legitimate_webtoon_id(
            (InvalidPlatformError, UnsupportedWebtoonRatingError)
        )


class NaverWebtoonSpecificScraper(AbstractNaverWebtoonScraper):
    """네이버 정식 연재만 다운로드받을 수 있는 스크래퍼입니다.

    네이버 베스트 도전, 네이버 도전만화는 이것으로 다운로드받을 수 없습니다.
    만약 자동으로 네이버 관련 플랫폼을 확인할 수 있는 스크래퍼를 사용하고 싶다면
    NaverWebtoonScraper를 이용하세요.
    """

    BASE_URL = "https://comic.naver.com/webtoon"
    TEST_WEBTOON_ID = 809590  # 이번 생
    WEBTOON_TYPE = "WEBTOON"
    EPISODE_IMAGES_URL_SELECTOR = "#sectionContWide > img"
    URL_REGEX: str = r"(?:https?:\/\/)?(?:m[.])?comic[.]naver[.]com\/webtoon\/list\?(?:.*&)*titleId=(?P<webtoon_id>\d+)(?:&.*)*"


class BestChallengeSpecificScraper(AbstractNaverWebtoonScraper):
    """네이버 베스트 도전만 다운로드받을 수 있는 스크래퍼입니다.

    네이버 정식 연재, 네이버 도전만화는 이것으로 다운로드받을 수 없습니다.
    만약 자동으로 네이버 관련 플랫폼을 확인할 수 있는 스크래퍼를 사용하고 싶다면
    NaverWebtoonScraper를 이용하세요.
    """

    BASE_URL = "https://comic.naver.com/bestChallenge"
    TEST_WEBTOON_ID = 809971  # 까마귀
    WEBTOON_TYPE = "BEST_CHALLENGE"
    EPISODE_IMAGES_URL_SELECTOR = "#comic_view_area > div > img"
    URL_REGEX: str = r"(?:https?:\/\/)?comic[.]naver[.]com\/bestChallenge\/list\?(?:.*&)*titleId=(?P<webtoon_id>\d+)(?:&.*)*"


class ChallengeSpecificScraper(AbstractNaverWebtoonScraper):
    """네이버 도전만화만 다운로드받을 수 있는 스크래퍼입니다.

    네이버 정식 연재, 네이버 베스트 도전은 이것으로 다운로드받을 수 없습니다.
    만약 자동으로 네이버 관련 플랫폼을 확인할 수 있는 스크래퍼를 사용하고 싶다면
    NaverWebtoonScraper를 이용하세요.
    """

    BASE_URL = "https://comic.naver.com/challenge"
    TEST_WEBTOON_ID = 818058  # T/F
    WEBTOON_TYPE = "CHALLENGE"
    EPISODE_IMAGES_URL_SELECTOR = "#comic_view_area > div > img"
    URL_REGEX: str = r"(?:https?:\/\/)?comic[.]naver[.]com\/challenge\/list\?(?:.*&)*titleId=(?P<webtoon_id>\d+)(?:&.*)*"


class NaverWebtoonScraper(
    NaverWebtoonSpecificScraper,
    BestChallengeSpecificScraper,
    ChallengeSpecificScraper,
):
    """네이버 웹툰(네이버 웹툰/베스트 도전/도전 만화 무관) 스크래퍼입니다."""
    URL_REGEX: str = r"(?:https?:\/\/)?(?:m[.])?comic[.]naver[.]com\/(?:webtoon|bestChallenge|challenge)\/list\?(?:.*&)*titleId=(?P<webtoon_id>\d+)(?:&.*)*"
    TEST_WEBTOON_IDS = (
        NaverWebtoonSpecificScraper.TEST_WEBTOON_ID,
        BestChallengeSpecificScraper.TEST_WEBTOON_ID,
        ChallengeSpecificScraper.TEST_WEBTOON_ID,
    )

    def __new__(
        cls, *args, **kwargs
    ) -> (
        NaverWebtoonSpecificScraper
        | BestChallengeSpecificScraper
        | ChallengeSpecificScraper
    ):
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
                raise ValueError(f"Unexpacted webtoon type {webtoon_type}. Please contect developer.")
