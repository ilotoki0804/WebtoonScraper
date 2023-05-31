# 웹툰을 쉽게 받도록
from WebtoonScraper import NaverWebtoonScraper
from WebtoonScraper import WebtoonsScraper
from WebtoonScraper import BestChallengeScraper
from WebtoonScraper import CanvasScraper

# class Webtoon:
#     NAVER = 'naver'
#     BEST_CHALLENGE = 'best_challenge'
#     WEBTOONS = 'webtoons'
#     CANVAS = 'canvas'

#     def __init__(self):
#         pass
    
#     def get_webtoon_type(self, webtoon_type):
#         if webtoon_type.lower() == 'naver':
#             webtoonscraper = NaverWebtoonScraper()
#         elif webtoon_type.lower() == 'best_challenge':
#             webtoonscraper = BestChallengeScraper()
#         elif webtoon_type.lower() == 'webtoons':
#             webtoonscraper = WebtoonsScraper()
#         elif webtoon_type.lower() == 'canvas':
#             webtoonscraper = CanvasScraper()
#         else:
#             raise ValueError('webtoon_type should be among naver, best_challenge, webtoons, and canvas.')
#         return webtoonscraper
    
#     def get_webtoon(self, webtoon_id:int, webtoon_type:str):
#         webtoonscraper = self.get_webtoon_type(webtoon_type)
#         webtoonscraper.download_one_webtoon(None, webtoon_id, 50)

#     async def get_webtoon_async(self, webtoon_id:int, webtoon_type:str):
#         webtoonscraper = self.get_webtoon_type(webtoon_type)
#         await webtoonscraper.download_one_webtoon_async(titleid=webtoon_id)
import asyncio
from WebtoonScraper.getsoup import *

class Webtoon:
    NAVER = 'naver'
    BEST_CHALLENGE = 'best_challenge'
    WEBTOONS = 'webtoons'
    CANVAS = 'canvas'

    def __init__(self):
        pass

    async def auto_webtoon_type(self, webtoon_id):
        '''If webtoon is best challenge, this returns True. Otherwise, False.'''
        title = get_soup_from_requests(f'https://comic.naver.com/webtoon/detail?titleId={webtoon_id}', 'meta[property="og:title"]')
        title = title[0].get('content')
    
        if title:
            return 'naver'
        
        title = get_soup_from_requests(f'https://comic.naver.com/bestChallenge/list?titleId={webtoon_id}', 'meta[property="og:title"]')
        title = title[0].get('content')
    
        if title:
            return 'best_challenge'
        
        webtoonscraper = WebtoonsScraper()
        title_function = lambda: get_soup_from_requests(f'https://www.webtoons.com/en/fantasy/watermelon/list?title_no={webtoon_id}',
                                            'meta[property="og:title"]',
                                            user_agent=webtoonscraper.user_agent)
        title_original = await webtoonscraper._run_unreliable_function(title_function)
        try:
            title_original[0]['content']
            return 'webtoons'
        except IndexError:
            return 'canvas'
    
    def get_webtoon_type(self, webtoon_type):
        if webtoon_type.lower() == 'naver':
            webtoonscraper = NaverWebtoonScraper()
        elif webtoon_type.lower() == 'best_challenge':
            webtoonscraper = BestChallengeScraper()
        elif webtoon_type.lower() == 'webtoons':
            webtoonscraper = WebtoonsScraper()
        elif webtoon_type.lower() == 'canvas':
            webtoonscraper = CanvasScraper()
        else:
            raise ValueError('webtoon_type should be among naver, best_challenge, webtoons, and canvas.')
        return webtoonscraper
    
    def get_webtoon(self, webtoon_id:int, webtoon_type:str=None):
        if webtoon_type is None:
            loop = asyncio.get_event_loop()
            webtoon_type = loop.run_until_complete(self.auto_webtoon_type(webtoon_id))
            # loop.stop()
        webtoonscraper = self.get_webtoon_type(webtoon_type)
        webtoonscraper.download_one_webtoon(None, webtoon_id, 50)

    async def get_webtoon_async(self, webtoon_id:int, webtoon_type:str=None):
        if webtoon_type is None:
            webtoon_type = await self.auto_webtoon_type(webtoon_id)
        webtoonscraper = self.get_webtoon_type(webtoon_type)
        await webtoonscraper.download_one_webtoon_async(titleid=webtoon_id)