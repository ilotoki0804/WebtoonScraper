"""Download Webtoons from Kakaopage."""

from __future__ import annotations

from itertools import count
from typing import NamedTuple
from urllib.parse import unquote
import re

from .A_scraper import Scraper, reload_manager


class TistoryWebtoonId(NamedTuple):
    blog_id: str
    category: str


class TistoryScraper(Scraper[TistoryWebtoonId]):
    """Scrape webtoons from Kakaopage."""

    BASE_URL = "https://tistory.com/"
    IS_CONNECTION_STABLE = True
    TEST_WEBTOON_ID = ("doldistudio", "진돌만화")
    # 티스토리는 커스텀 URL을 쓰는 경우도 많기에 이 regex에 걸리지 않을 수도 있음.
    URL_REGEX = r"(?:https?:\/\/)?(?P<blog_id>.*?)[.]tistory[.]com\/category\/(?P<category>[^?]*)"

    def get_webtoon_directory_name(self) -> str:
        # category_no는 거의 대부분 title과 같기 때문에 사용하지 않음.
        blog_id, category_no = self.webtoon_id

        # 만약 이 코드를 수정할 것이라면 NaverBlogScraper에 있는 정보 참고.
        return f"{self.title}({blog_id})"

    @reload_manager
    def fetch_webtoon_information(self, *, reload: bool = False) -> None:
        blog_id, category = self.webtoon_id
        res = self.hxoptions.get(f"https://{blog_id}.tistory.com/category/{category}")
        # title = res.soup_select_one("span.txt_section", True).text  # 돌디스튜디오 한정
        # title = res.soup_select_one("span > h1", True).text  # 일반적인 티스토리
        title = unquote(category)

        thumbnail_raw = res.soup_select_one(
            "#content_search > div > div > ul > li > a > div", no_empty_result=True
        )["style"]
        assert isinstance(thumbnail_raw, str)
        thumbnail_url = re.search("(?<=fname=).+(?=')", thumbnail_raw)
        assert thumbnail_url is not None
        thumbnail_url = thumbnail_url.group(0)

        # 혹은 146x146 썸네일을 사용하는 것이 낫다고 판단된다면 다음의 코드를 사용할 것.
        # thumbnail_url = re.search("(?<='//).+(?=')", thumbnail_raw)
        # thumbnail_url = "https://" + thumbnail_url.group(0)

        self.title = title
        self.webtoon_thumbnail = thumbnail_url

    @reload_manager
    def fetch_episode_informations(self, *, reload: bool = False) -> None:
        blog_id, category = self.webtoon_id

        episode_titles = []
        episode_ids = []
        for i in count(1):
            res = self.hxoptions.get(
                f"https://{blog_id}.tistory.com/category/{category}?page={i}"
            )

            if not res.soup_select(
                "#content_search > div > div > ul > li > a.link_thumb"
            ):
                break

            episode_titles += [
                element.text
                for element in res.soup_select(
                    "#content_search > div > div > ul > li > a > div > p.txt_thumb"
                )
            ]
            episode_ids += [
                i["href"]
                for i in res.soup_select(
                    "#content_search > div > div > ul > li > a.link_thumb"
                )
            ]

        self.episode_titles = episode_titles[::-1]
        self.episode_ids = episode_ids[::-1]

    def get_episode_image_urls(self, episode_no) -> list[str]:
        blog_id, category = self.webtoon_id
        episode_id = self.episode_ids[episode_no]

        # episode_id 자체에 /가 포함되어 있으니 /를 입력할 필요 없음.
        res = self.hxoptions.get(f"https://{blog_id}.tistory.com{episode_id}")

        return [
            url
            for i in res.soup_select("figure > span > img")
            if isinstance(url := i["src"], str)
        ]  # 타입을 확실하게 하기 위해 if문이 필요함.
