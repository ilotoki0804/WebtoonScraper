"""Used exceptions of WebtoonScraper."""


class WebtoonScraperError(Exception):
    """Base class of every error of WebtoonScraper."""


class DirectoryStateUnmatched(WebtoonScraperError):
    """directory state recieved from check_directory_state is not wanted."""


class InvalidWebtoonId(WebtoonScraperError):
    """webtoon id is invalid. Or it can be adult webtoon, which is currently not supported."""


class UseFetchEpisode(WebtoonScraperError):
    """Only fetch_episode_informations exists."""

    def __init__(self, message: str = ''):
        super().__init__(message or 'Use `fetch_episode_informations` for get webtoon information.')
