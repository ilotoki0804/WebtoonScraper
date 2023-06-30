from WebtoonScraper import Webtoon as wt

def skip_by_KeyboadInterrupt(func):
    try:
        func()
    except KeyboardInterrupt:
        print('Interrupted.')
        print('=============')

if __name__ == "__main__":
    # skip_by_KeyboadInterrupt(lambda: wt.get_webtoon(809590, wt.N)) # 네이버 웹툰
    # skip_by_KeyboadInterrupt(lambda: wt.get_webtoon(767676, wt.B)) # 베스트 도전만화
    # skip_by_KeyboadInterrupt(lambda: wt.get_webtoon(1435, wt.O)) # 웹툰 오리지널
    # skip_by_KeyboadInterrupt(lambda: wt.get_webtoon(263735, wt.C)) # 캔버스
    # skip_by_KeyboadInterrupt(lambda: wt.get_webtoon(146, wt.M)) # 만화경
    skip_by_KeyboadInterrupt(lambda: wt.get_webtoon(1007888, wt.BF, cookie='')) # 버프툰
    skip_by_KeyboadInterrupt(lambda: wt.get_webtoon(597061, wt.P, member_no=19803452)) # 네이버 포스트
