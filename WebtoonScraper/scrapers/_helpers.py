from __future__ import annotations

import functools
import json
from pathlib import Path
import textwrap
from typing import TYPE_CHECKING, Any
from collections.abc import Iterable

if TYPE_CHECKING:
    from WebtoonScraper.scrapers._scraper import Scraper

if TYPE_CHECKING:
    from typing import Self

from ..base import logger


class ExtraInfoScraper:
    """이미지 이외의 정보(댓글, 작가의 말, 별점 등)와 기타 프로세싱을 사용할 때 사용되는 추가적인 스크래퍼입니다."""

    def initializer(self, scraper: Scraper, webtoon_directory: Path):
        pass

    def finalizer(self, scraper: Scraper, extras: dict[str, Any], exc: BaseException | None):
        webtoon_directory: Path = extras["webtoon_directory"]
        thumbnail_name: str = extras["thumbnail_name"]
        # merge_number: int = extras["merge_number"]

        # information.json 추가
        if scraper.does_store_information:
            information_file = webtoon_directory / "information.json"
            if information_file.is_file():
                old_information = json.loads(information_file.read_text(encoding="utf-8"))
            else:
                old_information = {}

            information = scraper._get_information(old_information)
            information.update(
                thumbnail_name=thumbnail_name,
                information_name="information.json",
                original_webtoon_directory_name=webtoon_directory.name,
                # merge_number=merge_number,
                contents=["thumbnail", "information"],
            )
            with open(information_file, "w", encoding="utf-8") as f:
                json.dump(information, f, ensure_ascii=False, indent=2)


class EpisodeRange:
    def __init__(self):
        """range 인스턴스는 기본적으로 체크되지 않으며 나중에 오류가 발현될 수 있습니다."""
        self._ranges: list = []

    def __contains__(self, index: int):
        """잘못된 값을 지니는 slice 인스턴스를 가지고 있더라도 순서에 따라 오류 없이 값을 내보낼 수도 있습니다."""

        for range_ in reversed(self._ranges):
            not_invert, container = range_
            invert = not not_invert
            match container:
                case set(container):
                    if index in container:
                        return True ^ invert

                case slice(start=None, stop=None, step=None):
                    return True ^ invert

                case slice(start=None, stop=int(stop), step=int() | None as step):
                    step = 1 if step is None else step
                    if index in range(1, stop, step):
                        return True ^ invert

                case slice(start=int(start), stop=None, step=int() | None as step):
                    step = 1 if step is None else step
                    if start <= index and (start - index) % step == 0:
                        return True ^ invert

                case slice(start=int(start), stop=int(stop), step=int() | None as step):
                    step = 1 if step is None else step
                    if index in range(start, stop, step):
                        return True ^ invert

                case slice():
                    raise ValueError(f"Invalid slice value: {range_!r}")

                case _:
                    raise ValueError(f"Invalid range value: {range_!r}")

        return False

    def __repr__(self) -> str:
        return f"{type(self).__name__}({', '.join(repr(range_) for range_ in self._ranges)})"

    @staticmethod
    def _normalize_item(item):
        if isinstance(item, int):
            return {item}
        elif isinstance(item, set | range | slice):
            return item
        else:
            return set(item)

    def _add(self, item, not_invert: bool) -> None:
        if not self._ranges:
            normalized_item = self._normalize_item(item)
            self._ranges.append((not_invert, normalized_item))
            return

        last_not_invert, last_item = self._ranges[-1]
        match last_item, item, not_invert == last_not_invert:
            case int(last_item), int(item), True:
                self._ranges[-1] = {last_item, item}
            case set(last_item), int(item), True:
                last_item.add(item)
            case set(last_item), [*item], True:
                last_item.update(item)
            case _, item, _:
                normalized_item = self._normalize_item(item)
                self._ranges.append((not_invert, normalized_item))

    def add(self, item: slice | range | Iterable[int] | int):
        self._add(item, not_invert=True)

    def add_not(self, item: slice | range | Iterable[int] | int):
        self._add(item, not_invert=False)

    def apply_string(self, episode_range: str, inclusive: bool = True, exclusion_from_all: bool = True):
        first_run = True
        for range_str in episode_range.split(","):
            if range_str.startswith("!"):
                if first_run and exclusion_from_all:
                    self.add(slice(None))
                adder = self.add_not
                range_str = range_str[1:]
            else:
                adder = self.add
            first_run = False

            start, tilde, end = range_str.partition("~")
            start = start.replace(" ", "")
            start = int(start) if start else None
            end = end.replace(" ", "")
            end = int(end) + inclusive if end else None

            if tilde:
                adder(slice(start, end))
            elif start:
                adder(start)

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
        self = cls()
        self.apply_string(episode_range, inclusive)
        return self


def reload_manager(f):
    """함수의 결과값을 캐싱합니다. 단, reload 파라미터를 True로 둘 경우 다시 함수를 호출에 값을 받아옵니다.

    이 함수는 클래스의 메소드에만 적용시킬 수 있습니다.
    `__slots__`가 있다면 제대로 작동하지 않을 수 있는데, 그럴 경우 `__slots__`에 `_reload_cache`를 추가해 주세요.
    """

    # __slots__가 필요하다면 Scraper에 _return_cache를 구현하면 됨!
    @functools.wraps(f)
    def wrapper(self, *args, reload: bool = False, **kwargs):
        try:
            self._reload_cache  # noqa
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
