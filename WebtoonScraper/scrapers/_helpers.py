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

    def register(self, scraper: Scraper) -> None:
        # self.scraper = scraper
        scraper.register_callback("initialize", self.initializer)
        scraper.register_callback("finalize", self.finalizer)

    def initializer(self, scraper: Scraper, webtoon_directory: Path):
        pass

    def finalizer(self, scraper: Scraper, finishing: bool, extras: dict[str, Any] | None = None, exc: BaseException | None = None):
        if not finishing:
            return
        else:  # TODO: 나중에 elif TYPE_CHECKING으로 변경
            assert exc is not None
            assert extras is not None

        webtoon_directory: Path = extras["webtoon_directory"]
        thumbnail_path: Path | None = extras.get("thumbnail_name")

        if thumbnail_path is None:
            thumbnail_name = None
        else:
            thumbnail_name = thumbnail_path.name

        # information.json 추가
        information_file = webtoon_directory / "information.json"
        if information_file.is_file():
            try:
                old_information = json.loads(information_file.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                logger.warning(
                    "Failed to parse existing information.json file since it's corrupted. Old information will be ignored."
                )
                old_information = {}
        else:
            old_information = {}

        if isinstance(scraper.webtoon_id, str | int):
            webtoon_id = scraper.webtoon_id
        elif isinstance(scraper.webtoon_id, Iterable):
            # webtoon id가 튜플일 경우 그 안의 요소들은
            # int이거나 str일 거라는 가정 하에 작동하는 코드.
            # 그렇지 않는다면 수정해야 함!
            webtoon_id = tuple(scraper.webtoon_id)
        else:
            raise ValueError(f"Invalid webtoon id type to parse: {type(scraper.webtoon_id).__name__}")

        information = scraper._get_information(old_information)
        information.update(
            webtoon_id=webtoon_id,
            thumbnail_name=thumbnail_name,
            information_name="information.json",
            original_webtoon_directory_name=webtoon_directory.name,
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


def async_reload_manager(f):
    """함수의 결과값을 캐싱합니다. 단, reload 파라미터를 True로 둘 경우 다시 함수를 호출해 값을 받아옵니다."""
    _NOTSET = object()
    _cache = _NOTSET

    @functools.wraps(f)
    async def wrapper(*args, reload: bool = False, **kwargs):
        nonlocal _cache
        if reload or _cache is _NOTSET:
            _cache = await f(*args, reload=reload, **kwargs)
        return _cache

    return wrapper


def shorten(text: str):
    shortened = textwrap.shorten(text, width=15, placeholder="...")
    return f"'{shortened}'"
