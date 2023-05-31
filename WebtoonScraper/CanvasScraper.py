# canvas2
from WebtoonScraper import WebtoonsScraper
class CanvasScraper(WebtoonsScraper):
    '''Scraping webtoons from webtoons.com'''
    def __init__(self):
        super().__init__()
        self.BASE_URL = 'https://www.webtoons.com/en/challenge/meme-girls'
