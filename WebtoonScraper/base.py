from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Iterable, TypeAlias

from rich.logging import RichHandler

__url__ = "https://github.com/ilotoki0804/WebtoonScraper"
__version_info__ = (4, 0, 0, "a", 1)
__version__ = str.join(".", map(str, __version_info__[:3])) + "".join(map(str, __version_info__[3:]))

if TYPE_CHECKING:
    from .scrapers import NaverBlogWebtoonId as _NaverBlogWebtoonId
    from .scrapers import NaverPostWebtoonId as _NaverPostWebtoonId

WebtoonId: TypeAlias = (
    "int | str | tuple[int, int] | tuple[str, int] | tuple[str, str] | _NaverPostWebtoonId | _NaverBlogWebtoonId"
)
EpisodeNoRange: TypeAlias = "tuple[int | None, int | None] | int | None | Iterable[int] | slice"

logger = logging.getLogger("webtoonscraper_logger")
logger.handlers = [RichHandler(show_time=False, show_path=False)]
logger.setLevel(logging.INFO)
