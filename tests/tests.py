# from WebtoonScraper.WebtoonScraper import *
# from WebtoonScraper import *

webtoon = NaverWebtoonScraper()
webtoon.get_webtoons(766648)

webtoons = WebtoonsScraper()
webtoons.get_webtoons(5291, 1435)