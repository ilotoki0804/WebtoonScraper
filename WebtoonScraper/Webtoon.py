'''Download webtoons automatiallly or easily'''
from WebtoonScraper import NaverWebtoonScraper
from WebtoonScraper import WebtoonOriginalsScraper
from WebtoonScraper import BestChallengeScraper
from WebtoonScraper import WebtoonCanvasScraper
from WebtoonScraper import TelescopeScraper

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
        title = get_soup_from_requests(f'https://comic.naver.com/webtoon/detail?titleId={webtoon_id}', 'meta[property="og:title"]')
        title = title[0].get('content')
    
        if title:
            return self.NAVER_WEBTOON
        
        title = get_soup_from_requests(f'https://comic.naver.com/bestChallenge/list?titleId={webtoon_id}', 'meta[property="og:title"]')
        title = title[0].get('content')
    
        if title:
            return self.BEST_CHALLENGE
        
        webtoonscraper = WebtoonOriginalsScraper()
        title = webtoonscraper.get_internet('soup_select_one', f'https://www.webtoons.com/en/fantasy/watermelon/list?title_no={webtoon_id}', 'meta[property="og:title"]')
        if title is not None:
            return self.ORIGINALS


        title = webtoonscraper.get_internet('soup_select_one', f'https://www.webtoons.com/en/challenge/meme-girls/list?title_no={webtoon_id}', 'meta[property="og:title"]')
        if title is not None:
            return self.CANVAS
        
        return self.TELESCOPE
    
    def get_webtoon_type(self, webtoon_type):
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
    
    def get_webtoon(self, webtoon_id:int, webtoon_type:str=None):
        loop = asyncio.get_event_loop()
        if webtoon_type is None:
            webtoon_type = loop.run_until_complete(self.auto_webtoon_type(webtoon_id))
            # loop.stop()
        webtoonscraper = self.get_webtoon_type(webtoon_type)
        # webtoonscraper.download_one_webtoon(None, webtoon_id, 50)
        loop.run_until_complete(webtoonscraper.download_one_webtoon_async(titleid=webtoon_id))

    async def get_webtoon_async(self, webtoon_id:int, webtoon_type:str=None):
        if webtoon_type is None:
            webtoon_type = await self.auto_webtoon_type(webtoon_id)
        webtoonscraper = self.get_webtoon_type(webtoon_type)
        await webtoonscraper.download_one_webtoon_async(titleid=webtoon_id)

if __name__ == '__main__':
    wt = Webtoon()
    # wt.get_webtoon(263735)