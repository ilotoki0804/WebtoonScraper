"""Scrape Webtoons from Naver Webtoon."""

from __future__ import annotations

import json
import re
import time
from datetime import datetime
from itertools import count
from json.decoder import JSONDecodeError
from typing import TYPE_CHECKING, ClassVar, Literal

import hxsoup

from ..exceptions import (
    CommentsDownloadOptionError,
    InvalidPlatformError,
    InvalidURLError,
    NotImplementedCommentsDownloadOptionError,
    UnsupportedRatingError,
)
from ._01_scraper import Comment, CommentsDownloadOption, EpisodeComments, Scraper, reload_manager


class AbstractNaverWebtoonScraper(Scraper[int]):
    """Scrape webtoons from Naver Webtoon."""

    BASE_URL: str
    TEST_WEBTOON_ID: int
    WEBTOON_TYPE: ClassVar[Literal["WEBTOON", "BEST_CHALLENGE", "CHALLENGE"]]
    URL_REGEX: re.Pattern[str]
    EPISODE_IMAGES_URL_SELECTOR: ClassVar[str]
    INTERVAL_BETWEEN_EPISODE_DOWNLOAD_SECONDS = 0.5
    PLATFORM = "naver_webtoon"
    COMMENTS_DOWNLOAD_SUPPORTED = True

    def __init__(self, webtoon_id: int) -> None:
        super().__init__(webtoon_id)
        self.headers.update(Referer="https://comic.naver.com/webtoon/")

    @reload_manager
    def fetch_webtoon_information(self, *, reload: bool = False, no_invalid_webtoon_type_error: bool = False) -> None:
        url = f"https://comic.naver.com/api/article/list/info?titleId={self.webtoon_id}"
        try:
            webtoon_json_info = self.hxoptions.get(url).json()
        except JSONDecodeError:
            raise InvalidPlatformError(f"{self.webtoon_id} is invalid webtoon ID.") from None
        # webtoon_json_info['thumbnailUrl']  # 정사각형 썸네일
        webtoon_thumbnail = webtoon_json_info["sharedThumbnailUrl"]  # 실제로 웹툰 페이지에 사용되는 썸네일
        title = webtoon_json_info["titleName"]  # 제목
        webtoon_type = webtoon_json_info["webtoonLevelCode"]  # BEST_CHALLENGE or WEBTOON
        authors = "/".join(author["name"] for author in webtoon_json_info["communityArtists"])

        if webtoon_json_info["age"]["type"] == "RATE_18":
            raise UnsupportedRatingError(
                f"Webtoon {title} is adult webtoon, "
                "which is not supported in NaverWebtoonScraper. "
                f"Thus cannot download {title}."
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

    def get_episode_image_urls(self, episode_no) -> list[str]:
        # sourcery skip: de-morgan
        episode_id = self.episode_ids[episode_no]
        url = f"{self.BASE_URL}/detail?titleId={self.webtoon_id}&no={episode_id}"
        response = self.hxoptions.get(url)
        episode_image_urls_raw = response.soup_select(self.EPISODE_IMAGES_URL_SELECTOR)
        episode_image_urls = [
            element["src"]
            for element in episode_image_urls_raw
            if not ("agerate" in element["src"] or "ctguide" in element["src"])
        ]

        if TYPE_CHECKING:
            episode_image_urls = [url for url in episode_image_urls if isinstance(url, str)]

        script = response.soup_select_one("body > script")
        if script is not None:
            information_script = script.text
            search_result = re.search(
                r'article: *{"no":\d*,"subtitle":".+?","authorWords":(?P<author_comments_raw>.+?)},\s*currentIndex: *\d*,',
                information_script,
            )
            if search_result is None:
                raise ValueError
            self.comments_data[episode_no]["author_comment"] = json.loads(search_result.group("author_comments_raw"))

        return episode_image_urls

    def get_episode_comments(self, episode_no) -> None:
        if self.comments_option is None:
            raise CommentsDownloadOptionError("comments_option is None. Set a proper option to proceed.")
        if self.comments_option.reply:
            raise NotImplementedCommentsDownloadOptionError("The `reply' option is currently unavailable.")

        episode_id = self.episode_ids[episode_no]
        top = self.comments_option.top_comments_only

        def fetch(data: dict | None = None, reply_of: str | int | None = None):
            formatted_time = datetime.now().strftime("%Y%m%d%H%M%S")
            url = (
                "https://apis.naver.com/commentBox/cbox/web_naver_list_jsonp.json"
                f"?ticket=comic&templateId=webtoon&pool=cbox3&_cv={formatted_time}&lang=ko&country=KR"
                f"&objectId={self.webtoon_id}_{episode_id}&categoryId=&pageSize=30&indexSize=10&groupId={self.webtoon_id}"
                f"&listType=OBJECT&pageType=more&page=1&currentPage=1&refresh=true&sort={'BEST' if top else 'NEW'}"
            )
            if reply_of:
                url += "&parentCommentNo={reply_of}"
            if data:
                lastest_comment_id: str = data["lastest_comment_id"]
                current_last_comment_id: str = data["current_last_comment_id"]
                prev_pointer: str = data["prev_pointer"]
                next_pointer: str = data["next_pointer"]
                # url += f"current={'466686102'}&prev={'466692684'}&moreParam.direction=next&moreParam.prev={'0695nz43m35m1'}&moreParam.next={'0695gpq00mnoi'}"
                url += f"&current={current_last_comment_id}&prev={lastest_comment_id}&moreParam.direction=next&moreParam.prev={prev_pointer}&moreParam.next={next_pointer}"
            res = self.hxoptions.get(url)
            return json.loads(res.text[10:-2])["result"]

        if top:
            data = fetch()

            comments_count = data["count"]["total"]
            comments = [self._extract_comment_infomation(comment) for comment in data["commentList"]]
        else:
            lastest_comment_id = None
            comments = []
            while True:
                if lastest_comment_id:
                    data = fetch(
                        {
                            "lastest_comment_id": lastest_comment_id,
                            "current_last_comment_id": current_last_comment_id,  # noqa: F821
                            "prev_pointer": prev_pointer,  # noqa: F821
                            "next_pointer": next_pointer,  # noqa: F821
                        }
                    )
                else:
                    data = fetch()

                prev_pointer = data["morePage"]["prev"]  # noqa: F841
                next_pointer = data["morePage"]["next"]
                end_pointer = data["morePage"]["end"]
                comments_count = data["count"]["total"]
                lastest_comment_id = lastest_comment_id or data["commentList"][0]["commentNo"]
                current_last_comment_id = data["commentList"][-1]["commentNo"]  # noqa: F841
                comments += [self._extract_comment_infomation(comment) for comment in data["commentList"]]
                if next_pointer == end_pointer:
                    break

        episode_comments: EpisodeComments = {
            "download_option": self.comments_option._asdict(),
            "comment_count": comments_count,
            "comments": comments,
        }
        self.comments_data[episode_no].update(episode_comments)

    def check_if_legitimate_webtoon_id(self) -> str | None:
        return super().check_if_legitimate_webtoon_id((InvalidPlatformError, UnsupportedRatingError))

    def _extract_comment_infomation(self, comment_data: dict) -> Comment:
        return {
            "comments_id": comment_data["commentNo"],
            # "reply_to": comment_data["parentCommentNo"],
            "reply_count": int(comment_data["replyCount"]),
            "comment": comment_data["contents"],
            "username": comment_data["userName"],  # or "shareCommentUserName"
            "likes": int(comment_data["sympathyCount"]),
            "dislikes": int(comment_data["antipathyCount"]),
            "last_modified": comment_data["modTime"],
            "created": comment_data["regTime"],
            "replies": [],
        }


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
    URL_REGEX = re.compile(
        r"(?:https?:\/\/)?(?:m[.])?comic[.]naver[.]com\/webtoon\/list\?(?:.*&)*titleId=(?P<webtoon_id>\d+)(?:&.*)*"
    )


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
    URL_REGEX = re.compile(
        r"(?:https?:\/\/)?comic[.]naver[.]com\/bestChallenge\/list\?(?:.*&)*titleId=(?P<webtoon_id>\d+)(?:&.*)*"
    )


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
    URL_REGEX = re.compile(
        r"(?:https?:\/\/)?comic[.]naver[.]com\/challenge\/list\?(?:.*&)*titleId=(?P<webtoon_id>\d+)(?:&.*)*"
    )


class NaverWebtoonScraper(
    NaverWebtoonSpecificScraper,
    BestChallengeSpecificScraper,
    ChallengeSpecificScraper,
):
    """네이버 웹툰(네이버 웹툰/베스트 도전/도전 만화 무관) 스크래퍼입니다."""

    URL_REGEX = re.compile(
        r"(?:https?:\/\/)?(?:m[.])?comic[.]naver[.]com\/(?P<webtoon_type>webtoon|bestChallenge|challenge)\/list\?(?:.*&)*titleId=(?P<webtoon_id>\d+)(?:&.*)*"
        r"|(?:https?:\/\/)?(?P<short_url>naver[.]me\/\w+)"
    )
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
                raise ValueError(f"Unexpacted webtoon type {webtoon_type}. Please contect developer.")

    @classmethod
    def from_url(
        cls, url: str
    ) -> NaverWebtoonSpecificScraper | BestChallengeSpecificScraper | ChallengeSpecificScraper:
        matched = cls.URL_REGEX.match(url)
        if matched is None:
            raise InvalidURLError.from_url(url, cls)

        try:
            webtoon_id: int = int(matched.group("webtoon_id"))
            webtoon_type: str = matched.group("webtoon_type")
        except Exception as e:
            short_url = matched.group("short_url")
            if short_url is None:
                raise InvalidURLError.from_url(url, cls) from e
            full_url = hxsoup.get("https://" + short_url).headers["location"]
            return cls.from_url(full_url)

        match webtoon_type:
            case "webtoon":
                return NaverWebtoonSpecificScraper(webtoon_id)
            case "bestChallenge":
                return BestChallengeSpecificScraper(webtoon_id)
            case "challenge":
                return ChallengeSpecificScraper(webtoon_id)
            case _:
                raise ValueError(f"Unexpacted webtoon type {webtoon_type}. Please contect developer.")
