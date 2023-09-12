import logging

from WebtoonScraper import webtoon as wt, DirectoryMerger

logging.warning(f'파일이 아닌 WebtoonScraper 모듈에서 실행되고 있습니다. {__name__ = }')


def skip_by_KeyboadInterrupt(func):
    try:
        func()
    except KeyboardInterrupt:
        print('Interrupted.')
        print('=============')


def test_download_ability():
    skip_by_KeyboadInterrupt(lambda: wt.download_webtoon(809590, wt.N))  # 네이버 웹툰
    skip_by_KeyboadInterrupt(lambda: wt.download_webtoon(767676, wt.B))  # 베스트 도전만화
    skip_by_KeyboadInterrupt(lambda: wt.download_webtoon(1435, wt.O))  # 웹툰 오리지널
    skip_by_KeyboadInterrupt(lambda: wt.download_webtoon(263735, wt.C))  # 캔버스
    skip_by_KeyboadInterrupt(lambda: wt.download_webtoon(1007888, wt.BF, cookie=''))  # 버프툰
    skip_by_KeyboadInterrupt(lambda: wt.download_webtoon((597061, 19803452), wt.P))  # 네이버 포스트
    skip_by_KeyboadInterrupt(lambda: wt.download_webtoon(59, wt.G))  # 네이버 게임
    skip_by_KeyboadInterrupt(lambda: wt.download_webtoon('noway', wt.P))  # 레진
    skip_by_KeyboadInterrupt(lambda: wt.download_webtoon(53397318, wt.KP))  # 카카오페이지


def test_platform_select_ability():
    skip_by_KeyboadInterrupt(lambda: wt.get_webtoon_platform(809590))  # 네이버 웹툰
    skip_by_KeyboadInterrupt(lambda: wt.get_webtoon_platform(767676))  # 베스트 도전만화
    skip_by_KeyboadInterrupt(lambda: wt.get_webtoon_platform(1435))  # 웹툰 오리지널
    skip_by_KeyboadInterrupt(lambda: wt.get_webtoon_platform(263735))  # 캔버스
    skip_by_KeyboadInterrupt(lambda: wt.get_webtoon_platform(1007888))  # 버프툰
    skip_by_KeyboadInterrupt(lambda: wt.get_webtoon_platform((597061, 19803452)))  # 네이버 포스트
    skip_by_KeyboadInterrupt(lambda: wt.get_webtoon_platform(59))  # 네이버 게임
    skip_by_KeyboadInterrupt(lambda: wt.get_webtoon_platform('noway'))  # 레진
    skip_by_KeyboadInterrupt(lambda: wt.get_webtoon_platform(53397318))  # 카카오페이지


def test_wrong_platform_select_ability():
    skip_by_KeyboadInterrupt(lambda: wt.get_webtoon_platform(19040928340))  # 나머지
    skip_by_KeyboadInterrupt(lambda: wt.get_webtoon_platform((19040928340, 209402)))  # 네이버 포스트
    skip_by_KeyboadInterrupt(lambda: wt.get_webtoon_platform('lezhin'))  # 레진


def test_merge_ability():
    fd = DirectoryMerger()
    fd.merge_webtoons_from_source_directory(5)


def main():
    test_platform_select_ability()
    test_wrong_platform_select_ability()
    # test_download_ability()
    # test_merge_ability()


if __name__ == "__main__":
    main()
