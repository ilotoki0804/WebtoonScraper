from __future__ import annotations

import json
import re
from collections import defaultdict
from datetime import datetime
from itertools import count
from typing import TYPE_CHECKING, NamedTuple, TypedDict

from hxsoup import SoupedResponse

from ._scraper import ExtraInfoScraper

if TYPE_CHECKING:
    from typing import Required

    from WebtoonScraper.scrapers._naver_webtoon import AbstractNaverWebtoonScraper


class Comment(TypedDict, total=False):
    comments_id: int | str
    reply_count: int | None
    username: Required[str]
    user_id: object
    likes: int
    dislikes: int
    last_modified: str
    created: str
    comment: Required[str]
    replies: list[Comment]


class EpisodeComments(TypedDict, total=False):
    download_option: dict
    comments: list[Comment]
    comment_count: int
    author_comment: str


class NaverWebtoonCommentsDownloadOption(NamedTuple):
    """댓글을 다운로드할 때 어떤 방식으로 다운로드할지 결정합니다.

    Some option can be not supported by scraper.
    Default setting(top comments only, no reply) are always supported and strongly recommended.
    """

    top_comments_only: bool = True
    """Download top comments only. Download all comments if False."""

    # reply: bool = False
    # """Download replies of comments."""


class NaverWebtoonMetaInfoScraper(ExtraInfoScraper):
    def __init__(self, comments_option: NaverWebtoonCommentsDownloadOption | None = None):
        self.comments_data: defaultdict[int, EpisodeComments] = defaultdict(EpisodeComments)
        self.comments_option: NaverWebtoonCommentsDownloadOption | None = comments_option

    def gather_author_comment(self, episode_no: int, response: SoupedResponse):
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

    def fetch_episode_comments(self, episode_no: int, scraper: AbstractNaverWebtoonScraper):
        if self.comments_option is None:
            return
            # raise CommentsDownloadOptionError("comments_option is None. Set a proper option to proceed.")

        is_official = scraper.WEBTOON_TYPE == "WEBTOON"

        episode_id = scraper.episode_ids[episode_no]
        top = self.comments_option.top_comments_only

        def fetch(parameter_data: dict | None = None, reply_of: str | int | None = None):
            parameters = dict(
                ticket="comic" if is_official else "comic_challenge",
                templateId="webtoon" if is_official else "creators",
                pool="cbox3",  # cspell: ignore cbox
                _cv=datetime.now().strftime("%Y%m%d%H%M%S"),
                lang="ko",
                country="KR",
                objectId=f"{scraper.webtoon_id}_{episode_id}",
                pageSize="30",
                indexSize="10",
                groupId=scraper.webtoon_id,
                listType="OBJECT",
                pageType="more",
                page="1",
                currentPage="1",
                refresh="true",
                sort="BEST" if top else "NEW",
            )
            if reply_of is not None:
                parameters.update(parentCommentNo=str(reply_of))
            if parameter_data:
                latest_comment_id: str = parameter_data["latest_comment_id"]
                current_last_comment_id: str = parameter_data["current_last_comment_id"]
                prev_pointer: str = parameter_data["prev_pointer"]
                next_pointer: str = parameter_data["next_pointer"]

                parameters.update(
                    {
                        "current": current_last_comment_id,
                        "prev": latest_comment_id,
                        "moreParam.direction": "next",
                        "moreParam.prev": prev_pointer,
                        "moreParam.next": next_pointer,
                        "page": str(parameter_data["index"] + 1),
                        "currentPage": str(parameter_data["index"] or 1),
                    }
                )

            res = scraper.hxoptions.get(
                "https://apis.naver.com/commentBox/cbox/web_naver_list_jsonp.json", params=parameters
            )
            return json.loads(res.text[10:-2])["result"]

        if top:
            data = fetch()

            comments_count = data["count"]["total"]
            comments = [self._extract_comment_information(comment) for comment in data["commentList"]]
        else:
            latest_comment_id = None
            comments = []
            for i in count(0):
                if latest_comment_id:
                    data = fetch(
                        {
                            "latest_comment_id": latest_comment_id,
                            "current_last_comment_id": current_last_comment_id,  # noqa: F821 # type: ignore
                            "prev_pointer": prev_pointer,  # noqa: F821 # type: ignore
                            "next_pointer": next_pointer,  # noqa: F821 # type: ignore
                            "index": i,
                        }
                    )
                else:
                    data = fetch()

                prev_pointer = data["morePage"]["prev"]  # noqa: F841
                next_pointer = data["morePage"]["next"]
                end_pointer = data["morePage"]["end"]
                start_pointer = data["morePage"]["start"]
                comments_count = data["count"]["total"]
                latest_comment_id = latest_comment_id or data["commentList"][0]["commentNo"]
                current_last_comment_id = data["commentList"][-1]["commentNo"]  # noqa: F841
                comments += [self._extract_comment_information(comment) for comment in data["commentList"]]
                if next_pointer == end_pointer or end_pointer == start_pointer:
                    # end_pointer와 start_pointer가 같을 때 next_pointer가 이상한 값을 지시할 수 있음.
                    break

        episode_comments: EpisodeComments = {
            "download_option": self.comments_option._asdict(),
            "comment_count": comments_count,  # type: ignore
            "comments": comments,
        }
        self.comments_data[episode_no].update(episode_comments)

    def _extract_comment_information(self, comment_data: dict) -> Comment:
        return {
            # "sort_value": comment_data["sortValue"],
            "comments_id": comment_data["commentNo"],
            "reply_count": int(comment_data["replyCount"]),
            "username": comment_data["userName"],  # or "shareCommentUserName"
            "user_id": comment_data["userIdNo"],  # or "idNo" or "profileUserId"
            "likes": int(comment_data["sympathyCount"]),
            "dislikes": int(comment_data["antipathyCount"]),
            "last_modified": comment_data["modTime"],
            "created": comment_data["regTime"],
            "comment": comment_data["contents"],
            "replies": [],
        }
