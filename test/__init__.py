# sourcery skip: merge-repeated-ifs
if __name__ == "__main__":
    import test
else:
    from . import test

if __name__ == "__main__":
    # test.test_download_ability()
    test.test_get_webtoon_platform()
