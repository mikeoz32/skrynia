import asyncio
from collections.abc import AsyncIterator
from typing import Any

import pytest
from skry_stream import Stream


async def source(items: list[Any]) -> AsyncIterator[Any]:
    for item in items:
        yield item


async def collect(stream: Stream[Any]) -> list[Any]:
    result: list[Any] = []
    async for item in stream:
        result.append(item)
    return result


@pytest.mark.asyncio
async def test_map_filter_and_flatten() -> None:
    numbers = Stream(source([1, 2, 3, 4]))
    mapped = numbers.map(lambda item: int(item) * 2).filter(lambda item: int(item) > 4)
    assert await collect(mapped) == [6, 8]

    nested = Stream(source([[1, 2], [3], [4, 5]])).flatten()
    assert await collect(nested) == [1, 2, 3, 4, 5]


@pytest.mark.asyncio
async def test_tap_take_skip_and_enumerate() -> None:
    seen: list[int] = []
    stream = Stream(source([1, 2, 3, 4, 5]))
    result = (
        await stream.tap(lambda item: seen.append(int(item))).skip(1).take(3).to_list()
    )
    assert seen == [1, 2, 3, 4]
    assert result == [2, 3, 4]

    indexed = await Stream(source(["a", "b"])).enumerate(start=10).to_list()
    assert indexed == [(10, "a"), (11, "b")]


@pytest.mark.asyncio
async def test_keyed_and_split() -> None:
    entries = [{"kind": "a", "value": 1}, {"kind": "b", "value": 2}]
    stream = Stream(source(entries))
    keyed = stream.keyed("kind")
    assert await collect(keyed) == [("a", entries[0]), ("b", entries[1])]

    split_stream = Stream(source([1])).split()
    assert isinstance(split_stream, Stream)
    assert await collect(split_stream) == [1]


@pytest.mark.asyncio
async def test_split_into_multiple_branches() -> None:
    first, second, third = Stream(source([1, 2, 3])).split(3)
    assert await collect(first) == [1, 2, 3]
    assert await collect(second) == [1, 2, 3]
    assert await collect(third) == [1, 2, 3]


@pytest.mark.asyncio
async def test_split_branch_validation() -> None:
    with pytest.raises(ValueError):
        Stream(source([1, 2, 3])).split(1)


@pytest.mark.asyncio
async def test_merge_combines_streams() -> None:
    async def delayed(items: list[int], delay: float) -> AsyncIterator[int]:
        for item in items:
            await asyncio.sleep(delay)
            yield item

    merged = Stream(delayed([1, 3, 5], 0.001)).merge(delayed([2, 4], 0.002))
    result = await merged.to_list()

    assert sorted(result) == [1, 2, 3, 4, 5]
    assert len(result) == 5


@pytest.mark.asyncio
async def test_merge_propagates_source_errors() -> None:
    async def broken() -> AsyncIterator[int]:
        yield 1
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError, match="boom"):
        await Stream(source([10])).merge(broken()).to_list()


@pytest.mark.asyncio
async def test_merge_handles_empty_and_single_source_cases() -> None:
    assert await Stream(source([1, 2, 3])).merge().to_list() == [1, 2, 3]
    assert await Stream(source([])).merge(source([])).to_list() == []


@pytest.mark.asyncio
async def test_merge_multiple_streams_with_interleaving() -> None:
    async def delayed(items: list[int], delay: float) -> AsyncIterator[int]:
        for item in items:
            await asyncio.sleep(delay)
            yield item

    merged = Stream(delayed([1, 4, 7], 0.001)).merge(
        delayed([2, 5, 8], 0.0015),
        delayed([3, 6, 9], 0.002),
    )
    result = await merged.to_list()
    assert sorted(result) == [1, 2, 3, 4, 5, 6, 7, 8, 9]


@pytest.mark.asyncio
async def test_merge_ordered_with_numbers_default_key() -> None:
    left = Stream(source([1, 4, 7]))
    right = source([2, 3, 6])
    third = source([5, 8])
    result = await left.merge_ordered(right, third).to_list()
    assert result == [1, 2, 3, 4, 5, 6, 7, 8]


@pytest.mark.asyncio
async def test_merge_ordered_with_custom_key_for_dict_items() -> None:
    first = Stream(source([{"ts": 1, "v": "a"}, {"ts": 4, "v": "d"}]))
    second = source([{"ts": 2, "v": "b"}, {"ts": 3, "v": "c"}])
    result = await first.merge_ordered(
        second, key=lambda item: int(item["ts"])
    ).to_list()
    assert [item["v"] for item in result] == ["a", "b", "c", "d"]


@pytest.mark.asyncio
async def test_merge_ordered_preserves_source_priority_for_equal_keys() -> None:
    first = Stream(source([{"k": 1, "src": "a1"}, {"k": 2, "src": "a2"}]))
    second = source([{"k": 1, "src": "b1"}, {"k": 2, "src": "b2"}])
    result = await first.merge_ordered(
        second, key=lambda item: int(item["k"])
    ).to_list()
    assert [item["src"] for item in result] == ["a1", "b1", "a2", "b2"]


@pytest.mark.asyncio
async def test_merge_ordered_handles_empty_streams() -> None:
    result = (
        await Stream(source([])).merge_ordered(source([]), source([1, 2])).to_list()
    )
    assert result == [1, 2]


@pytest.mark.asyncio
async def test_merge_ordered_propagates_source_errors() -> None:
    async def broken() -> AsyncIterator[int]:
        yield 2
        raise RuntimeError("ordered boom")

    with pytest.raises(RuntimeError, match="ordered boom"):
        await Stream(source([1, 3])).merge_ordered(broken()).to_list()


@pytest.mark.asyncio
async def test_merge_ordered_propagates_key_errors() -> None:
    with pytest.raises(KeyError):
        await (
            Stream(source([{"ts": 1}]))
            .merge_ordered(
                source([{"no_ts": 2}]),
                key=lambda item: int(item["ts"]),
            )
            .to_list()
        )


@pytest.mark.asyncio
async def test_zip_two_streams() -> None:
    left = Stream(source([1, 2, 3]))
    right = source(["a", "b", "c"])
    result = await left.zip(right).to_list()
    assert result == [(1, "a"), (2, "b"), (3, "c")]


@pytest.mark.asyncio
async def test_zip_stops_on_shortest_stream() -> None:
    left = Stream(source([1, 2, 3, 4]))
    right = source(["a", "b"])
    result = await left.zip(right).to_list()
    assert result == [(1, "a"), (2, "b")]


@pytest.mark.asyncio
async def test_zip_three_streams() -> None:
    first = Stream(source([1, 2, 3]))
    second = source([10, 20, 30])
    third = source([100, 200, 300])
    result = await first.zip(second, third).to_list()
    assert result == [(1, 10, 100), (2, 20, 200), (3, 30, 300)]


@pytest.mark.asyncio
async def test_zip_empty_source() -> None:
    result = await Stream(source([])).zip(source([1, 2, 3])).to_list()
    assert result == []


@pytest.mark.asyncio
async def test_zip_propagates_source_errors() -> None:
    async def broken() -> AsyncIterator[int]:
        yield 10
        raise RuntimeError("zip boom")

    with pytest.raises(RuntimeError, match="zip boom"):
        await Stream(source([1, 2])).zip(broken()).to_list()


@pytest.mark.asyncio
async def test_zip_longest_two_streams_with_fillvalue() -> None:
    left = Stream(source([1, 2, 3]))
    right = source(["a"])
    result = await left.zip_longest(right, fillvalue="-").to_list()
    assert result == [(1, "a"), (2, "-"), (3, "-")]


@pytest.mark.asyncio
async def test_zip_longest_three_streams_default_fillvalue() -> None:
    first = Stream(source([1]))
    second = source([10, 20])
    third = source([100, 200, 300])
    result = await first.zip_longest(second, third).to_list()
    assert result == [(1, 10, 100), (None, 20, 200), (None, None, 300)]


@pytest.mark.asyncio
async def test_zip_longest_with_empty_streams() -> None:
    assert await Stream(source([])).zip_longest(source([])).to_list() == []
    result = await Stream(source([])).zip_longest(source([1, 2]), fillvalue=0).to_list()
    assert result == [(0, 1), (0, 2)]


@pytest.mark.asyncio
async def test_zip_longest_propagates_source_errors() -> None:
    async def broken() -> AsyncIterator[int]:
        yield 1
        raise RuntimeError("zip longest boom")

    with pytest.raises(RuntimeError, match="zip longest boom"):
        await Stream(source([10, 20])).zip_longest(broken()).to_list()


@pytest.mark.asyncio
async def test_chunk_and_group_by_alias() -> None:
    records = [
        {"kind": "a", "value": 1},
        {"kind": "b", "value": 2},
        {"kind": "a", "value": 3},
    ]
    grouped = await collect(Stream(source(records)).chunk(size=3).group_by("kind"))
    assert grouped == [{"a": [records[0], records[2]], "b": [records[1]]}]

    alias_grouped = await collect(Stream(source(records)).chunk(size=3).groupBy("kind"))
    assert alias_grouped == grouped

    chunks = await collect(Stream(source([1, 2, 3])).chunk(size=2))
    assert chunks == [[1, 2], [3]]


@pytest.mark.asyncio
async def test_window_and_sliding_window() -> None:
    points = [{"timestamp": 0}, {"timestamp": 1}, {"timestamp": 4}, {"timestamp": 5}]
    windowed = await collect(Stream(source(points)).window(interval=2))
    assert windowed == [[points[0], points[1]], [points[2], points[3]]]

    sliding_points = [
        {"timestamp": 0, "value": "a"},
        {"timestamp": 1, "value": "b"},
        {"timestamp": 2, "value": "c"},
        {"timestamp": 3, "value": "d"},
    ]
    sliding = await collect(
        Stream(source(sliding_points)).sliding_window(size=3, advance=2)
    )
    assert sliding == [
        [sliding_points[0], sliding_points[1], sliding_points[2]],
        [sliding_points[2], sliding_points[3]],
    ]


@pytest.mark.asyncio
async def test_window_with_timestamp_getter_and_no_partial() -> None:
    points = [
        {"ts": 0, "value": "a"},
        {"ts": 1, "value": "b"},
        {"ts": 4, "value": "c"},
    ]
    result = (
        await Stream(source(points))
        .window(
            interval=2,
            timestamp_getter=lambda item: int(item["ts"]),
            include_partial=False,
        )
        .to_list()
    )
    assert result == [[points[0], points[1]]]


@pytest.mark.asyncio
async def test_sliding_window_validation() -> None:
    with pytest.raises(ValueError):
        await (
            Stream(source([{"timestamp": 1}]))
            .sliding_window(size=0, advance=1)
            .to_list()
        )
    with pytest.raises(ValueError):
        await (
            Stream(source([{"timestamp": 1}]))
            .sliding_window(size=1, advance=0)
            .to_list()
        )


@pytest.mark.asyncio
async def test_sink_processes_tail_chunk() -> None:
    values = Stream(source([1, 2, 3]))
    seen: list[int] = []

    async def sink(item: Any) -> None:
        seen.append(int(item))

    await values.sink(sink, parallel=2)
    assert seen == [1, 2, 3]
