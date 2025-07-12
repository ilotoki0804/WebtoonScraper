"""Scrape Webtoons from Naver Webtoon."""

from __future__ import annotations

import json
import re
from itertools import count
from json.decoder import JSONDecodeError
from pathlib import Path
from typing import Literal, Self

import httpc
from httpx import HTTPStatusError
from yarl import URL

from ..exceptions import (
    RatingError,
    URLError,
    WebtoonIdError,
)
from ._scraper import Scraper, async_reload_manager


class NaverWebtoonScraper(Scraper[int]):
    """Scrape webtoons from Naver Webtoon."""

    PLATFORM = "naver_webtoon"
    LOGIN_URL = "https://nid.naver.com/nidlogin.login?url=https%3A%2F%2Fcomic.naver.com%2Findex"
    information_vars = (
        Scraper.information_vars
        | Scraper._build_information_dict("raw_articles", "raw_webtoon_info", "episode_audio_urls", subcategory="extra")
        | Scraper._build_information_dict("webtoon_type", "authors", "author_comments", "download_audio", "audio_names")
    )
    comment_counts: dict
    comments: dict

    def __init__(self, webtoon_id: int) -> None:
        self.download_comments = False
        self.top_comments_only = True
        self.download_audio = True
        self.episode_audio_urls: dict[int, str] = {}
        self.audio_names: dict[int, str] = {}
        super().__init__(webtoon_id)
        self.headers.update({"Referer": "https://comic.naver.com/webtoon/"})

    @async_reload_manager
    async def fetch_webtoon_information(self, *, reload: bool = False) -> None:
        headers = self.headers.copy()
        headers.update({"Accept": "application/json, text/plain, */*"})
        with WebtoonIdError.redirect_error(self, error_type=(JSONDecodeError, HTTPStatusError)):
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
        if not self._cookie_set and webtoon_json_info["age"]["type"] == "RATE_18":
            raise RatingError(f"In order to download adult webtoon {self.title}, you need valid cookie. Refer to docs to get additional info.")

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

            current_articles = data["articleList"]
            if previous_articles == current_articles:
                break
            articles += current_articles
            previous_articles = current_articles

        episode_data = {article["no"]: article["subtitle"] for article in articles if not article.get("blindInspection")}

        episode_ids = []
        episode_titles = []
        for zero_index in range(max(episode_data) if episode_data else 0):
            index = zero_index + 1
            # 1. 인덱스가 있는지 확인, 2. subtitle이 존재하는지 확인
            # 만약 에피소스당 데이터가 2개 이상이 되어 튜플을 사용하는 경우
            # 이 코드도 subtitle이 존재하는지를 확인하는 코드로 재정의되어야 함!
            if episode_data.get(index):
                episode_ids.append(index)
                episode_titles.append(episode_data[index])
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

        try:
            audio_url = response.single("audio#bgmPlayer > source", remain_ok=True).attrs["src"]
            assert audio_url
        except (ValueError, KeyError):
            pass
        else:
            self.episode_audio_urls[episode_no] = audio_url

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
        # NOTE: 이 코드는 Scraper.from_url에서 긁어온 코드이기 때문에, 해당 코드가 변경되었을 경우
        # 같이 변경이 필요함.
        try:
            webtoon_type, webtoon_id = cls._extract_webtoon_id(URL(url))
        except Exception as exc:
            raise URLError.from_url(url, cls) from exc

        if webtoon_id is None or webtoon_type is None:
            raise URLError.from_url(url, cls)

        self = cls(webtoon_id)
        self._set_webtoon_type(webtoon_type)  # camelCase 웹툰 타입
        return self

    async def _download_episode_images(self, episode_no: int, image_urls: list[str], episode_directory: Path) -> None:
        if self.download_audio:
            audio_url = self.episode_audio_urls.get(episode_no)
            audio_name = f"{len(image_urls) + 1:03d}.mp3"
            audio_path = episode_directory / audio_name
            if audio_url and not audio_path.exists() and self.directory_manager._snapshot_contents_info(audio_path) is None:
                try:
                    res = await self.client.get(audio_url)
                    with audio_path.open("wb") as f:
                        async for data in res.aiter_bytes():
                            f.write(data)
                except Exception as exc:
                    exc.add_note("Failed to download audio file.")
                    raise
                else:
                    self.audio_names[episode_no] = audio_name
        return await super()._download_episode_images(episode_no, image_urls, episode_directory)

    @classmethod
    def _extract_webtoon_id(cls, url) -> tuple[str, int] | tuple[None, None]:
        match url.host, url.parts, dict(url.query):
            case "naver.me", _, _:
                resolved_url = httpc.get(f"https://naver.me{url.path}").headers["location"]
                return cls._extract_webtoon_id(URL(resolved_url))
            case ("comic.naver.com" | "m.comic.naver.com", ("/", webtoon_type, "list"), {"titleId": webtoon_id_str}):
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
        token = self._cookie_get(value, "XSRF-TOKEN")
        if not token:
            raise ValueError("Cookie does not contain required data.")
        self.headers.update({"Cookie": value, "X-Xsrf-Token": token})
        self.json_headers.update({"Cookie": value, "X-Xsrf-Token": token})

    def _gather_author_comment(self, episode_no: int, response: httpc.Response):
        script = response.single("body > script", remain_ok=True)
        information_script = script.text()
        search_result = re.search(
            r'article: *{"no":\d*,"subtitle":".+?","authorWords":(?P<author_comments_raw>.+?)},\s*currentIndex: *\d*,',
            information_script,
        )
        assert search_result is not None
        self.author_comments[episode_no] = json.loads(search_result.group("author_comments_raw"))

    def _apply_option(self, option: str, value: str) -> None:
        match option:
            case "download-comment" | "download-comments":
                self.download_comments = self._as_boolean(value)
            case "download-all-comment" | "download-all-comments":
                if self._as_boolean(value):
                    self.download_comments = True
                    self.top_comments_only = False
            case "download-audio" | "download-audios":
                self.download_audio = self._as_boolean(value)
            case _:
                super()._apply_option(option, value)
