if __name__ == "__main__":
    from A_FolderManager import FolderManager
    import B_Webtoon as Webtoon
    from D_NaverWebtoonScraper import NaverWebtoonScraper
    from E_BestChallengeScraper import BestChallengeScraper
    from F_WebtoonOriginalsScraper import WebtoonOriginalsScraper
    from G_WebtoonCanvasScraper import WebtoonCanvasScraper
    from H_TelescopeScraper import TelescopeScraper
    from I_BufftoonScraper import BufftoonScraper
    from J_NaverPostScraper import NaverPostScraper
    from K_NaverGameScraper import NaverGameScraper
else:
    from .A_FolderManager import FolderManager
    from . import B_Webtoon as Webtoon
    from .D_NaverWebtoonScraper import NaverWebtoonScraper
    from .E_BestChallengeScraper import BestChallengeScraper
    from .F_WebtoonOriginalsScraper import WebtoonOriginalsScraper
    from .G_WebtoonCanvasScraper import WebtoonCanvasScraper
    from .H_TelescopeScraper import TelescopeScraper
    from .I_BufftoonScraper import BufftoonScraper
    from .J_NaverPostScraper import NaverPostScraper
    from .K_NaverGameScraper import NaverGameScraper

if __name__ == '__main__':
    print('Testing codes.')
