"""웹툰을 다운로드하는 데에 직접적으로 사용되는 스크래퍼들을 모아놓은 모듈입니다.

가장 근간이 되는 Scraper 클래스는 _scraper.py에 있고,
각각의 플랫폼에 대한 상세한 정의는 여러 파일이 나누어져 각각 정의되어 있습니다.
"""

__all__ = [
    "Scraper",
    "EpisodeRange",
    "ExtraInfoScraper",
    "BestChallengeSpecificScraper",
    "ChallengeSpecificScraper",
    "NaverWebtoonScraper",
    "NaverWebtoonSpecificScraper",
    "LezhinComicsScraper",
]

from ._helpers import EpisodeRange, ExtraInfoScraper
from ._scraper import Scraper
from ._naver_webtoon import (
    BestChallengeSpecificScraper,
    ChallengeSpecificScraper,
    NaverWebtoonScraper,
    NaverWebtoonSpecificScraper,
)

from ._lezhin_comics import LezhinComicsScraper
