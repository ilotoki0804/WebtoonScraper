"""Used exceptions of WebtoonScraper."""


class DirectoryStateUnmatched(ValueError):
    """directory state recieved from check_directory_state is not wanted."""


class InvalidWebtoonId(ValueError):
    """webtoon id is invalid. Or it can be adult webtoon, which is currently not supported."""
