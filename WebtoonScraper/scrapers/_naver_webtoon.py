"""Scrape Webtoons from Naver Webtoon."""

from __future__ import annotations

import json
import re
from itertools import count
from json.decoder import JSONDecodeError
from typing import Literal, Self

import httpc
from httpx import HTTPStatusError
from yarl import URL

from ..exceptions import (
    InvalidURLError,
    InvalidWebtoonIdError,
    UnsupportedRatingError,
)
from ..base import logger
from ._scraper import Scraper, async_reload_manager


class NaverWebtoonScraper(Scraper[int]):
    """Scrape webtoons from Naver Webtoon."""
    PLATFORM = "naver_webtoon"
    DOWNLOAD_INTERVAL = 0.5
    COMMENTS_DOWNLOAD_SUPPORTED = True
    information_vars = (
        Scraper.information_vars
        | Scraper._build_information_dict("raw_articles", "raw_webtoon_info", subcategory="extra")
        | Scraper._build_information_dict("webtoon_type", "authors", "author_comments")
    )
    comment_counts: dict
    comments: dict

    def __init__(self, webtoon_id: int) -> None:
        self.download_comments = False
        self.top_comments_only = True
        super().__init__(webtoon_id)
        self.headers.update({"Referer": "https://comic.naver.com/webtoon/"})

    @async_reload_manager
    async def fetch_webtoon_information(self, *, reload: bool = False) -> None:
        headers = self.headers.copy()
        headers.update({"Accept": "application/json, text/plain, */*"})
        with InvalidWebtoonIdError.redirect_error(self, error_type=(JSONDecodeError, HTTPStatusError)):
            url = f"https://comic.naver.com/api/article/list/info?titleId={self.webtoon_id}"
            res = await self.client.get(url, headers=headers)
            webtoon_json_info: dict = res.json()

        # 정보 저장
        self.webtoon_thumbnail_url = webtoon_json_info["sharedThumbnailUrl"]
        self.title = webtoon_json_info["titleName"]  # 제목
        self.authors = [author["name"] for author in webtoon_json_info["communityArtists"]]
        self.author = "/".join(self.authors)
        # 정사각형 썸네일은 thumbnailUrl이고, 긴 비율의 썸네일은 sharedThumbnailUrl이다.
        self.webtoon_type: Literal["WEBTOON", "BEST_CHALLENGE", "CHALLENGE"] = webtoon_json_info["webtoonLevelCode"]
        self._set_webtoon_type(self.webtoon_type)  # SCREAMING_CASE 웹툰 타입
        self.raw_webtoon_info = webtoon_json_info

        # 심의 확인
        if not self.cookie and webtoon_json_info["age"]["type"] == "RATE_18":
            raise UnsupportedRatingError(
                f"In order to download adult webtoon {self.title}, you need valid cookie. Refer to docs to get additional info."
            )

    @async_reload_manager
    async def fetch_episode_information(self, *, reload: bool = False) -> None:
        articles = []
        previous_articles = []
        for i in count(1):
            url = f"https://comic.naver.com/api/article/list?titleId={self.webtoon_id}&page={i}&sort=ASC"
            try:
                data = (await self.client.get(url)).json()
            except JSONDecodeError:
                # fetch_webtoon_information은 지원하지 않는 rating일 때 오류를 낸다.
                # 만약 fetch_webtoon_information보다 fetch_episode_information가 먼저
                # 실행되었을 경우 UnsupportedWebtoonRatingError를 미처 내지 못했을 수 있다.
                # 그런 경우인지 확인한 후 만약 지원하지 않는 rating에 대한 오류가 아니었다면
                # 다른 버그로 간주하고 다시 raise한다.
                await self.fetch_webtoon_information()
                raise

            # TODO: 혹이 HTTP 304를 이용하지는 않을까? 한번 코드를 돌려 보며 확인해야 한다.
            current_articles = data["articleList"]
            if previous_articles == current_articles:
                break
            articles += current_articles
            previous_articles = current_articles

        raw_episode_ids = set(article["no"] for article in articles)
        raw_episode_ids_iter = (article["no"] for article in articles)
        raw_episode_titles_iter = (article["subtitle"] for article in articles)
        episode_ids = []
        episode_titles = []
        for zero_index in range(max(raw_episode_ids)):
            index = zero_index + 1
            if index in raw_episode_ids:
                episode_ids.append(next(raw_episode_ids_iter))
                episode_titles.append(next(raw_episode_titles_iter))
            else:
                episode_ids.append(None)
                episode_titles.append(None)
        self.episode_titles = episode_titles
        self.episode_ids = episode_ids
        self.raw_articles = articles
        self.author_comments = {}

    async def get_episode_image_urls(self, episode_no: int) -> list[str] | None:
        episode_id = self.episode_ids[episode_no]
        url = f"{self.base_url}/detail?titleId={self.webtoon_id}&no={episode_id}"

        try:
            response = await self.client.get(url)
        except HTTPStatusError:
            return None

        self._gather_author_comment(episode_no, response)

        episode_image_urls: list[str] = []
        for element in response.match(self.image_selector):
            image_url = element.attrs.get("src")
            assert image_url is not None
            if "agerate" in image_url or "ctguide" in image_url:  # cspell: ignore agerate ctguide
                continue
            episode_image_urls.append(image_url)

        try:
            get_episode_comments = self.extra_info_scraper.get_episode_comments  # type: ignore
        except AttributeError:
            pass
        else:
            # 댓글을 asynchronously 다운로드하고 싶은 경우.
            # await self._tasks.put(asyncio.create_task(get_episode_comments(episode_no, self)))
            await get_episode_comments(episode_no, self)

        return episode_image_urls

    @classmethod
    def from_url(cls, url: str) -> Self:
        try:
            webtoon_type, webtoon_id = cls._extract_webtoon_id(URL(url))
        except Exception as exc:
            raise InvalidURLError.from_url(url, cls) from exc

        if webtoon_id is None or webtoon_type is None:
            raise InvalidURLError.from_url(url, cls)

        self = cls(webtoon_id)
        self._set_webtoon_type(webtoon_type)  # camelCase 웹툰 타입
        return self

    @classmethod
    def _extract_webtoon_id(cls, url) -> tuple[str, int] | tuple[None, None]:
        match url.host, url.parts, dict(url.query):
            case "naver.me", _, _:
                resolved_url = httpc.get(f"https://naver.me{url.path}").headers["location"]
                return cls._extract_webtoon_id(URL(resolved_url))
            case (
                "comic.naver.com" | "m.comic.naver.com",
                ("/", webtoon_type, "list"),
                {"titleId": webtoon_id_str}
            ):
                return webtoon_type, int(webtoon_id_str)
            case _:
                return None, None

    def _set_webtoon_type(
        self,
        webtoon_type: Literal["WEBTOON", "BEST_CHALLENGE", "CHALLENGE", "webtoon", "bestChallenge", "challenge"] | str,
    ) -> None:
        match webtoon_type:
            case "WEBTOON" | "webtoon":
                self.image_selector = "#sectionContWide > img"
                self.path_name = "webtoon"
                self.base_url = "https://comic.naver.com/webtoon"
            case "BEST_CHALLENGE" | "bestChallenge":
                self.image_selector = "#comic_view_area > div > img"
                self.path_name = "bestChallenge"
                self.base_url = "https://comic.naver.com/bestChallenge"
            case "CHALLENGE" | "challenge":
                self.image_selector = "#comic_view_area > div > img"
                self.path_name = "challenge"
                self.base_url = "https://comic.naver.com/challenge"

    def _set_cookie(self, value: str) -> None:
        matched = re.search(r"XSRF-TOKEN=([^;]+);", value)
        if not matched:
            raise ValueError("Cookie does not contain required data.")
        self.headers.update({"Cookie": value, "X-Xsrf-Token": matched[1]})

    def _gather_author_comment(self, episode_no: int, response: httpc.Response):
        script = response.single("body > script", remain_ok=True)
        information_script = script.text()
        search_result = re.search(
            r'article: *{"no":\d*,"subtitle":".+?","authorWords":(?P<author_comments_raw>.+?)},\s*currentIndex: *\d*,',
            information_script,
        )
        assert search_result is not None
        self.author_comments[episode_no] = json.loads(search_result.group("author_comments_raw"))

    def _apply_options(self, options: dict[str, str], /) -> None:
        def raw_string_to_boolean(raw_string: str) -> bool:
            """boolean으로 변경합니다.

            `true`나 `false`면 각각 True와 False로 처리하고,
            정수라면 0이면 False, 나머지는 True로 처리합니다.

            그 외의 값은 ValueError를 일으킵니다.
            """
            if raw_string.lower() == "true":
                value = True
            elif raw_string.lower() == "false":
                value = False
            else:
                try:
                    value = bool(int(raw_string))
                except ValueError:
                    raise ValueError(f"Invalid value for boolean: {raw_string}") from None
            return value

        for option, raw_value in options.items():
            option = option.upper().replace("-", "_").strip()
            if option.removesuffix("S") == "DOWNLOAD_COMMENT":
                self.download_comments = raw_string_to_boolean(raw_value)
            if option.removesuffix("S") == "DOWNLOAD_ALL_COMMENT":
                option_true = not raw_string_to_boolean(raw_value)
                if option_true:
                    self.download_comments = option_true
                    self.top_comments_only = option_true
            else:
                logger.warning(f"Unknown option for {type(self).__name__}: {option!r}. value: {raw_value!r}")
