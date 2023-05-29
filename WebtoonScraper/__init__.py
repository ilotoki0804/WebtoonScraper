import WebtoonScraper.getsoup as getsoup
from WebtoonScraper.scraper import NaverWebtoonScraper, WebtoonsScraper
from WebtoonScraper.foldermanagement import WebtoonFolderManagement

if __name__ == '__main__':
    print('Testing codes.')
    webtoon = NaverWebtoonScraper()
    webtoon.get_webtoons(766648)

    webtoons = WebtoonsScraper()
    webtoons.get_webtoons(5291, 1435)