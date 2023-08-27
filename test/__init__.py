# sourcery skip: merge-repeated-ifs
if __name__ in {"__main__", "__init__"}:
    import test
else:
    from . import test

if __name__ == "__main__":
    test.main()
