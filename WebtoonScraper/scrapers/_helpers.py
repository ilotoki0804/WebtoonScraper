from __future__ import annotations

import asyncio
import functools
import json
import textwrap
from collections.abc import Iterable
from pathlib import Path
from typing import TYPE_CHECKING, NamedTuple, Self
from collections.abc import Callable

from WebtoonScraper.exceptions import AuthenticationError
import filetype
from filetype.types import IMAGE

if TYPE_CHECKING:
    from WebtoonScraper.scrapers._scraper import Scraper

from ..base import __version__ as version


class ExtraInfoScraper:
    """이미지 이외의 정보(댓글, 작가의 말, 별점 등)와 기타 프로세싱을 사용할 때 사용되는 추가적인 스크래퍼입니다."""

    def register(self, scraper: Scraper) -> None:
        # self.scraper = scraper
        scraper.register_callback("download_started", self.initializer)
        scraper.register_callback("download_ended", self.finalizer)

    def unregister(self, scraper: Scraper) -> None:
        scraper.unregister_callback("download_started", self.initializer)
        scraper.unregister_callback("download_ended", self.finalizer)

    def initializer(self, scraper: Scraper, webtoon_directory: Path):
        pass

    def finalizer(self, finishing: bool, **context):
        if not finishing:
            return

        exc: BaseException | None = context["exc"]
        extras: dict = context["extras"]
        scraper: Scraper = context["scraper"]

        webtoon_directory: Path = extras["webtoon_directory"]
        thumbnail_path: Path | None = extras.get("thumbnail_path")

        if thumbnail_path is None:
            thumbnail_name = None
        else:
            thumbnail_name = thumbnail_path.name

        if isinstance(scraper.webtoon_id, str | int):
            webtoon_id = scraper.webtoon_id
        elif isinstance(scraper.webtoon_id, Iterable):
            # webtoon id가 튜플일 경우 그 안의 요소들은
            # int이거나 str일 거라는 가정 하에 작동하는 코드.
            # 그렇지 않는다면 수정해야 함!
            webtoon_id = tuple(scraper.webtoon_id)
        else:
            raise ValueError(f"Invalid webtoon id type to parse: {type(scraper.webtoon_id).__name__}")

        information = scraper._get_information()
        information.update(
            webtoon_id=webtoon_id,
            thumbnail_name=thumbnail_name,
            information_name="information.json",
            original_webtoon_directory_name=webtoon_directory.name,
            contents=["thumbnail", "information"],
        )
        with open(webtoon_directory / "information.json", "w", encoding="utf-8") as f:
            # 버전은 맨 위에 오는 것이 가장 보기 좋음
            json.dump(dict(version=version) | information, f, ensure_ascii=False)


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


class Callback(NamedTuple):
    function: Callable
    is_async: bool
    replace_default: bool
    use_task: bool | None = None


class BearerMixin:
    @property
    def bearer(self) -> str | None:
        return self._bearer

    @bearer.setter
    def bearer(self, value: str | None) -> None:
        if value is not None and value and (not value.startswith("Bearer") or value == "Bearer ..."):
            raise AuthenticationError("Invalid bearer. Please provide valid bearer.")
        self._bearer = value
        if value is not None:
            self.headers.update({"Authorization": value})  # type: ignore
            self.json_headers.update({"Authorization": value})  # type: ignore


# code from https://discuss.python.org/t/boundedtaskgroup-to-control-parallelism/27171, with small variation
class BoundedTaskGroup(asyncio.TaskGroup):
    def __init__(self, max_task: int) -> None:
        self._semaphore = asyncio.Semaphore(max_task)
        super().__init__()

    async def _wrap_coroutine(self, coro):
        async with self._semaphore:
            return await coro

    def create_task(self, coro, *, name=None, context=None):
        coro = self._wrap_coroutine(coro)
        return super().create_task(coro, name=name, context=context)


def async_reload_manager(f):
    """함수의 결과값을 캐싱합니다. 단, reload 파라미터를 True로 둘 경우 다시 함수를 호출해 값을 받아옵니다."""

    # 주의: 클로저를 이용한 캐싱을 사용하면 인스턴스별로 설정되지 않아 재앙이 닥칠 수 있다
    @functools.wraps(f)
    async def wrapper(self, *args, reload: bool = False, **kwargs):
        if not hasattr(self, "_cache"):
            self._cache = {}

        result = self._cache.get(f)
        if reload or result is None:
            result = await f(self, *args, reload=reload, **kwargs)
            self._cache[f] = result
        return result

    return wrapper


def shorten(string: str, width: int = 30, *, ellipsis: str = "...", quote: bool = False):
    if quote:
        width -= 2
    if len(string) <= width:
        if quote:
            string = f"'{string}'"
        return string
    else:
        string = string[:width - len(ellipsis)] + ellipsis
        if quote:
            string = f"'{string}'"
        return string


def boolean_option(value: str) -> bool:
    # sqlite에서 boolean pragma statement를 처리하는 방식을 참고함
    # https://www.sqlite.org/pragma.html
    match value.strip().lower():
        case "1" | "yes" | "true" | "on":
            return True
        case "0" | "no" | "false" | "off":
            return False
        case other:
            raise ValueError(f"{other!r} can't be represented as boolean.")


def infer_filetype(content_type: str | None, image_raw: bytes | None) -> str:
    if content_type:
        # content-type 헤더에서 추론
        content_type = content_type.lower()
        for filetype_cls in IMAGE:
            if filetype_cls.MIME == content_type:
                return filetype_cls.EXTENSION

    if image_raw is None:
        raise ValueError("Failed to infer file extension contents.")

    # 파일 헤더에서 추론
    file_extension = filetype.guess_extension(image_raw)
    if not file_extension:
        raise ValueError("Failed to infer file extension contents.")
        # 만약 필요한 경우 가장 흔한 확장자읜 jpg로 fallback하는 아래의 코드를 사용할 것.
        # return "jpg"
    return file_extension
