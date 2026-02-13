from __future__ import annotations

from typing import Annotated, Any, get_args, get_origin, get_type_hints

from skry_di import Container


def _contains_doc(annotation: Any) -> bool:
    if get_origin(annotation) is not Annotated:
        return False
    extras = get_args(annotation)[1:]
    return any(type(item).__name__ == "Doc" for item in extras)


def test_public_api_contains_doc_metadata() -> None:
    hints = get_type_hints(Container.register, include_extras=True)
    assert _contains_doc(hints["token"])
    assert _contains_doc(hints["provider"])
