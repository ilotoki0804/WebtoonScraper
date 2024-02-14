import contextlib
import logging
from typing import Any, Callable, Generic, Iterable, TypeAlias, TypeVar

# import coloredlogs


__title__ = "WebtoonScraper"
__description__ = "Scraping webtoons with ease."
__url__ = "https://github.com/ilotoki0804/WebtoonScraper"
__version_info__ = (3, 1, 2)
__version__ = str.join(".", map(str, __version_info__))
__author__ = "ilotoki0804"
__author_email__ = "ilotoki0804@gmail.com"
__license__ = "Apache-2.0"

__github_user_name__ = __author__
__github_project_name__ = __title__

WebtoonId: TypeAlias = (
    "int | str | tuple[int, int] | tuple[str, int] | tuple[str, str]"  # + ' | NaverPostWebtoonId | NaverBlogWebtoonId'
)
EpisodeNoRange: TypeAlias = "tuple[int | None, int | None] | int | None | Iterable[int] | slice"

logger = logging.getLogger("webtoonscraper_logger")
# coloredlogs.install(logger=logger, datefmt='%H:%M:%S')


# CHANGE REPORTER


class Missing:
    pass


missing = Missing()
ValueType = TypeVar("ValueType")
UsingClass = TypeVar("UsingClass")


class ChangeReporter(Generic[ValueType, UsingClass]):
    def __init__(
        self,
        default_value: ValueType | Missing = missing,
        value_unchanging_callback: Callable[[UsingClass, str, ValueType, ValueType], Any] | None = None,
        value_changing_callback: Callable[[UsingClass, ValueType, ValueType, str], ValueType] | None = None,
    ) -> None:
        if not isinstance(default_value, Missing):
            self.default_value: ValueType = default_value

        if value_changing_callback and value_unchanging_callback:
            raise TypeError("value_changing_callback and value_unchanging_callback cannot be defined same time.")

        self.value_changing_callback = value_changing_callback
        self.value_unchanging_callback = value_unchanging_callback

    def get_value(self, instance: UsingClass | None = None) -> ValueType:
        try:
            return getattr(instance, f"_{self.name}_value")
        except AttributeError:
            return self.default_value

    def set_value(self, value: ValueType, instance: UsingClass) -> None:
        try:
            setattr(instance, f"_{self.name}_value", value)
        except AttributeError:
            logger.warning(
                "Failed to set value to instance. Instance may be defined __slots__. "
                f"Please delete it or add '_{self.name}_value' to your __slots__."
            )

    def __get__(self, instance: UsingClass, cls: type[UsingClass]) -> ValueType:
        # print('get', instance, cls)

        with contextlib.suppress(AttributeError):
            return self.get_value(instance)

        raise AttributeError(f"AttributeError: '{cls.__name__}' object has no attribute '{self.name}'")

    def __set__(self, instance: UsingClass, new_value: ValueType) -> None:
        old_value = self.get_value()
        if self.value_changing_callback is not None:
            new_value = self.value_changing_callback(instance, old_value, new_value, self.name)
        elif self.value_unchanging_callback is not None:
            self.value_unchanging_callback(instance, self.name, new_value, old_value)

        self.set_value(new_value, instance)

    def __delete__(self, instance: UsingClass) -> None:
        with contextlib.suppress(AttributeError):
            delattr(instance, f"_{self.name}_value")

    def __set_name__(self, owner: type[UsingClass], name: str) -> None:
        self.name = name
