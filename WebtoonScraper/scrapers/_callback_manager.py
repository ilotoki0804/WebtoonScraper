from __future__ import annotations

import asyncio
import logging
import typing
from collections import defaultdict
from collections.abc import Callable, Coroutine
from contextlib import asynccontextmanager
from typing import (
    Any,
    NamedTuple,
    TypeVar,
    overload,
)

from ..base import logger

CallableT = TypeVar("CallableT", bound=Callable)
LogLevel = typing.Literal["debug", "info", "warning", "error", "critical"] | int


class Callback(NamedTuple):
    function: Callable
    is_async: bool
    replace_default: bool
    use_task: bool | None = None


class CallbackManager:
    """콜백을 관리합니다."""

    def __init__(self, default_context: dict | None = None):
        self.callbacks: defaultdict[str, list[Callback]] = defaultdict(list)
        self.default_context = default_context or {}

    def default(
        self,
        message: str | Callable | None = None,
        extra_context: dict | None = None,
        *,
        func: Callable | None = None,
        level: LogLevel = "info",
        progress_update: str | Callable | None = None,
        log_with_progress: bool = False,
        is_async: bool = False,
        use_task: bool = False,
    ) -> Callback:
        """기본 콜백을 생성합니다."""

        if func is not None:
            return Callback(
                func,
                is_async=is_async,
                use_task=use_task,
                replace_default=False,  # no-op
            )

        if isinstance(level, str):
            level = logging._nameToLevel[level.upper()]

        if is_async:
            async def log(**context):  # type: ignore
                nonlocal extra_context
                extra_context = extra_context or {}

                self = context["scraper"]
                if self.use_progress_bar and progress_update is not None:
                    if isinstance(progress_update, str):
                        log = progress_update.format(**context, **extra_context)
                    else:
                        log = await progress_update(**context, **extra_context)
                    self.progress.update(self.progress_task_id, description=log)
                    updated = True
                else:
                    updated = False

                if message is not None and (not updated or updated and log_with_progress):
                    if isinstance(message, str):
                        log = message.format(**context, **extra_context)
                    else:
                        log = await message(**context, **extra_context)
                    logger.log(level, log)
        else:
            def log(**context):
                nonlocal extra_context
                extra_context = extra_context or {}

                self = context["scraper"]
                if self.use_progress_bar and progress_update is not None:
                    if isinstance(progress_update, str):
                        log = progress_update.format(**context, **extra_context)
                    else:
                        log = progress_update(**context, **extra_context)
                    self.progress.update(self.progress_task_id, description=log)
                    updated = True
                else:
                    updated = False

                if message is not None and (not updated or updated and log_with_progress):
                    if isinstance(message, str):
                        log = message.format(**context, **extra_context)
                    else:
                        log = message(**context, **extra_context)
                    logger.log(level, log)

        return Callback(
            log,
            is_async=is_async,
            use_task=use_task,
            replace_default=False,  # no-op
        )

    @overload
    def register_async(self, trigger: str, func: CallableT, *, replace_default: bool = False, blocking: bool = True) -> CallableT: ...

    @overload
    def register_async(self, trigger: str, *, replace_default: bool = False, blocking: bool = True) -> Callable[[CallableT], CallableT]: ...

    def register_async(self, trigger: str, func: Callable[..., Coroutine] | None = None, *, replace_default: bool = False, blocking: bool = True) -> Any:
        """특정 callback 트리거가 발생했을 때 실행할 비동기 콜백을 등록합니다."""
        if func is None:
            return lambda func: self.register_async(trigger, func, replace_default=replace_default, blocking=blocking)

        # blocking으로 할지 말지를 callback을 등록할 때 해야 할까, 아님 부를 때 결정해야 할까?
        # 실례를 한번 봐야 할 것 같은데 아직은 잘 모르겠다.
        # 일단 지금은 callback을 등록할 때 결정하는 것으로 한다.
        self.callbacks[trigger].append(Callback(func, is_async=True, replace_default=replace_default, use_task=not blocking))
        return func

    def remove(self, trigger: str, func_or_callback: Callable | Callback) -> None:
        if isinstance(func_or_callback, Callback):
            self.callbacks[trigger].remove(func_or_callback)
        else:
            self.callbacks[trigger][:] = (callback for callback in self.callbacks[trigger] if callback.function is not func_or_callback)

    @overload
    def register(self, trigger: str, func: CallableT, *, replace_default: bool = False) -> CallableT: ...

    @overload
    def register(self, trigger: str, *, log_format: str, log_level: typing.Literal["info", "warning", "error", "critical"] | int = "info", replace_default: bool = False) -> None: ...

    @overload
    def register(self, trigger: str, *, replace_default: bool = False) -> Callable[[CallableT], CallableT]: ...

    def register(
        self,
        trigger: str,
        func: Callable | None = None,
        *,
        log_format: str | None = None,
        log_level: LogLevel = "info",
        replace_default: bool = False,
    ):
        """특정 callback 트리거가 발생했을 때 실행할 콜백을 등록합니다.

        Example:
            ```python
            scraper = Scraper.from_url(...)
            @scraper.register_callback("setup"):
            def startup_message(scraper: Scraper, finishing: bool, **context):
                if not finishing:
                    print("Download has been started!")
            scraper.download_webtoon()

            # output:
            # ...
            # Download has been started!
            # ...
            ```

        Note:
            이 메서드는 메서드로도 데코레이터로도 사용될 수 있습니다.
            callback과 마찬가지로 등록된 함수들도 진행을 멈추고 호출되니 지연되지 않도록 주의해야 합니다.

        Args:
            trigger (str): callback을 실행할 명령어를 결정합니다.
            func (Callable, optional): 이 인자는 설정되지 않을 수 있으며, 설정되지 않을 경우 데코레이터로서 사용할 수 있습니다.
            replace_default (bool, optional): 기본으로 설정되어 있는 callback을 대체할 것인지 설정합니다. True로 설정할 경우 기존 callback은 실행되지 않습니다.
        """
        if func is None and log_format is None:
            return lambda func: self.register(trigger, func, replace_default=replace_default)

        if log_format is not None:
            if isinstance(log_level, str):
                log_level = logging._nameToLevel[log_level.upper()]
            func = lambda scraper, **context: logger.log(log_level, log_format.format(context))  # noqa: E731

        self.callbacks[trigger].append(Callback(func, is_async=False, replace_default=replace_default))  # type: ignore
        return func

    async def async_callback(
        self,
        situation: str,
        default_callback: Callback | None = None,
        **context,
    ) -> list[asyncio.Task] | None:
        # async_callback이 callback을 부르지 않으니 둘 다 수정하도록 할 것
        # async_callback이 더 상위 개념이고 async_callback이
        # callback도 부를 수 있으니 async_callback을 사용할 수 있는 순간에는
        # 무조건 async_callback을 사용할 것.
        skip_default = False
        tasks = []
        if callbacks := self.callbacks.get(situation):
            for callback in callbacks:
                if callback.is_async:
                    if callback.use_task:
                        # task가 제대로 종료되는지 확인하는 것은 caller의 몫
                        task = asyncio.create_task(callback.function(**self.default_context, **context))
                        tasks.append(task)
                    else:
                        await callback.function(**self.default_context, **context)
                else:
                    callback.function(**self.default_context, **context)
                if callback.replace_default:
                    skip_default = True

        if not skip_default and default_callback is not None:
            if default_callback.is_async:
                await default_callback.function(**self.default_context, **context)
            else:
                default_callback.function(**self.default_context, **context)

        if context:
            logger.debug(f"{situation}: {context}")
        else:
            logger.debug(f"{situation}:")

        return tasks or None

    def callback(
        self,
        situation: str,
        default_callback: Callback | None = None,
        **context,
    ) -> None:
        # async_callback이 callback을 부르지 않으니 둘 다 수정하도록 할 것
        skip_default = False
        if callbacks := self.callbacks.get(situation):
            for callback in callbacks:
                if callback.is_async:
                    logger.error("An registered async callback is ignored. This callback does not support async callbacks.")
                    continue  # callback이 실행되지 않을 경우 skip_callback을 enable하지 않음
                else:
                    callback.function(**self.default_context, **context)
                if callback.replace_default:
                    skip_default = True

        if not skip_default and default_callback is not None:
            if default_callback.is_async:
                logger.error("A default async callback is ignored. This callback does not support async callbacks.")
            else:
                default_callback.function(**self.default_context, **context)

        if context:
            logger.debug(f"{situation}: {context}")
        else:
            logger.debug(f"{situation}:")

    # TODO: 실제로 유용하게 사용될 수 있는지 분석하기
    @asynccontextmanager
    async def with_context(self, context: dict | None = None):
        context = context or {}
        yield lambda *args, **kwargs: self.async_callback(*args, **context, **kwargs)

    @asynccontextmanager
    async def context(self, context_name: str, *, start_default: Callback | None = None, end_default: Callback | None = None, **contexts):
        await self.async_callback(context_name, start_default, finishing=False, **contexts)
        end_contexts: dict = dict(finishing=True, is_successful=True)
        yield end_contexts
        await self.async_callback(context_name, end_default, **end_contexts)
