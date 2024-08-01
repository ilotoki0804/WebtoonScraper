import pytest
from WebtoonScraper.scrapers import *

def test_from_string():
    # NaverWebtoonScraper and other scrapers that have integer for webtoon ID

    scraper = NaverWebtoonScraper._from_string("432096")
    assert scraper.webtoon_id == 432096

    with pytest.raises(Exception):
        NaverWebtoonScraper._from_string("unknown")

    # NaverPostScraper

    scraper = NaverPostScraper._from_string("235,235")
    assert scraper.webtoon_id == (235, 235)

    scraper = NaverPostScraper._from_string("235, 235")
    assert scraper.webtoon_id == (235, 235)

    with pytest.raises(Exception):
        NaverPostScraper._from_string("unknown")

    with pytest.raises(Exception):
        NaverPostScraper._from_string("unknown,43")

    with pytest.raises(Exception):
        NaverPostScraper._from_string("43,unknown")

    with pytest.raises(Exception):
        NaverPostScraper._from_string("43,")

    with pytest.raises(Exception):
        NaverPostScraper._from_string(",43")

    # LezhinComicsScraper

    scraper = LezhinComicsScraper._from_string("webtoon_id")
    assert scraper.webtoon_id == "webtoon_id"

    # NaverBlogScraper

    scraper = NaverBlogScraper._from_string("blog_id,1234")
    assert scraper.webtoon_id == ("blog_id", 1234)

    with pytest.raises(Exception):
        NaverBlogScraper._from_string("unknown")

    with pytest.raises(Exception):
        NaverBlogScraper._from_string("blog_id,unknown")

    with pytest.raises(Exception):
        NaverBlogScraper._from_string("blog_id,")

    with pytest.raises(Exception):
        NaverBlogScraper._from_string(",1234")

    # TistoryScraper

    scraper = TistoryScraper._from_string("blog_id,category")
    assert scraper.webtoon_id == ("blog_id", "category")

    with pytest.raises(Exception):
        TistoryScraper._from_string("unknown")

    with pytest.raises(Exception):
        TistoryScraper._from_string("blog_id,")

    with pytest.raises(Exception):
        TistoryScraper._from_string(",category")
