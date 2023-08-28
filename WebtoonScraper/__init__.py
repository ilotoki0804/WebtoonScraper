"""
░██╗░░░░░░░██╗███████╗██████╗░████████╗░█████╗░░█████╗░███╗░░██╗░██████╗░█████╗░██████╗░░█████╗░██████╗░███████╗██████╗░
░██║░░██╗░░██║██╔════╝██╔══██╗╚══██╔══╝██╔══██╗██╔══██╗████╗░██║██╔════╝██╔══██╗██╔══██╗██╔══██╗██╔══██╗██╔════╝██╔══██╗
░╚██╗████╗██╔╝█████╗░░██████╦╝░░░██║░░░██║░░██║██║░░██║██╔██╗██║╚█████╗░██║░░╚═╝██████╔╝███████║██████╔╝█████╗░░██████╔╝
░░████╔═████║░██╔══╝░░██╔══██╗░░░██║░░░██║░░██║██║░░██║██║╚████║░╚═══██╗██║░░██╗██╔══██╗██╔══██║██╔═══╝░██╔══╝░░██╔══██╗
░░╚██╔╝░╚██╔╝░███████╗██████╦╝░░░██║░░░╚█████╔╝╚█████╔╝██║░╚███║██████╔╝╚█████╔╝██║░░██║██║░░██║██║░░░░░███████╗██║░░██║
░░░╚═╝░░░╚═╝░░╚══════╝╚═════╝░░░░╚═╝░░░░╚════╝░░╚════╝░╚═╝░░╚══╝╚═════╝░░╚════╝░╚═╝░░╚═╝╚═╝░░╚═╝╚═╝░░░░░╚══════╝╚═╝░░╚═╝

Scrape webtoons with ease.
"""


if __name__ == "__main__":
    from a_folder_merger import FolderMerger
    import B_Webtoon as Webtoon
    from D_NaverWebtoonScraper import NaverWebtoonScraper
    from E_BestChallengeScraper import BestChallengeScraper
    from F_WebtoonOriginalsScraper import WebtoonOriginalsScraper
    from G_WebtoonCanvasScraper import WebtoonCanvasScraper
    from H_TelescopeScraper import TelescopeScraper
    from I_BufftoonScraper import BufftoonScraper
    from J_NaverPostScraper import NaverPostScraper
    from K_NaverGameScraper import NaverGameScraper
    from L_LezhinComicsScraper import LezhinComicsScraper
    from M_KakaopageWebtoonScraper import KakaopageWebtoonScraper
else:
    from .a_folder_merger import FolderMerger
    from . import B_Webtoon as Webtoon
    from .D_NaverWebtoonScraper import NaverWebtoonScraper
    from .E_BestChallengeScraper import BestChallengeScraper
    from .F_WebtoonOriginalsScraper import WebtoonOriginalsScraper
    from .G_WebtoonCanvasScraper import WebtoonCanvasScraper
    from .H_TelescopeScraper import TelescopeScraper
    from .I_BufftoonScraper import BufftoonScraper
    from .J_NaverPostScraper import NaverPostScraper
    from .K_NaverGameScraper import NaverGameScraper
    from .L_LezhinComicsScraper import LezhinComicsScraper
    from .M_KakaopageWebtoonScraper import KakaopageWebtoonScraper

__version__ = (1, 3, 0)
