import skry_stream
from skry_stream.stream import AggregatedStream, Stream


def test_public_exports() -> None:
    assert skry_stream.Stream is Stream
    assert skry_stream.AggregatedStream is AggregatedStream


def test_version_is_present() -> None:
    assert isinstance(skry_stream.__version__, str)
    assert skry_stream.__version__
