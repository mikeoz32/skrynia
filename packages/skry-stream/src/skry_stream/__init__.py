from importlib.metadata import PackageNotFoundError, version

from .stream import AggregatedStream, Stream

try:
    __version__ = version("skry-stream")
except PackageNotFoundError:
    __version__ = "0.1.0"

__all__ = ["__version__", "AggregatedStream", "Stream"]
