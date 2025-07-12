import asyncio

import pytest

from WebtoonScraper.scrapers import *  # type: ignore


def test_from_string():
    # NaverWebtoonScraper and other scrapers that have integer for webtoon ID

    scraper = NaverWebtoonScraper._from_string("432096")
    assert scraper.webtoon_id == 432096

    with pytest.raises(ValueError):
        NaverWebtoonScraper._from_string("unknown")

    # LezhinComicsScraper

    scraper = LezhinComicsScraper._from_string("webtoon_id")
    assert scraper.webtoon_id == "webtoon_id"


def test_from_url():
    scraper = NaverWebtoonScraper.from_url("https://comic.naver.com/webtoon/list?titleId=805702")
    assert scraper.webtoon_id == 805702 and type(scraper) is NaverWebtoonScraper
    scraper = NaverWebtoonScraper.from_url("https://comic.naver.com/webtoon/list?titleId=812354&tab=thu")
    assert scraper.webtoon_id == 812354 and type(scraper) is NaverWebtoonScraper
    scraper = NaverWebtoonScraper.from_url("https://comic.naver.com/bestChallenge/list?titleId=816046")
    assert scraper.webtoon_id == 816046 and type(scraper) is NaverWebtoonScraper
    scraper = NaverWebtoonScraper.from_url("https://comic.naver.com/challenge/list?titleId=745689")
    assert scraper.webtoon_id == 745689 and type(scraper) is NaverWebtoonScraper
    assert NaverWebtoonScraper.from_url("https://comic.naver.com/webtoon/list?titleId=812354&tab=thu").webtoon_id == 812354
    assert NaverWebtoonScraper.from_url("https://comic.naver.com/bestChallenge/list?titleId=816046").webtoon_id == 816046
    assert NaverWebtoonScraper.from_url("https://comic.naver.com/challenge/list?titleId=745689").webtoon_id == 745689

    assert LezhinComicsScraper.from_url("https://www.lezhin.com/ko/comic/dr_hearthstone").webtoon_id == "dr_hearthstone"


def test_callback():
    asyncio.run(async_test_callback())


async def async_test_callback():
    scraper = NaverWebtoonScraper.from_url("https://comic.naver.com/webtoon/list?titleId=805702")

    @scraper.callback_manager.register_async_callback("async_trigger")
    async def async_callback(scraper, **context):
        assert context["key"] == "value"

    @scraper.callback_manager.register_async_callback("async_task_trigger", blocking=False)
    async def async_callback_task(scraper, **context):
        assert context["key"] == "value"
        return "return_value"

    @scraper.callback_manager.register_callback("trigger")
    def callback(scraper, **context):
        assert context["key"] == "value"

    await scraper.callback_manager.async_callback("async_trigger", key="value")
    await scraper.callback_manager.async_callback("trigger", key="value")
    scraper.callback_manager.callback("trigger", key="value")
    (task,) = await scraper.callback_manager.async_callback("async_task_trigger", key="value")  # type: ignore
    assert await task == "return_value"

    with pytest.raises(AssertionError):
        await scraper.callback_manager.async_callback("async_trigger", key="not_a_value")
    with pytest.raises(AssertionError):
        await scraper.callback_manager.async_callback("trigger", key="not_a_value")
    scraper.callback_manager.callback("async_trigger", key="not_a_value")
    with pytest.raises(AssertionError):
        scraper.callback_manager.callback("trigger", key="not_a_value")
    with pytest.raises(AssertionError):
        (task,) = await scraper.callback_manager.async_callback("async_task_trigger", key="not_a_value")  # type: ignore
        await task
