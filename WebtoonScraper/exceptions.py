"""Used exceptions of WebtoonScraper."""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Self


class WebtoonScraperError(Exception):
    """Base class of every error of custom WebtoonScraper error."""


class DirectoryStateUnmatchedError(WebtoonScraperError):
    """Directory state received from check_directory_state is not desired."""

    @classmethod
    def from_state(cls, container_state, directory: Path | str | None = None):
        message = f"State of directory is {container_state}, which cannot be downloaded."
        if directory:
            message += f"\nDirectory path: {directory if isinstance(directory, str) else directory.absolute()}"
        return cls(message)


class InvalidWebtoonIdError(WebtoonScraperError):
    """Webtoon ID is invalid."""

    @classmethod
    def from_webtoon_id(
        cls, webtoon_id, scraper=None, rating_notice: bool = False, additional: str = ""
    ) -> InvalidWebtoonIdError:
        rating_message = (
            " It might be because rating of the webtoon is not supported. Check if the webtoon is adult-only."
            if rating_notice
            else ""
        )
        if scraper is None:
            return cls(f"Invalid webtoon ID: {webtoon_id!r}." + rating_message + additional)
        assert isinstance(scraper, type)
        return cls(f"Invalid webtoon ID: {webtoon_id!r} for {scraper.__name__}." + rating_message + additional)


class InvalidURLError(WebtoonScraperError):
    """Given URL is not valid."""

    @classmethod
    def from_url(cls, url: str, scraper=None) -> Self:
        if scraper is None:
            return cls(f"URL `{url}` is not matched.")
        assert isinstance(scraper, type)
        return cls(f"{scraper.__qualname__} does not accept URL `{url}`.")


class UnsupportedRatingError(InvalidWebtoonIdError):
    """The webtoon can't be downloaded due to rating."""


class InvalidAuthenticationError(WebtoonScraperError):
    """Provided authentication method is invalid, expired or corrupted."""


class UseFetchEpisode(WebtoonScraperError):
    """`fetch_episode_information` do all."""

    def __init__(self, message: str = ""):
        super().__init__(message or "Use `fetch_episode_information` for get webtoon information.")


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
    """Invalid platform error.

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
            "Please contact developer or make a issue for this." + ("\n" + message if message else "")
        )


class MissingOptionalDependencyError(WebtoonScraperError, ImportError):
    @classmethod
    @contextmanager
    def importing(cls, package_name: str, install_through: str | None = None):
        try:
            yield
        except ImportError as e:
            error_message = (
                f"Package {package_name!r} is not installed in Python environment. "
                f"Please install {package_name!r} though one of following command:\n"
            )
            if install_through:
                error_message += (
                    "pip install -U WebtoonScraper[full]  (RECOMMENDED; download every extra dependency)\n"
                    f"pip install -U WebtoonScraper[{install_through}]  (minimal; download required dependency for this particular download)\n"
                )
            error_message += f"pip install -U {package_name}  (download manually, not recommended since it could install incompatible version)"
            raise cls(error_message) from e


class CommentError(WebtoonScraperError):
    """Errors related to comments."""


class CommentsDownloadOptionError(CommentError):
    """Comment download option is not supported or implemented."""


class UnsupportedCommentsDownloadOptionError(CommentsDownloadOptionError):
    """The comment download option cannot be implemented due to technical difficulties."""


class NotImplementedCommentsDownloadOptionError(CommentsDownloadOptionError, NotImplementedError):
    """This option is not currently implemented, but may be implemented in the future."""
