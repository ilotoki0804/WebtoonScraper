import asyncio

import pytest

from WebtoonScraper.scrapers import *  # type: ignore


def test_callback():
    asyncio.run(async_test_callback())


async def async_test_callback():
    scraper = NaverWebtoonScraper.from_url("https://comic.naver.com/webtoon/list?titleId=805702")

    @scraper.callbacks.register_async("async_trigger")
    async def async_callback(scraper, **context):
        assert context["key"] == "value"

    @scraper.callbacks.register_async("async_task_trigger", blocking=False)
    async def async_callback_task(scraper, **context):
        assert context["key"] == "value"
        return "return_value"

    @scraper.callbacks.register("trigger")
    def callback(scraper, **context):
        assert context["key"] == "value"

    await scraper.callbacks.async_callback("async_trigger", key="value")
    await scraper.callbacks.async_callback("trigger", key="value")
    scraper.callbacks.callback("trigger", key="value")
    (task,) = await scraper.callbacks.async_callback("async_task_trigger", key="value")  # type: ignore
    assert await task == "return_value"

    with pytest.raises(AssertionError):
        await scraper.callbacks.async_callback("async_trigger", key="not_a_value")
    with pytest.raises(AssertionError):
        await scraper.callbacks.async_callback("trigger", key="not_a_value")
    scraper.callbacks.callback("async_trigger", key="not_a_value")
    with pytest.raises(AssertionError):
        scraper.callbacks.callback("trigger", key="not_a_value")
    with pytest.raises(AssertionError):
        (task,) = await scraper.callbacks.async_callback("async_task_trigger", key="not_a_value")  # type: ignore
        await task
