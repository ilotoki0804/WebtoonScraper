'''Download Webtoons from Webtoon Canvas.'''

from __future__ import annotations

if __name__ in ("__main__", 'E_webtoon_canvas'):
    from D_webtoon_originals import WebtoonOriginalsScraper
else:
    from .D_webtoon_originals import WebtoonOriginalsScraper


class WebtoonCanvasScraper(WebtoonOriginalsScraper):
    '''Scrape webtoons from Webtoon Originals.'''
    BASE_URL = 'https://www.webtoons.com/en/challenge/meme-girls'
    TEST_WEBTOON_ID = 263735  # Spookman
