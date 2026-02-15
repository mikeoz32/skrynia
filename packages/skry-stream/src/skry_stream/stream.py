import asyncio
import heapq
import itertools
from collections import deque
from collections.abc import AsyncIterable, AsyncIterator, Awaitable, Callable, Iterable
from copy import copy
from inspect import isawaitable
from logging import getLogger
from typing import Any, Generic, TypeVar, cast

T = TypeVar("T")
R = TypeVar("R")


async def _await(value: R | Awaitable[R]) -> R:
    if isawaitable(value):
        return await cast(Awaitable[R], value)
    return value


def _extract_timestamp(item: Any) -> int:
    return int(cast(dict[str, Any], item)["timestamp"])


class Stream(Generic[T]):
    def __init__(self, source: AsyncIterable[T]) -> None:
        self._source = aiter(source)

    def __aiter__(self) -> AsyncIterator[T]:
        return self

    async def __anext__(self) -> T:
        return await self._source.__anext__()

    def split(self, branches: int | None = None) -> "Stream[T] | tuple[Stream[T], ...]":
        if branches is not None:
            if branches < 2:
                raise ValueError("branches must be >= 2")
            return _split_stream(self, branches)

        try:
            return Stream(copy(self._source))
        except TypeError:
            return Stream(self._source)

    def map(self, predicate: Callable[[T], R | Awaitable[R]]) -> "Stream[R]":
        async def _map() -> AsyncIterator[R]:
            async for item in self:
                yield await _await(predicate(item))

        return Stream(_map())

    def tap(self, callback: Callable[[T], Any | Awaitable[Any]]) -> "Stream[T]":
        async def _tap() -> AsyncIterator[T]:
            async for item in self:
                await _await(callback(item))
                yield item

        return Stream(_tap())

    def flatten(self: "Stream[Iterable[R]]") -> "Stream[R]":
        async def _flatten() -> AsyncIterator[R]:
            async for item in self:
                for nested in item:
                    yield nested

        return Stream(_flatten())

    def filter(self, predicate: Callable[[T], bool | Awaitable[bool]]) -> "Stream[T]":
        async def _filter() -> AsyncIterator[T]:
            async for item in self:
                if await _await(predicate(item)):
                    yield item

        return Stream(_filter())

    def enumerate(self, start: int = 0) -> "Stream[tuple[int, T]]":
        async def _enumerate() -> AsyncIterator[tuple[int, T]]:
            index = start
            async for item in self:
                yield index, item
                index += 1

        return Stream(_enumerate())

    def take(self, count: int) -> "Stream[T]":
        async def _take() -> AsyncIterator[T]:
            if count <= 0:
                return
            seen = 0
            iterator = aiter(self)
            while seen < count:
                try:
                    item = await anext(iterator)
                except StopAsyncIteration:
                    break
                yield item
                seen += 1

        return Stream(_take())

    def skip(self, count: int) -> "Stream[T]":
        async def _skip() -> AsyncIterator[T]:
            skipped = 0
            async for item in self:
                if skipped < count:
                    skipped += 1
                    continue
                yield item

        return Stream(_skip())

    def merge(self, *others: AsyncIterable[T]) -> "Stream[T]":
        async def _merge() -> AsyncIterator[T]:
            sources: tuple[AsyncIterable[T], ...] = (self, *others)
            done_marker = object()
            queue: asyncio.Queue[T | BaseException | object] = asyncio.Queue()

            async def _pump(source: AsyncIterable[T]) -> None:
                try:
                    async for item in source:
                        await queue.put(item)
                except BaseException as exc:
                    await queue.put(exc)
                finally:
                    await queue.put(done_marker)

            tasks = [asyncio.create_task(_pump(source)) for source in sources]
            active_sources = len(tasks)

            while active_sources > 0:
                item = await queue.get()
                if item is done_marker:
                    active_sources -= 1
                    continue
                if isinstance(item, BaseException):
                    for task in tasks:
                        task.cancel()
                    await asyncio.gather(*tasks, return_exceptions=True)
                    raise item
                yield cast(T, item)

            await asyncio.gather(*tasks, return_exceptions=True)

        return Stream(_merge())

    def zip(self, *others: AsyncIterable[Any]) -> "Stream[tuple[Any, ...]]":
        async def _zip() -> AsyncIterator[tuple[Any, ...]]:
            iterators = [aiter(self), *(aiter(other) for other in others)]

            while True:
                items: list[Any] = []
                for iterator in iterators:
                    try:
                        item = await anext(iterator)
                    except StopAsyncIteration:
                        return
                    items.append(item)
                yield tuple(items)

        return Stream(_zip())

    def zip_longest(
        self,
        *others: AsyncIterable[Any],
        fillvalue: Any = None,
    ) -> "Stream[tuple[Any, ...]]":
        async def _zip_longest() -> AsyncIterator[tuple[Any, ...]]:
            iterators = [aiter(self), *(aiter(other) for other in others)]
            finished = [False] * len(iterators)

            while True:
                items: list[Any] = []
                all_finished = True

                for index, iterator in enumerate(iterators):
                    if finished[index]:
                        items.append(fillvalue)
                        continue

                    try:
                        item = await anext(iterator)
                    except StopAsyncIteration:
                        finished[index] = True
                        items.append(fillvalue)
                        continue

                    items.append(item)
                    all_finished = False

                if all_finished:
                    return

                yield tuple(items)

        return Stream(_zip_longest())

    def merge_ordered(
        self,
        *others: AsyncIterable[T],
        key: Callable[[T], Any] | None = None,
    ) -> "Stream[T]":
        async def _merge_ordered() -> AsyncIterator[T]:
            sources: tuple[AsyncIterable[T], ...] = (self, *others)
            if not sources:
                return

            key_fn: Callable[[T], Any]
            if key is None:

                def _identity(value: T) -> T:
                    return value

                key_fn = _identity
            else:
                key_fn = key

            order_counter = itertools.count()
            heap: list[tuple[Any, int, int, T]] = []
            iterators = [aiter(source) for source in sources]

            for source_index, iterator in enumerate(iterators):
                try:
                    item = await anext(iterator)
                except StopAsyncIteration:
                    continue
                heapq.heappush(
                    heap,
                    (key_fn(item), source_index, next(order_counter), item),
                )

            while heap:
                _, source_index, _, item = heapq.heappop(heap)
                yield item
                iterator = iterators[source_index]
                try:
                    next_item = await anext(iterator)
                except StopAsyncIteration:
                    continue
                heapq.heappush(
                    heap,
                    (
                        key_fn(next_item),
                        source_index,
                        next(order_counter),
                        next_item,
                    ),
                )

        return Stream(_merge_ordered())

    def keyed(self, key_name: str) -> "Stream[tuple[Any, T]]":
        async def _keyed() -> AsyncIterator[tuple[Any, T]]:
            async for item in self:
                key = cast(dict[str, Any], item)[key_name]
                yield key, item

        return Stream(_keyed())

    def chunk(self, size: int = 10) -> "AggregatedStream":
        async def _chunk() -> AsyncIterator[list[T]]:
            chunk: list[T] = []
            async for item in self:
                if len(chunk) < size:
                    chunk.append(item)
                else:
                    yield chunk.copy()
                    chunk = [item]
            if chunk:
                yield chunk.copy()

        return AggregatedStream(_chunk())

    def window(
        self,
        interval: int = 1000,
        *,
        timestamp_getter: Callable[[T], int] | None = None,
        include_partial: bool = True,
    ) -> "AggregatedStream":
        get_timestamp = timestamp_getter or _extract_timestamp

        async def _window() -> AsyncIterator[list[T]]:
            chunk: list[T] = []
            ts: int | None = None
            async for item in self:
                timestamp = get_timestamp(item)
                if ts is None:
                    ts = timestamp
                if ts + interval >= timestamp:
                    chunk.append(item)
                else:
                    if chunk:
                        yield chunk.copy()
                    chunk = [item]
                    ts = timestamp
            if include_partial and chunk:
                yield chunk.copy()

        return AggregatedStream(_window())

    def sliding_window(
        self,
        size: int,
        advance: int,
        *,
        timestamp_getter: Callable[[T], int] | None = None,
        include_partial: bool = True,
    ) -> "AggregatedStream":
        if size <= 0:
            raise ValueError("size must be > 0")
        if advance <= 0:
            raise ValueError("advance must be > 0")

        get_timestamp = timestamp_getter or _extract_timestamp

        async def _window() -> AsyncIterator[list[T]]:
            windows: list[dict[str, Any]] = []
            last_start: int | None = None

            async for item in self:
                if item is None:
                    continue

                timestamp = get_timestamp(item)
                if last_start is None:
                    last_start = timestamp
                    windows.append({"ts": last_start, "items": []})
                else:
                    while timestamp - last_start >= advance:
                        last_start += advance
                        windows.append({"ts": last_start, "items": []})

                next_windows: list[dict[str, Any]] = []
                for window in windows:
                    window_items = cast(list[T], window["items"])
                    window_start = cast(int, window["ts"])
                    if timestamp - window_start >= size:
                        if window_items:
                            yield window_items
                        continue
                    window_items.append(item)
                    next_windows.append(window)

                windows = next_windows

            if include_partial:
                for window in windows:
                    window_items = cast(list[T], window["items"])
                    if window_items:
                        yield window_items

        return AggregatedStream(_window())

    async def to_list(self) -> list[T]:
        result: list[T] = []
        async for item in self:
            result.append(item)
        return result

    async def sink(
        self, sink: Callable[[T], Any | Awaitable[Any]], parallel: int = 1
    ) -> None:
        chunk: list[Awaitable[Any]] = []
        async for item in self:
            chunk.append(_await(sink(item)))
            if len(chunk) == parallel:
                await asyncio.gather(*chunk)
                getLogger("Stream").info("Gathering")
                chunk = []

        if chunk:
            await asyncio.gather(*chunk)


class AggregatedStream(Stream[Any]):
    def group_by(self, key_name: str) -> "Stream[dict[Any, list[Any]]]":
        async def _group_by() -> AsyncIterator[dict[Any, list[Any]]]:
            async for chunk in self:
                group: dict[Any, list[Any]] = {}
                for item in chunk:
                    key = cast(dict[str, Any], item)[key_name]
                    if key not in group:
                        group[key] = []
                    group[key].append(item)
                yield group

        return Stream(_group_by())

    def groupBy(self, key_name: str) -> "Stream[dict[Any, list[Any]]]":
        return self.group_by(key_name)


class _SplitState(Generic[T]):
    def __init__(self, source: AsyncIterable[T], branches: int) -> None:
        self.iterator = aiter(source)
        self.buffers: list[deque[T]] = [deque() for _ in range(branches)]
        self.done = False
        self.error: BaseException | None = None
        self.lock = asyncio.Lock()

    async def next_for(self, index: int) -> T:
        while True:
            buffer = self.buffers[index]
            if buffer:
                return buffer.popleft()

            if self.done:
                if self.error is not None:
                    raise self.error
                raise StopAsyncIteration

            async with self.lock:
                buffer = self.buffers[index]
                if buffer:
                    continue
                if self.done:
                    continue

                try:
                    item = await anext(self.iterator)
                except StopAsyncIteration:
                    self.done = True
                    continue
                except BaseException as exc:
                    self.error = exc
                    self.done = True
                    continue

                for branch_buffer in self.buffers:
                    branch_buffer.append(item)


def _split_stream(source: AsyncIterable[T], branches: int) -> tuple[Stream[T], ...]:
    state: _SplitState[T] = _SplitState(source, branches)

    def _branch(index: int) -> Stream[T]:
        async def _iterator() -> AsyncIterator[T]:
            while True:
                try:
                    yield await state.next_for(index)
                except StopAsyncIteration:
                    break

        return Stream(_iterator())

    return tuple(_branch(index) for index in range(branches))
