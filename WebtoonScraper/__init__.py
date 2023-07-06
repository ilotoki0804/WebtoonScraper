if __name__ == "__main__":
    from NaverWebtoonScraper import NaverWebtoonScraper
    from FolderManager import FolderManager
    from WebtoonOriginalsScraper import WebtoonOriginalsScraper
    from BestChallengeScraper import BestChallengeScraper
    from WebtoonCanvasScraper import WebtoonCanvasScraper
    import Webtoon
    from TelescopeScraper import TelescopeScraper
    from BufftoonScraper import BufftoonScraper
    from NaverPostScraper import NaverPostScraper
    from NaverGameScraper import NaverGameScraper
else:
    from .NaverWebtoonScraper import NaverWebtoonScraper
    from .FolderManager import FolderManager
    from .WebtoonOriginalsScraper import WebtoonOriginalsScraper
    from .BestChallengeScraper import BestChallengeScraper
    from .WebtoonCanvasScraper import WebtoonCanvasScraper
    from . import Webtoon
    from .TelescopeScraper import TelescopeScraper
    from .BufftoonScraper import BufftoonScraper
    from .NaverPostScraper import NaverPostScraper
    from .NaverGameScraper import NaverGameScraper

if __name__ == '__main__':
    print('Testing codes.')
