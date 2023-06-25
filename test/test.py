from WebtoonScraper import Webtoon as wt

if __name__ == "__main__":
    # wt.get_webtoon(146, wt.M)
    wt.get_webtoon(263735)
    # wt.get_webtoon(597061, wt.NAVER_POST) # 19803452
    wt.get_webtoon(597061, wt.NAVER_POST, member_no=19803452) # 19803452
    wt.get_webtoon(1007888, wt.BU, cookie='')
    wt.get_webtoon(146, wt.T)