import pytest
from WebtoonScraper.scrapers import *


def test_from_string():
    # NaverWebtoonSpecificScraper and other scrapers that have integer for webtoon ID

    scraper = NaverWebtoonSpecificScraper._from_string("432096")
    assert scraper.webtoon_id == 432096

    with pytest.raises(ValueError):
        NaverWebtoonSpecificScraper._from_string("unknown")

    # LezhinComicsScraper

    scraper = LezhinComicsScraper._from_string("webtoon_id")
    assert scraper.webtoon_id == "webtoon_id"


def test_from_url():
    scraper = NaverWebtoonScraper.from_url(
        "https://comic.naver.com/webtoon/list?titleId=812354&tab=thu"
    )
    assert scraper.webtoon_id == 812354 and type(scraper) is NaverWebtoonSpecificScraper
    scraper = NaverWebtoonScraper.from_url(
        "https://comic.naver.com/bestChallenge/list?titleId=816046"
    )
    assert scraper.webtoon_id == 816046 and type(scraper) is BestChallengeSpecificScraper
    scraper = NaverWebtoonScraper.from_url(
        "https://comic.naver.com/challenge/list?titleId=745689"
    )
    assert scraper.webtoon_id == 745689 and type(scraper) is ChallengeSpecificScraper
    assert NaverWebtoonSpecificScraper.from_url(
        "https://comic.naver.com/webtoon/list?titleId=812354&tab=thu"
    ).webtoon_id == 812354
    assert BestChallengeSpecificScraper.from_url(
        "https://comic.naver.com/bestChallenge/list?titleId=816046"
    ).webtoon_id == 816046
    assert ChallengeSpecificScraper.from_url(
        "https://comic.naver.com/challenge/list?titleId=745689"
    ).webtoon_id == 745689

    assert LezhinComicsScraper.from_url(
        "https://www.lezhin.com/ko/comic/dr_hearthstone"
    ).webtoon_id == "dr_hearthstone"
