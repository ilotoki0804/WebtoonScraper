import contextlib
import logging
from typing import Any, Callable, Generic, Iterable, TypeAlias, TypeVar

# import coloredlogs


__github_user_name__ = __title__ = "WebtoonScraper"
__github_project_name__ = __author__ = "ilotoki0804"
__description__ = "Scraping webtoons with ease."
__url__ = "https://github.com/ilotoki0804/WebtoonScraper"
__version_info__ = (3, 1, 4)
__version__ = str.join(".", map(str, __version_info__))

WebtoonId: TypeAlias = (
    "int | str | tuple[int, int] | tuple[str, int] | tuple[str, str]"  # + ' | NaverPostWebtoonId | NaverBlogWebtoonId'
)
EpisodeNoRange: TypeAlias = "tuple[int | None, int | None] | int | None | Iterable[int] | slice"

logger = logging.getLogger("webtoonscraper_logger")
# coloredlogs.install(logger=logger, datefmt='%H:%M:%S')
