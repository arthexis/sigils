from __future__ import annotations

from sigils import Sigil
from sigils.secret import Secret
from sigils.sigil.sequences import split_top_level_sequence


def test_comma_expression_constructs_tuple() -> None:
    context = {"a": 1, "b": 2, "c": 3}

    result = Sigil("[a, b, c]").results(context)

    assert result["a, b, c"] == (1, 2, 3)


def test_top_level_sequence_split_respects_nested_groups_and_quotes() -> None:
    assert split_top_level_sequence("a, call(x, y), 'z,w'") == (
        "a",
        "call(x, y)",
        "'z,w'",
    )


def test_dot_traversal_indexes_tuple() -> None:
    context = {"values": ("zero", "one", "two", "three")}

    assert Sigil("[values.3]").solve(context) == "three"


def test_whitespace_traversal_indexes_tuple() -> None:
    context = {"values": ("zero", "one", "two", "three")}

    assert Sigil("[values 3]").solve(context) == "three"


def test_negative_index_uses_python_sequence_semantics() -> None:
    context = {"values": ("zero", "one", "two")}

    assert Sigil("[values.-1]").solve(context) == "two"


def test_out_of_range_index_remains_unresolved() -> None:
    context = {"values": ("zero", "one")}

    assert Sigil("[values.4]").solve(context) == "[values.4]"


def test_tuple_construction_preserves_secret_items() -> None:
    context = {"public": "visible", "token": Secret("swordfish")}

    result = Sigil("[public, token]").results(context)

    assert result["public, token"] == ("visible", Secret.REDACTED)
    assert "swordfish" not in repr(result)


def test_directional_binding_can_capture_constructed_tuple() -> None:
    context = {"a": "first", "b": "second"}

    assert Sigil("[a, b -> pair] [pair.1]").solve(context) == (
        "('first', 'second') second"
    )
