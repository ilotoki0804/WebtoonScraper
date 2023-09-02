"""
░██╗░░░░░░░██╗███████╗██████╗░████████╗░█████╗░░█████╗░███╗░░██╗░██████╗░█████╗░██████╗░░█████╗░██████╗░███████╗██████╗░
░██║░░██╗░░██║██╔════╝██╔══██╗╚══██╔══╝██╔══██╗██╔══██╗████╗░██║██╔════╝██╔══██╗██╔══██╗██╔══██╗██╔══██╗██╔════╝██╔══██╗
░╚██╗████╗██╔╝█████╗░░██████╦╝░░░██║░░░██║░░██║██║░░██║██╔██╗██║╚█████╗░██║░░╚═╝██████╔╝███████║██████╔╝█████╗░░██████╔╝
░░████╔═████║░██╔══╝░░██╔══██╗░░░██║░░░██║░░██║██║░░██║██║╚████║░╚═══██╗██║░░██╗██╔══██╗██╔══██║██╔═══╝░██╔══╝░░██╔══██╗
░░╚██╔╝░╚██╔╝░███████╗██████╦╝░░░██║░░░╚█████╔╝╚█████╔╝██║░╚███║██████╔╝╚█████╔╝██║░░██║██║░░██║██║░░░░░███████╗██║░░██║
░░░╚═╝░░░╚═╝░░╚══════╝╚═════╝░░░░╚═╝░░░░╚════╝░░╚════╝░╚═╝░░╚══╝╚═════╝░░╚════╝░╚═╝░░╚═╝╚═╝░░╚═╝╚═╝░░░░░╚══════╝╚═╝░░╚═╝

Scrape webtoons with ease.
"""


if __name__ in {"__main__", "__init__"}:
    from directory_merger import FolderMerger
    # import webtoon
    from scrapers.B_naver_webtoon import NaverWebtoonScraper
    from scrapers.C_best_challenge import BestChallengeScraper
    from scrapers.D_webtoon_originals import WebtoonOriginalsScraper
    from scrapers.E_webtoon_canvas import WebtoonCanvasScraper
    from scrapers.F_telescope import TelescopeScraper
    from scrapers.G_bufftoon import BufftoonScraper
    from scrapers.H_naver_post import NaverPostScraper
    from scrapers.I_naver_game import NaverGameScraper
    from scrapers.J_lezhin_comics import LezhinComicsScraper
    from scrapers.K_kakaopage import KakaopageScraper
else:
    from .directory_merger import FolderMerger
    # from . import webtoon
    from .scrapers.B_naver_webtoon import NaverWebtoonScraper
    from .scrapers.C_best_challenge import BestChallengeScraper
    from .scrapers.D_webtoon_originals import WebtoonOriginalsScraper
    from .scrapers.E_webtoon_canvas import WebtoonCanvasScraper
    from .scrapers.F_telescope import TelescopeScraper
    from .scrapers.G_bufftoon import BufftoonScraper
    from .scrapers.H_naver_post import NaverPostScraper
    from .scrapers.I_naver_game import NaverGameScraper
    from .scrapers.J_lezhin_comics import LezhinComicsScraper
    from .scrapers.K_kakaopage import KakaopageScraper

__version__ = (1, 4, 0)
