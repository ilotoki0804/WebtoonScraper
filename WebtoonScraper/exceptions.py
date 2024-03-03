"""Used exceptions of WebtoonScraper."""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Self


class WebtoonScraperError(Exception):
    """Base class of every error of WebtoonScraper."""


class DirectoryStateUnmatchedError(WebtoonScraperError):
    """Directory state recieved from check_directory_state is not wanted."""


class InvalidWebtoonIdError(WebtoonScraperError):
    """Webtoon id is invalid. Or it can be adult webtoon, which is currently not supported in most platform."""

    @classmethod
    def from_webtoon_id(cls, webtoon_id, scraper=None, rating_notice: bool = False) -> InvalidWebtoonIdError:
        rating_message = (
            " It might be because rating of the webtoon is not supported. " "Check if the webtoon is adult-only."
            if rating_notice
            else ""
        )
        if scraper is None:
            return cls(f"Invalid webtoon ID: {webtoon_id}." + rating_message)
        assert isinstance(scraper, type)
        return cls(f"Invalid webtoon ID: {webtoon_id} at {scraper.__qualname__}." + rating_message)


class InvalidURLError(WebtoonScraperError):
    """Given URL is not valid."""

    @classmethod
    def from_url(cls, url: str, scraper=None) -> Self:
        if scraper is None:
            return cls(f"URL `{url}` is not matched.")
        assert isinstance(scraper, type)
        return cls(f"{scraper.__qualname__} does not accept URL `{url}`.")


class UnsupportedRatingError(InvalidWebtoonIdError):
    """The weboon can't be downloaded due to rating."""


class InvalidAuthenticationError(WebtoonScraperError):
    """Provided authentication method is invalid, expired or corrupted."""


class UseFetchEpisode(WebtoonScraperError):
    """`fetch_episode_informations` do all."""

    def __init__(self, message: str = ""):
        super().__init__(message or "Use `fetch_episode_informations` for get webtoon information.")


class InvalidBlogIdError(InvalidWebtoonIdError):
    """Invalid blog id. Maybe there's a typo or blog is closed.

    네이버 블로그의 경우 일반적인 웹툰 플랫폼들과는 다르게 blog id와 category number로
    분리되어 있고 처리 과정 중에 blog id가 잘못됐는지 category number가 잘못됐는지 확인할 수 있는
    로직이 있어서 따로 분리됨.
    """


class InvalidCategoryNoError(InvalidWebtoonIdError):
    """Invalid category number.

    Maybe there's a typo or category is deleted.
    Check docs of InvalidBlogId for full description.
    """


class InvalidPlatformError(WebtoonScraperError):
    """Invalid platfrom error.

    Maybe you didn't select platform or typed invalid parameter.
    """


class UserCanceledError(WebtoonScraperError):
    """User revoked process."""


class InvalidFetchResultError(WebtoonScraperError):
    """Fetch result was invalid."""


class Unreachable(WebtoonScraperError):
    """This code is unreachable."""

    def __init__(self, message: str | None = None):
        super().__init__(
            "This code is meant to be unreachable. If you saw this message, it's clearly error. "
            "Please contect developer or make a issue for this." + ("\n" + message if message else "")
        )
