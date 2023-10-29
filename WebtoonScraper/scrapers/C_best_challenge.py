'''Download Webtoons from Naver Webtoon Best Challenge.'''

from __future__ import annotations

from .B_naver_webtoon import NaverWebtoonScraper


class BestChallengeScraper(NaverWebtoonScraper):
    BASE_URL = 'https://comic.naver.com/bestChallenge'
    TEST_WEBTOON_ID = 809971  # 까마귀
    IS_BEST_CHALLENGE = True
    EPISODE_IMAGES_URL_SELECTOR = '#comic_view_area > div > img'
    URL_REGEX: str = r"(?:https?:\/\/)?comic[.]naver[.]com\/bestChallenge\/list\?(?:.*&)*titleId=(?P<webtoon_id>\d+)(?:&.*)*"
