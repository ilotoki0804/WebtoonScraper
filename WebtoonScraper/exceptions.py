"""Used exceptions of WebtoonScraper."""


class WebtoonScraperError(Exception):
    """Base class of every error of WebtoonScraper."""


class DirectoryStateUnmatched(WebtoonScraperError):  # TODO: 뒤에 Error 붙이기
    """Directory state recieved from check_directory_state is not wanted."""


class InvalidWebtoonId(WebtoonScraperError):
    """Webtoon id is invalid. Or it can be adult webtoon, which is currently not supported."""


class UnsupportedWebtoonRating(InvalidWebtoonId):
    """The weboon is not supported to download due to rating.

    WebtoonScraper does not support adult webtoon officially.
    """


class UseFetchEpisode(WebtoonScraperError):
    """Only fetch_episode_informations exists.

    사용되고 있지 않고 사용될지 여부가 불확실함.
    """

    def __init__(self, message: str = ''):
        super().__init__(message or 'Use `fetch_episode_informations` for get webtoon information.')


class InvalidBlogId(InvalidWebtoonId):
    """Invalid blog id. Maybe there's a typo or blog is closed.

    네이버 블로그의 경우 일반적인 웹툰 플렛폼들과는 다르게 blog id와 category number로
    분리되어 있고 처리 과정 중에 blog id가 잘못됐는지 category number가 잘못됐는지 확인할 수 있는
    로직이 있어서 따로 분리됨.
    """


class InvalidCategoryNo(InvalidWebtoonId):
    """Invalid category number. Maybe there's a typo or category is deleted. Check docs of InvalidBlogId for full description."""


class InvalidPlatformError(WebtoonScraperError):
    """Invalid platfrom error.

    Maybe you didn't select platform or typed invalid parameter.
    Or you misuse naver webtoon and best challenge.
    """


class UserCanceledError(WebtoonScraperError):
    """User revoked process."""
