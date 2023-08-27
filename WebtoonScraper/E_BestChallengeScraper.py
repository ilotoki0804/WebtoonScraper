'''Download Webtoons from Naver Webtoon Best Challenge.'''

from __future__ import annotations
if __name__ in ("__main__", "E_BestChallengeScraper"):
    from D_NaverWebtoonScraper import NaverWebtoonScraper
else:
    from .D_NaverWebtoonScraper import NaverWebtoonScraper


class BestChallengeScraper(NaverWebtoonScraper):
    def __init__(self, pbar_independent=False):
        super().__init__(pbar_independent)
        self.BASE_URL = 'https://comic.naver.com/bestChallenge'  # TODO: init 밖으로 옮기기
        self.EPISODE_IMAGES_URL_SELECTOR = '#comic_view_area > div > img'


if __name__ == '__main__':
    wt = BestChallengeScraper()
    wt.download_one_webtoon(763952)  # 과학고
