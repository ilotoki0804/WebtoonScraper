import asyncio

if __name__ == "__main__":
    # 파일을 이용하는 것은 아님. 만약 제대로 사용하려면 상대 경로로 실행해야 함.
    from WebtoonScraper import Webtoon as wt
else:
    from ..WebtoonScraper import Webtoon as wt


def skip_by_KeyboadInterrupt(func):
    try:
        func()
    except KeyboardInterrupt:
        print('Interrupted.')
        print('=============')


def test_download_ability():
    skip_by_KeyboadInterrupt(lambda: wt.get_webtoon(809590, wt.N))  # 네이버 웹툰
    skip_by_KeyboadInterrupt(lambda: wt.get_webtoon(767676, wt.B))  # 베스트 도전만화
    skip_by_KeyboadInterrupt(lambda: wt.get_webtoon(1435, wt.O))  # 웹툰 오리지널
    skip_by_KeyboadInterrupt(lambda: wt.get_webtoon(263735, wt.C))  # 캔버스
    skip_by_KeyboadInterrupt(lambda: wt.get_webtoon(146, wt.M))  # 만화경
    skip_by_KeyboadInterrupt(lambda: wt.get_webtoon(1007888, wt.BF, cookie=''))  # 버프툰
    skip_by_KeyboadInterrupt(lambda: wt.get_webtoon(597061, wt.P, member_no=19803452))  # 네이버 포스트


def test_get_webtoon_platform():
    asyncio.run(wt.get_webtoon_platform(18))


if __name__ == "__main__":
    # test_download_ability()
    test_get_webtoon_platform()
