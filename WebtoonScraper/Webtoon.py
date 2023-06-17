'''Download webtoons automatiallly or easily'''
from WebtoonScraper.NaverWebtoonScraper import NaverWebtoonScraper
from WebtoonScraper.foldermanagement import WebtoonFolderManagement
from WebtoonScraper.WebtoonOriginalsScraper import WebtoonOriginalsScraper
from WebtoonScraper.BestChallengeScraper import BestChallengeScraper
from WebtoonScraper.WebtoonCanvasScraper import WebtoonCanvasScraper
from WebtoonScraper.TelescopeScraper import TelescopeScraper

import asyncio
from WebtoonScraper.getsoup import *

class Webtoon:
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

    def __init__(self):
        pass

    async def auto_webtoon_type(self, webtoon_id):
        '''If webtoon is best challenge, this returns True. Otherwise, False.'''
        webtoonscraper = NaverWebtoonScraper()
        title = await webtoonscraper.get_internet('soup_select_one', f'https://comic.naver.com/webtoon/detail?titleId={webtoon_id}', 'meta[property="og:title"]')
        title = title.get('content')
        print(title)
        if title:
            return self.NAVER_WEBTOON
        
        title = await webtoonscraper.get_internet('soup_select_one', f'https://comic.naver.com/bestChallenge/list?titleId={webtoon_id}', 'meta[property="og:title"]')
        title = title.get('content')
        if title:
            return self.BEST_CHALLENGE
        
        title = await webtoonscraper.get_internet('soup_select_one', f'https://www.webtoons.com/en/fantasy/watermelon/list?title_no={webtoon_id}', 'meta[property="og:title"]')
        if title is not None:
            print(title)
            return self.ORIGINALS

        title = await webtoonscraper.get_internet('soup_select_one', f'https://www.webtoons.com/en/challenge/meme-girls/list?title_no={webtoon_id}', 'meta[property="og:title"]')
        if title is not None:
            return self.CANVAS
        
        return self.TELESCOPE
    
    async def get_webtoon_type(self, webtoon_type):
        if webtoon_type.lower() == self.NAVER_WEBTOON:
            webtoonscraper = NaverWebtoonScraper()
        elif webtoon_type.lower() == self.BEST_CHALLENGE:
            webtoonscraper = BestChallengeScraper()
        elif webtoon_type.lower() == self.ORIGINALS:
            webtoonscraper = WebtoonOriginalsScraper()
        elif webtoon_type.lower() == self.CANVAS:
            webtoonscraper = WebtoonCanvasScraper()
        elif webtoon_type.lower() == self.TELESCOPE:
            webtoonscraper = TelescopeScraper()
        else:
            raise ValueError('webtoon_type should be among naver_webtoon, best_challenge, originals, canvas, and telescope.')
        return webtoonscraper
    
    async def get_webtoon_async(self, webtoon_id:int, webtoon_type:str=None):
        if webtoon_type is None:
            webtoon_type = await self.auto_webtoon_type(webtoon_id)
        webtoonscraper = await self.get_webtoon_type(webtoon_type)
        await webtoonscraper.download_one_webtoon_async(titleid=webtoon_id)

    def get_webtoon(self, webtoon_id:int, webtoon_type:str=None):
        wt = Webtoon()
        asyncio.run(wt.get_webtoon_async(webtoon_id, webtoon_type))

if __name__ == '__main__':
    wt = Webtoon()
    wt.get_webtoon(263735)