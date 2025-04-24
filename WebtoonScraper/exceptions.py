"""Used exceptions of WebtoonScraper."""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING

from httpx import HTTPStatusError

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Self

    from .scrapers import Scraper as _Scraper


class WebtoonScraperError(Exception):
    """Base class of every error of custom WebtoonScraper error."""


class DirectoryStateError(WebtoonScraperError):
    """Directory state received from check_directory_state is not desired."""

    @classmethod
    def from_state(cls, container_state, directory: Path | str | None = None):
        message = f"State of directory is {container_state}, which cannot be downloaded."
        if directory:
            message += f"\nDirectory path: {directory if isinstance(directory, str) else directory.absolute()}"
        return cls(message)


class WebtoonIdError(WebtoonScraperError):
    """Webtoon ID is invalid."""

    @classmethod
    @contextmanager
    def redirect_error(cls, scraper: _Scraper, rating_notice=False, error_type: type[BaseException] | tuple[type[BaseException], ...] = HTTPStatusError):
        error = None
        try:
            try:
                yield
            except* error_type as exc:
                error = exc
        except error_type as exc:
            error = exc

        if error:
            if isinstance(error, HTTPStatusError):
                response = error.response
                reason = response.reason_phrase

                if response.has_redirect_location:
                    reason += f" to {response.url}"

                additional = f" (HTTP {error.response.status_code}{' ' * bool(reason)}{reason})"
            else:
                additional = ""

            raise cls.from_webtoon_id(
                webtoon_id=scraper.webtoon_id,
                scraper=type(scraper),
                rating_notice=rating_notice,
                additional=additional,
            ) from None

    @classmethod
    def from_webtoon_id(cls, webtoon_id, scraper=None, rating_notice: bool = False, additional: str = "") -> WebtoonIdError:
        rating_message = " It might be because rating of the webtoon is not supported. Check if the webtoon is adult-only." if rating_notice else ""
        if scraper is None:
            return cls(f"Invalid webtoon ID: {webtoon_id!r}.{rating_message}{additional}")
        assert isinstance(scraper, type)
        return cls(f"Invalid webtoon ID: {webtoon_id!r} for {scraper.__name__}.{rating_message}{additional}")


class URLError(WebtoonScraperError):
    """Given URL is not valid."""

    @classmethod
    def from_url(cls, url: str, scraper=None) -> Self:
        if scraper is None:
            return cls(f"URL `{url}` is not matched.")
        assert isinstance(scraper, type)
        return cls(f"{scraper.__qualname__} does not accept URL `{url}`.")


class WebtoonError(WebtoonScraperError):
    """The webtoon cannot be downloaded by Scraper."""


class RatingError(WebtoonError):
    """The webtoon can't be downloaded due to rating."""


class AuthenticationError(WebtoonScraperError):
    """Provided authentication method is invalid, expired or corrupted."""


class UseFetchEpisode(WebtoonScraperError):
    """`fetch_episode_information` do all."""

    def __init__(self, message: str = ""):
        super().__init__(message or "Use `fetch_episode_information` for get webtoon information.")


class PlatformError(WebtoonScraperError):
    """Invalid platform error.

    Maybe you didn't select platform or typed invalid parameter.
    """


class Unreachable(WebtoonScraperError):
    """This code is unreachable."""

    def __init__(self, message: str | None = None):
        super().__init__(
            "This code is meant to be unreachable. If you saw this message, it's clearly error. "
            "Please contact developer or make a issue for this." + ("\n" + message if message else "")
        )


class DependencyError(WebtoonScraperError, ImportError):
    @classmethod
    @contextmanager
    def importing(cls, package_name: str, install_through: str | None = None):
        try:
            yield
        except ImportError as exc:
            error_message = f"Package {package_name!r} is not installed in Python environment. Please install {package_name!r} though one of following command:\n"
            if install_through:
                error_message += (
                    "pip install -U WebtoonScraper[full]  (RECOMMENDED; download every extra dependency)\n"
                    f"pip install -U WebtoonScraper[{install_through}]  (minimal; download required dependency for this particular download)\n"
                )
            error_message += f"pip install -U {package_name}  (download manually, not recommended since it could install incompatible version)"
            raise cls(error_message) from exc
