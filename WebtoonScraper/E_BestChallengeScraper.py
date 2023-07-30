'''Download Webtoons from Naver Webtoon Best Challenge.'''

if __name__ in ("__main__", "E_BestChallengeScraper"):
    from D_NaverWebtoonScraper import NaverWebtoonScraper
else:
    from .D_NaverWebtoonScraper import NaverWebtoonScraper


class BestChallengeScraper(NaverWebtoonScraper):
    def __init__(self, pbar_independent=False):
        super().__init__(pbar_independent)
        self.BASE_URL = 'https://comic.naver.com/bestChallenge'
        self.EPISODE_IMAGES_URL_SELECTOR = '#comic_view_area > div > img'


if __name__ == '__main__':
    wt = BestChallengeScraper()
    wt.download_one_webtoon(763952)  # 과학고
