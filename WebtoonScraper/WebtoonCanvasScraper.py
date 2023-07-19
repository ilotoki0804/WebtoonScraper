'''Download Webtoons from Webtoon Canvas.
'''

if __name__ in ("__main__", 'WebtoonCanvasScraper'):
    from WebtoonOriginalsScraper import WebtoonOriginalsScraper
else:
    from .WebtoonOriginalsScraper import WebtoonOriginalsScraper


class WebtoonCanvasScraper(WebtoonOriginalsScraper):
    '''Scrape webtoons from Webtoon Originals.'''
    def __init__(self, pbar_independent=False, short_connection=False):
        super().__init__(pbar_independent, short_connection)
        self.BASE_URL = 'https://www.webtoons.com/en/challenge/meme-girls'


if __name__ == '__main__':
    wt = WebtoonCanvasScraper()
    wt.download_one_webtoon(263735)  # Spookman
