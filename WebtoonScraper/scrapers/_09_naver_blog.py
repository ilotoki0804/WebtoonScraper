"""Download Webtoons from Naver Blog."""

from __future__ import annotations

import re
from contextlib import suppress
from itertools import count
from typing import NamedTuple, TypeGuard

from ..base import logger
from ..exceptions import (
    InvalidCategoryNoError,
    InvalidWebtoonIdError,
    UseFetchEpisode,
)
from ._01_scraper import Scraper, reload_manager


class NaverBlogWebtoonId(NamedTuple):
    blog_id: str
    category_no: int


class NaverBlogScraper(Scraper[tuple[str, int]]):
    """Scrape webtoons from Naver Blog."""

    TEST_WEBTOON_ID = NaverBlogWebtoonId("bkid4", 55)  # 상덕
    BASE_URL = "https://m.blog.naver.com"
    URL_REGEX = re.compile(
        r"(?:https?:\/\/)?m[.]blog[.]naver[.]com\/(?P<blog_id>\w+)\?(?:[^&]*&)*categoryNo=(?P<category_no>\d+)(?:&.*)*"
        r"|(?:https?:\/\/)?m[.]blog[.]naver[.]com\/PostList[.]naver\?blogId=(?P<blog_id2>\w+)&(?:[^&]*&)*categoryNo=(?P<category_no2>\d+)(?:&.*)*"
    )
    PLATFORM = "naver_blog"
    INFORMATION_VARS = Scraper.INFORMATION_VARS | dict(
        episodes_image_urls=None,
    )

    def __init__(self, webtoon_id) -> None:
        super().__init__(webtoon_id)
        self.headers.update(Referer="https://m.blog.naver.com/")

    def get_webtoon_directory_name(self) -> str:
        # string은 tuple()을 이용해면 quote가 제거되지 않아서 이 방식을 이용함.
        # 예를 들어 ('hello', 123)을 stringify하면 "('hello', 123)"이 됨.
        blog_id, category_no = self.webtoon_id
        return self._get_safe_file_name(f"{self.title}({blog_id}, {category_no})")

    @reload_manager
    def fetch_webtoon_information(self, *, reload: bool = False) -> None:
        raise UseFetchEpisode()

    @reload_manager
    def fetch_episode_information(self, limit: int = 1000, *, reload: bool = False):
        blog_id, category_no = self.webtoon_id

        url = f"{self.BASE_URL}/api/blogs/{blog_id}/post-list?categoryNo={category_no}&itemCount=24&page={{i}}"

        response = self.hxoptions.get(url.format(i=1)).json()
        if response["isSuccess"] is False:
            raise InvalidWebtoonIdError.from_webtoon_id(self.webtoon_id, type(self))
        if response["result"]["categoryName"] == "전체글" and category_no != 0:
            raise InvalidCategoryNoError("Invalid category number. Maybe there's a typo or category is deleted.")

        fetch_result = response["result"]

        if len(fetch_result["items"]) == limit:
            logger.warning("It seems to go beyond limit. automatically increase limit.")
            return self.fetch_episode_information(limit * 2)

        self.title: str = fetch_result["categoryName"]
        self.webtoon_thumbnail_url: str = fetch_result["items"][0]["thumbnailUrl"] + "?type=ffn640_640"

        items = fetch_result["items"]
        for i in count(2):
            response = self.hxoptions.get(url.format(i=i))

            if current_items := response.json()["result"]["items"]:
                items += current_items
            else:
                break

        image_full_name_regex = re.compile(r"/(\d+)[.]\w{3,}[?]type=w800$", re.VERBOSE)

        def get_integer_picture_name(image_full_name: str) -> int:  # noqa: E306
            result = image_full_name_regex.search(image_full_name)
            if result is None:
                raise ValueError()
            return int(result.group(1))

        self.episode_titles: list[str] = []
        self.episode_ids: list[int] = []
        self.episodes_image_urls: list[list[str]] = []
        for episode in reversed(items):
            self.episode_titles.append(episode["titleWithInspectMessage"])
            self.episode_ids.append(episode["logNo"])

            # 아래 코드보다 콤펙트한 버전. 만약 다운로드가 잘 안 될 경우
            # 이 코드를 비활성화하고 아래 코드를 활성화해서 경고가 나오지는 않는지 확인할 것.
            one_episode_image_urls = [
                thumbnail["encodedThumbnailUrl"] + "?type=w800" for thumbnail in episode["thumbnailList"]
            ]

            # 흔하지 않은 타입에 대한 경고를 포함한 버전.
            # 위의 리스트 컴프리헨션 버전이 실사용 시에 충분히 문제 없이 동작한다면 제거하기.
            # one_episode_image_urls = []
            # for thumbnail in episode['thumbnailList']:
            #     if thumbnail['type'] != 'P':
            #         logger.warning(f'Unknown type {thumbnail["type"]}')
            #     if (thumbnail['videoAniThumbnailUrl']
            #             or thumbnail['videoPlayTime']
            #             or thumbnail['videoThumbnail']
            #             or thumbnail['vrthumbnail']):
            #         logger.warning(f'Unexpected information detected: {thumbnail}')
            #     one_episode_image_urls.append(thumbnail['encodedThumbnailUrl'] + '?type=w800')

            with suppress(ValueError):
                one_episode_image_urls = sorted(one_episode_image_urls, key=get_integer_picture_name)

            self.episodes_image_urls.append(one_episode_image_urls)

    def get_episode_image_urls(self, episode_no):
        return self.episodes_image_urls[episode_no]

    def check_if_legitimate_webtoon_id(self) -> str | None:
        return super().check_if_legitimate_webtoon_id(InvalidWebtoonIdError)

    @classmethod
    def _get_webtoon_id_from_matched_url(cls, matched_url: re.Match) -> tuple[str, int]:
        try:
            return (matched_url.group("blog_id"), int(matched_url.group("category_no")))
        except (TypeError, ValueError):
            return (
                matched_url.group("blog_id2"),
                int(matched_url.group("category_no2")),
            )

    @staticmethod
    def _check_webtoon_id_type(webtoon_id) -> TypeGuard[tuple[str, int]]:
        return (
            isinstance(webtoon_id, tuple)
            and len(webtoon_id) == 2
            and isinstance(webtoon_id[0], str)
            and isinstance(webtoon_id[1], int)
        )
