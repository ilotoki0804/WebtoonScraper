"""WebtoonScraper의 기본 정보들을 모아놓은 모듈입니다. circular import를 피하기 위해 필요합니다."""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING

from rich.logging import RichHandler

if TYPE_CHECKING:
    from WebtoonScraper.scrapers import Scraper

__url__ = "https://github.com/ilotoki0804/WebtoonScraper"
__version__ = "4.2.0"

_CPU_COUNT = os.cpu_count()
DEFAULT_PROCESS_NUMBER = 1 if _CPU_COUNT is None or _CPU_COUNT < 2 else max(_CPU_COUNT // 2, 10)

logger = logging.getLogger("WebtoonScraper")
logger.handlers = [RichHandler(show_time=False, show_path=False)]
logger.setLevel(logging.INFO)

platforms: dict[str, type[Scraper]] = {}
