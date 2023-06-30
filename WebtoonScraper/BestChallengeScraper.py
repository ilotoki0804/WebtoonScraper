'''Download Webtoons from Naver Webtoon Best Challenge.'''
from WebtoonScraper.NaverWebtoonScraper import NaverWebtoonScraper


class BestChallengeScraper(NaverWebtoonScraper):
    def __init__(self, pbar_independent=False, short_connection=False):
        super().__init__(pbar_independent, short_connection)
        self.BASE_URL = 'https://comic.naver.com/bestChallenge'
        self.EPISODE_IMAGES_URL_SELECTOR = '#comic_view_area > div > img'


if __name__ == '__main__':
    wt = BestChallengeScraper()
