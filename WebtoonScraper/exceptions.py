"""Used exceptions of WebtoonScraper."""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING

from httpx import HTTPStatusError

if TYPE_CHECKING:
    from .scrapers import Scraper as _Scraper
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
    @contextmanager
    def redirect_error(cls, scraper: _Scraper, rating_notice=False, error_type: type[BaseException] | tuple[type[BaseException], ...] = HTTPStatusError):
        try:
            yield
        except error_type as exc:
            if isinstance(exc, HTTPStatusError):
                reason = exc.response.reason_phrase
                raise cls.from_webtoon_id(
                    webtoon_id=scraper.webtoon_id,
                    scraper=type(scraper),
                    rating_notice=rating_notice,
                    additional=f" (HTTP {exc.response.status_code}{' ' * bool(reason)}{reason})",
                ) from None
            else:
                raise cls.from_webtoon_id(
                    webtoon_id=scraper.webtoon_id,
                    scraper=type(scraper),
                    rating_notice=rating_notice,
                ) from None

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
            return cls(f"Invalid webtoon ID: {webtoon_id!r}.{rating_message}{additional}")
        assert isinstance(scraper, type)
        return cls(f"Invalid webtoon ID: {webtoon_id!r} for {scraper.__name__}.{rating_message}{additional}")


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
        except ImportError as exc:
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
            raise cls(error_message) from exc


class CommentError(WebtoonScraperError):
    """Errors related to comments."""


class CommentsDownloadOptionError(CommentError):
    """Comment download option is not supported or implemented."""


class UnsupportedCommentsDownloadOptionError(CommentsDownloadOptionError):
    """The comment download option cannot be implemented due to technical difficulties."""


class NotImplementedCommentsDownloadOptionError(CommentsDownloadOptionError, NotImplementedError):
    """This option is not currently implemented, but may be implemented in the future."""
