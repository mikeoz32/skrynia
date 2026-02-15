# skry-stream

`skry-stream` provides lightweight async stream primitives for composing event pipelines.

## Features

- lazy async transformations (`map`, `filter`, `flatten`)
- windowing helpers (`chunk`, `window`, `sliding_window`)
- aggregation helpers (`group_by` and `groupBy` compatibility alias)
- async sink with bounded parallelism

## Install

```bash
uv add skry-stream
```

## Quick example

```python
from skry_stream import Stream

async def source():
    for item in [1, 2, 3, 4]:
        yield item

stream = Stream(source()).map(lambda x: x * 2).filter(lambda x: x > 4)

async for item in stream:
    print(item)
```
