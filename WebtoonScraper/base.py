"""WebtoonScraper의 기본 정보들을 모아놓은 모듈입니다. circular import를 피하기 위해 필요합니다."""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING

from rich.console import Console
from rich.logging import RichHandler

if TYPE_CHECKING:
    from WebtoonScraper.scrapers import Scraper

__version__ = "5.7.3"
platforms: dict[str, type[Scraper]] = {}
console = Console()

logger = logging.getLogger("WebtoonScraper")
logger.addHandler(RichHandler(show_time=False, show_path=False))
logger.setLevel(logging.INFO)


def get_default_thread_number() -> int:
    # 우선 THREAD_NUMBER environ이 있는지 확인
    # 이 값이 계속 변할 수 있기에 정확한 값을 불러오려면
    # 함수가 필요함.
    process_number = os.getenv("THREAD_NUMBER")
    if process_number and process_number != "0":
        return int(process_number)

    # 그 외의 경우 스레드 개수의 절반을 값으로 사용
    cpu_count = os.cpu_count()
    process_number = 1 if cpu_count is None or cpu_count < 2 else max(cpu_count // 2, 10)
    return process_number
