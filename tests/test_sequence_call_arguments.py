from __future__ import annotations

from sigils import Sigil


def test_call_argument_tuple_split_ignores_nested_commas() -> None:
    sigil = Sigil("[value]")
    context = {"a": 1, "b": 2}

    assert sigil._resolve_call_argument("a, (b, a)", context) == (
        1,
        "(b, a)",
    )
