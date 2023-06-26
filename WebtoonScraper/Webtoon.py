"""Download webtoons automatiallly or easily"""
import asyncio

from WebtoonScraper.NaverWebtoonScraper import NaverWebtoonScraper
from WebtoonScraper.foldermanagement import WebtoonFolderManagement
from WebtoonScraper.WebtoonOriginalsScraper import WebtoonOriginalsScraper
from WebtoonScraper.BestChallengeScraper import BestChallengeScraper
from WebtoonScraper.WebtoonCanvasScraper import WebtoonCanvasScraper
from WebtoonScraper.TelescopeScraper import TelescopeScraper
from WebtoonScraper.BufftoonScraper import BufftoonScraper 
from WebtoonScraper.NaverPostScraper import NaverPostScraper 
# from WebtoonScraper.NaverGameScraper import NaverGameScraper 
from NaverGameScraper import NaverGameScraper 

N = NAVER_WEBTOON = 'naver_webtoon'
B = BEST_CHALLENGE = 'best_challenge'
O = ORIGINALS = 'originals'
C = CANVAS = 'canvas'
T = M = TELESCOPE = 'telescope'
BU = BT = BUFFTOON = 'bufftoon'
P = POST = NAVER_POST = 'naver_post'

async def auto_webtoon_type(webtoon_id: int) -> str:
    """If webtoon is best challenge, this returns True. Otherwise, False."""
    available_webtoon = []
    webtoonscraper = NaverGameScraper()

    title = await webtoonscraper.get_internet('soup_select_one', f'https://comic.naver.com/webtoon/detail?titleId={webtoon_id}', 'meta[property="og:title"]')
    try:
        title = title.get('content')
        if title:
            available_webtoon.append((NAVER_WEBTOON, title))
    except AttributeError:
        pass
    
    title = await webtoonscraper.get_internet('soup_select_one', f'https://comic.naver.com/bestChallenge/list?titleId={webtoon_id}', 'meta[property="og:title"]')
    try:
        title = title.get('content')
        if title:
            available_webtoon.append((BEST_CHALLENGE, title))
    except AttributeError:
        pass
    
    webtoonscraper.IS_STABLE_CONNECTION = False
    
    title = await webtoonscraper.get_internet('soup_select_one', f'https://www.webtoons.com/en/fantasy/watermelon/list?title_no={webtoon_id}', 'meta[property="og:title"]')
    if title:
        available_webtoon.append((BEST_CHALLENGE, title))

    title = await webtoonscraper.get_internet('soup_select_one', f'https://www.webtoons.com/en/challenge/meme-girls/list?title_no={webtoon_id}', 'meta[property="og:title"]')
    try:
        title = title.get('content')
        if title:
            available_webtoon.append((CANVAS, title))
    except AttributeError:
        pass
    
    # return TELESCOPE
    title = await webtoonscraper.get_internet('soup_select_one', f'https://www.manhwakyung.com/title/{webtoon_id}', 'meta[property="og:title"]')
    title = title["content"][:-6]
    title = None if title == "에러 페이지" else title
    if title:
        available_webtoon.append((TELESCOPE, title))


    title = await webtoonscraper.get_internet('soup_select_one', f'https://bufftoon.plaync.com/series/{webtoon_id}', 'meta[property="og:title"]')
    title = title["content"]
    title = None if title == "이야기 던전에 입장하라, 버프툰" else title
    if title:
        available_webtoon.append((BUFFTOON, title))
    print(f'{title=}')
    
    try:
        title, _ = await webtoonscraper.get_webtoon_data(webtoon_id)
        if title:
            available_webtoon.append((BUFFTOON, title))
        print(f'{title=}')
    except Exception:
        pass

    # print(available_webtoon)
    if (webtoon_length := len(available_webtoon)) == 1:
        print(f'Webtoon\'s platform is assumed to be {available_webtoon[0][0]}')
        return available_webtoon[0][0]
    elif webtoon_length == 0:
        print(f'There\'s no webtoon that webtoon ID is {webtoon_id}.')
    else:
        for i, (platform, name) in enumerate(available_webtoon, 1):
            print(f'{i}. {platform}: {name}')
        try:
            platform_no = int(input('Multiple webtoon is searched. Please type number of webtoon you want to download: '))
            try:
                selected_platform, selected_webtoon = available_webtoon[platform_no - 1]
            except IndexError:
                print('Exceeded the range of webtoons.')
            print(f'Webtoon {selected_webtoon} is selected.')
            return selected_platform
        except ValueError:
            raise ValueError('Webtoon ID should be integer.')

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
    elif webtoon_type.lower() == BUFFTOON:
        webtoonscraper = BufftoonScraper()
    elif webtoon_type.lower() == NAVER_POST:
        webtoonscraper = NaverPostScraper()
    else:
        raise ValueError('webtoon_type should be among naver_webtoon, best_challenge, originals, canvas, and telescope.')
    return webtoonscraper

async def get_webtoon_async(webtoon_id:int, webtoon_type:str=None, *, merge:None|int=None, cookie: None|str=None, member_no: None|int=None) -> None:
    if webtoon_type is None:
        webtoon_type = await auto_webtoon_type(webtoon_id)
    webtoonscraper = await get_webtoon_type(webtoon_type)
    if webtoon_type.lower() == BUFFTOON or cookie is not None:
        if cookie is None:
            webtoonscraper.COOKIE = cookie
        else:
            webtoonscraper.COOKIE = input(f'Enter cookie of {webtoon_id} (Enter nothing to preceed without cookie)')
    if webtoon_type.lower() == NAVER_POST or member_no is not None:
        if not member_no:
            member_no = int(input(f'Enter memberNo of {webtoon_id}: '))
        await webtoonscraper.download_one_webtoon_async(titleid=webtoon_id, member_no=member_no)
    else:
        await webtoonscraper.download_one_webtoon_async(titleid=webtoon_id)
    if merge:
        fd = WebtoonFolderManagement('webtoon_merge')
        fd.divide_all_webtoons(merge)

def get_webtoon(webtoon_id:int, webtoon_type:str=None, *, merge:None|int|bool=None, cookie: None|str=None, member_no: None|int=None) -> None:
    asyncio.run(get_webtoon_async(webtoon_id, webtoon_type, merge=merge, cookie=cookie, member_no=member_no))

if __name__ == '__main__':
    # get_webtoon(263735)
    # get_webtoon(263735, merge=True)
    # asyncio.run(auto_webtoon_type(31))
    asyncio.run(auto_webtoon_type(1007888))
    # asyncio.run(auto_webtoon_type(493850238058309))
    # asyncio.run(auto_webtoon_type(263735))