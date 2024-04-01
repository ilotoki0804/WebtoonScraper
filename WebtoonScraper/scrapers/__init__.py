"""웹툰을 다운로드하는 데에 직접적으로 사용되는 스크래퍼들을 모아놓은 모듈입니다.

가장 근간이 되는 Scraper 클래스는 A_scraper.py에 있고,
각각의 플랫폼에 대한 상세한 정의는 여러 파일이 나누어져 각각 정의되어 있습니다.
"""

from .A_scraper import CommentsDownloadOption, ExistingEpisodePolicy, Scraper
from .B_naver_webtoon import (
    BestChallengeSpecificScraper,
    ChallengeSpecificScraper,
    NaverWebtoonScraper,
    NaverWebtoonSpecificScraper,
)
from .D_webtoon_originals import WebtoonsDotcomScraper
from .G_bufftoon import BufftoonScraper
from .H_naver_post import NaverPostScraper, NaverPostWebtoonId
from .I_naver_game import NaverGameScraper
from .J_lezhin_comics import LezhinComicsScraper
from .K_kakaopage import KakaopageScraper
from .L_naver_blog import NaverBlogScraper, NaverBlogWebtoonId
from .M_tistory import TistoryScraper, TistoryWebtoonId
from .N_kakao_webtoon import KakaoWebtoonScraper
