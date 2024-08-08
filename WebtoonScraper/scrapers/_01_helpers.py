from __future__ import annotations

import functools
import textwrap
from typing import TYPE_CHECKING, Iterable

if TYPE_CHECKING:
    from typing import Self

from ..base import logger


class ExtraInfoScraper:
    """이미지 이외의 정보(댓글, 작가의 말, 별점 등)을 불러올 때 사용되는 추가적인 스크래퍼입니다."""


class EpisodeRange:
    def __init__(self, *ranges: slice | range | Iterable[int] | int):
        """range 인스턴스는 기본적으로 체크되지 않으며 나중에 오류가 발현될 수 있습니다."""

        if not ranges:
            self._ranges = []
            return

        new_ranges: list[slice | range | set[int]] = []
        indexes = set()
        for range_ in ranges:
            if isinstance(range_, slice | range):
                new_ranges.append(range_)
            elif isinstance(range_, Iterable):
                indexes.update(range_)
            else:
                indexes.add(range_)
        if indexes:
            new_ranges.append(indexes)
        self._ranges = new_ranges

    def __contains__(self, index: int):
        """잘못된 값을 지니는 slice 인스턴스를 가지고 있더라도 순서에 따라 오류 없이 값을 내보낼 수도 있습니다."""

        for range_ in self._ranges:
            match range_:
                case set():
                    if index in range_:
                        return True

                case slice(start=None, stop=int(stop), step=int() | None as step):
                    step = 1 if step is None else step
                    if index in range(1, stop, step):
                        return True

                case slice(start=int(start), stop=None, step=int() | None as step):
                    step = 1 if step is None else step
                    if start <= index and (start - index) % step == 0:
                        return True

                case slice(start=int(start), stop=int(stop), step=int() | None as step):
                    step = 1 if step is None else step
                    if index in range(start, stop, step):
                        return True

                case slice():
                    raise ValueError(f"Invalid slice value: {range_!r}")

                case _:
                    raise ValueError(f"Invalid range value: {range_!r}")

        return False

    def __repr__(self) -> str:
        return f"{type(self).__name__}({', '.join(repr(range_) for range_ in self._ranges)})"

    @classmethod
    def from_string(cls, episode_range: str, inclusive: bool = True) -> Self:
        """문자열로부터 EpisodeRange 인스턴스를 만듭니다.

        Args:
            episode_range (str):
                에피소드 범위가 될 문자열입니다. 규칙은 다음과 같습니다.
                여러 에피소드를 쉼표로 나누어 병렬하여 나타내면
                각각의 에피소드를 다운로드받습니다.
                예를 들어 `1,4,45`는 1화, 4화, 45화가 선택됩니다.
                에피소드 수를 모두 쓰는 대신 범위를 지정해줄 수 있습니다.
                예를 들어 `5~20`은 5화부터 20화까지(inclusive=True일때) 범위가 선택됩니다.
                이때 시작이나 끝을 생략할 수 있습니다.
                예를 들어 `7~`은 7화부터 끝날 때가지 범위를 선택하며
                `~31`은 시작부터 31화까지 범위를 선택하며 `1~31`과 같습니다.
                범위 선택과 에피소드 수 쓰기는 쉼표로 나누어 병렬할 수 있습니다.
                예를 들어 `2,15,5~10,45~`은 2화, 15화, 5~10화, 45화부터 끝까지 다운로드한다는 의미입니다.
            inclusive (bool, True):
                맨 마지막 인덱스를 포함할지 결정합니다. 기본값은 True입니다.
                예를 들어 `5~10`일때 inclusive=True라면 10회차를 포함하고,
                False라면 포함하지 않아 5회차부터 9회차까지만 포함합니다.
        """
        ranges = []
        for range_str in episode_range.split(","):
            start, tilde, end = range_str.partition("~")
            start = start.replace(" ", "")
            start = int(start) if start else None
            end = end.replace(" ", "")
            end = int(end) + inclusive if end else None

            if tilde:
                ranges.append(slice(start, end))
            elif start:
                ranges.append(start)

        return cls(*ranges)


def reload_manager(f):
    """함수의 결과값을 캐싱합니다. 단, reload 파라미터를 True로 둘 경우 다시 함수를 호출에 값을 받아옵니다.

    이 함수는 클래스의 메소드에만 적용시킬 수 있습니다.
    `__slots__`가 있다면 제대로 작동하지 않을 수 있는데, 그럴 경우 `__slots__`에 `_reload_cache`를 추가해 주세요.
    """

    # __slots__가 필요하다면 Scraper에 _return_cache를 구현하면 됨!
    @functools.wraps(f)
    def wrapper(self, *args, reload: bool = False, **kwargs):
        try:
            self._reload_cache
        except AttributeError:
            self._reload_cache = {}

        if f in self._reload_cache:
            if not reload:
                logger.debug(
                    f"{f} is already loaded, so loading is skipped. In order to reload, set `reload` parameter to True."
                )
                return self._reload_cache[f]
            logger.info("Refreshing webtoon_information")

        return_value = f(self, *args, reload=reload, **kwargs)
        self._reload_cache[f] = return_value
        return return_value

    return wrapper


def shorten(text: str):
    shortened = textwrap.shorten(text, width=15, placeholder="...")
    return f"'{shortened}'"
