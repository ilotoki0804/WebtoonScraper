'''Download Webtoons from Webtoon Canvas.
'''
from WebtoonScraper.WebtoonOriginalsScraper import WebtoonOriginalsScraper
class WebtoonCanvasScraper(WebtoonOriginalsScraper):
    '''Scrape webtoons from Webtoon Originals.'''
    def __init__(self, pbar_independent=False, short_connection=False):
        super().__init__(pbar_independent, short_connection)
        self.BASE_URL = 'https://www.webtoons.com/en/challenge/meme-girls'

if __name__ == '__main__':
    wt = WebtoonCanvasScraper()