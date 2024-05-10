"""웹툰을 다운로드하는 데에 직접적으로 사용되는 스크래퍼들을 모아놓은 모듈입니다.

가장 근간이 되는 Scraper 클래스는 _01_scraper.py에 있고,
각각의 플랫폼에 대한 상세한 정의는 여러 파일이 나누어져 각각 정의되어 있습니다.
"""

__all__ = [
    "CommentsDownloadOption",
    "ExistingEpisodePolicy",
    "Scraper",
    "BestChallengeSpecificScraper",
    "ChallengeSpecificScraper",
    "NaverWebtoonScraper",
    "NaverWebtoonSpecificScraper",
    "WebtoonsDotcomScraper",
    "BufftoonScraper",
    "NaverPostScraper",
    "NaverPostWebtoonId",
    "NaverGameScraper",
    "LezhinComicsScraper",
    "KakaopageScraper",
    "NaverBlogScraper",
    "NaverBlogWebtoonId",
    "TistoryScraper",
    "TistoryWebtoonId",
    "KakaoWebtoonScraper",
]

from ._01_scraper import CommentsDownloadOption, ExistingEpisodePolicy, Scraper
from ._02_naver_webtoon import (
    BestChallengeSpecificScraper,
    ChallengeSpecificScraper,
    NaverWebtoonScraper,
    NaverWebtoonSpecificScraper,
)
from ._03_webtoon_originals import WebtoonsDotcomScraper
from ._04_bufftoon import BufftoonScraper
from ._05_naver_post import NaverPostScraper, NaverPostWebtoonId
from ._06_naver_game import NaverGameScraper
from ._07_lezhin_comics import LezhinComicsScraper
from ._08_kakaopage import KakaopageScraper
from ._09_naver_blog import NaverBlogScraper, NaverBlogWebtoonId
from ._10_tistory import TistoryScraper, TistoryWebtoonId
from ._11_kakao_webtoon import KakaoWebtoonScraper
