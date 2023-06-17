"""Download webtoons automatiallly or easily"""
import asyncio

from WebtoonScraper.NaverWebtoonScraper import NaverWebtoonScraper
from WebtoonScraper.foldermanagement import WebtoonFolderManagement
from WebtoonScraper.WebtoonOriginalsScraper import WebtoonOriginalsScraper
from WebtoonScraper.BestChallengeScraper import BestChallengeScraper
from WebtoonScraper.WebtoonCanvasScraper import WebtoonCanvasScraper
from WebtoonScraper.TelescopeScraper import TelescopeScraper

N = 'naver_webtoon'
NAVER_WEBTOON = 'naver_webtoon'
B = 'best_challenge'
BEST_CHALLENGE = 'best_challenge'
O = 'originals'
ORIGINALS = 'originals'
C = 'canvas'
CANVAS = 'canvas'
T = 'telescope'
M = 'telescope'
TELESCOPE = 'telescope'

async def get_webtoon_async(webtoon_id:int, webtoon_type:str=None, merge:None|int=None) -> None:
    async def auto_webtoon_type(webtoon_id: int) -> str:
        """If webtoon is best challenge, this returns True. Otherwise, False."""
        webtoonscraper = NaverWebtoonScraper()

        title = await webtoonscraper.get_internet('soup_select_one', f'https://comic.naver.com/webtoon/detail?titleId={webtoon_id}', 'meta[property="og:title"]')
        title = title.get('content')
        print(title)
        if title:
            return NAVER_WEBTOON
        
        title = await webtoonscraper.get_internet('soup_select_one', f'https://comic.naver.com/bestChallenge/list?titleId={webtoon_id}', 'meta[property="og:title"]')
        title = title.get('content')
        if title:
            return BEST_CHALLENGE
        
        webtoonscraper.IS_STABLE_CONNECTION = False
        
        title = await webtoonscraper.get_internet('soup_select_one', f'https://www.webtoons.com/en/fantasy/watermelon/list?title_no={webtoon_id}', 'meta[property="og:title"]')
        if title is not None:
            print(title)
            return ORIGINALS

        title = await webtoonscraper.get_internet('soup_select_one', f'https://www.webtoons.com/en/challenge/meme-girls/list?title_no={webtoon_id}', 'meta[property="og:title"]')
        if title is not None:
            return CANVAS
        
        return TELESCOPE

    async def get_webtoon_type(webtoon_type: int):
        if webtoon_type.lower() == NAVER_WEBTOON:
            webtoonscraper = NaverWebtoonScraper()
        elif webtoon_type.lower() == BEST_CHALLENGE:
            webtoonscraper = BestChallengeScraper()
        elif webtoon_type.lower() == ORIGINALS:
            webtoonscraper = WebtoonOriginalsScraper()
        elif webtoon_type.lower() == CANVAS:
            webtoonscraper = WebtoonCanvasScraper()
        elif webtoon_type.lower() == TELESCOPE:
            webtoonscraper = TelescopeScraper()
        else:
            raise ValueError('webtoon_type should be among naver_webtoon, best_challenge, originals, canvas, and telescope.')
        return webtoonscraper

    ##### MAIN #####

    if webtoon_type is None:
        webtoon_type = await auto_webtoon_type(webtoon_id)
    webtoonscraper = await get_webtoon_type(webtoon_type)
    await webtoonscraper.download_one_webtoon_async(titleid=webtoon_id)
    if merge:
        fd = WebtoonFolderManagement('webtoon_merge')
        fd.divide_all_webtoons(merge)

def get_webtoon(webtoon_id:int, webtoon_type:str=None, merge:None|int=None) -> None:
    asyncio.run(get_webtoon_async(webtoon_id, webtoon_type, merge))

if __name__ == '__main__':
    # get_webtoon(263735)
    get_webtoon(263735, merge=True)