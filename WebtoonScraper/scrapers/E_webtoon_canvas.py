"""Download Webtoons from Webtoon Canvas."""

from __future__ import annotations

from .D_webtoon_originals import WebtoonOriginalsScraper


class WebtoonCanvasScraper(WebtoonOriginalsScraper):
    """Scrape webtoons from Webtoon Originals."""

    BASE_URL = "https://www.webtoons.com/en/challenge/meme-girls"
    TEST_WEBTOON_ID = 263735  # Spookman
