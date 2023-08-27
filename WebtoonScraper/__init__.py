if __name__ == "__main__":
    from A_FolderMerger import FolderMerger
    import B_Webtoon as Webtoon
    from D_NaverWebtoonScraper import NaverWebtoonScraper
    from E_BestChallengeScraper import BestChallengeScraper
    from F_WebtoonOriginalsScraper import WebtoonOriginalsScraper
    from G_WebtoonCanvasScraper import WebtoonCanvasScraper
    from H_TelescopeScraper import TelescopeScraper
    from I_BufftoonScraper import BufftoonScraper
    from J_NaverPostScraper import NaverPostScraper
    from K_NaverGameScraper import NaverGameScraper
    from M_KakaopageWebtoonScraper import KakaopageWebtoonScraper
else:
    from .A_FolderMerger import FolderMerger
    from . import B_Webtoon as Webtoon
    from .D_NaverWebtoonScraper import NaverWebtoonScraper
    from .E_BestChallengeScraper import BestChallengeScraper
    from .F_WebtoonOriginalsScraper import WebtoonOriginalsScraper
    from .G_WebtoonCanvasScraper import WebtoonCanvasScraper
    from .H_TelescopeScraper import TelescopeScraper
    from .I_BufftoonScraper import BufftoonScraper
    from .J_NaverPostScraper import NaverPostScraper
    from .K_NaverGameScraper import NaverGameScraper
    from .M_KakaopageWebtoonScraper import KakaopageWebtoonScraper

__version__ = (1, 3, 0)

if __name__ == '__main__':
    print('Testing codes.')
