"""Single literal fallback behavior for Sigils."""

import pytest

from sigils import Sigil


def test_missing_value_uses_literal_default() -> None:
    assert Sigil("[missing | fallback]").solve({}) == "fallback"


def test_fallback_rhs_is_not_resolved_from_context() -> None:
    context = {"fallback": "context-value"}
    assert Sigil("[missing | fallback]").solve(context) == "fallback"


@pytest.mark.parametrize(
    ("expression", "expected"),
    [
        ("[missing|default]", "default"),
        ("[missing |default]", "default"),
        ("[missing| default]", "default"),
        ("[missing | default]", "default"),
    ],
)
def test_optional_whitespace_around_separator(expression: str, expected: str) -> None:
    assert Sigil(expression).solve({}) == expected


@pytest.mark.parametrize(
    "value",
    [False, 0, "", [], {}, ()],
)
def test_falsey_resolved_values_do_not_trigger_fallback(value) -> None:
    result = Sigil("[value | fallback]").results({"value": value})
    assert result["value | fallback"] == value


@pytest.mark.parametrize(
    ("literal", "expected"),
    [
        ("/tmp/gway-runs", "/tmp/gway-runs"),
        ("https://example.test/a?b=c", "https://example.test/a?b=c"),
        ("10", "10"),
        ("production mode", "production mode"),
        ("", ""),
    ],
)
def test_literal_defaults_are_returned_as_text(literal: str, expected: str) -> None:
    assert Sigil(f"[missing | {literal}]").solve({}) == expected


def test_resolved_value_wins_over_literal_default() -> None:
    assert Sigil("[name | fallback]").solve({"name": "primary"}) == "primary"


@pytest.mark.parametrize(
    "expression",
    [
        "[a|b|c]",
        "[a || b]",
        "[a || b || c]",
    ],
)
def test_multiple_top_level_fallback_separators_are_rejected(expression: str) -> None:
    with pytest.raises(ValueError, match="only one top-level fallback"):
        Sigil(expression).solve({})


def test_quoted_pipe_is_not_a_top_level_fallback_separator() -> None:
    left, default = Sigil._split_fallback_expression('call("a|b") | default')
    assert left == 'call("a|b")'
    assert default == "default"


def test_nested_pipe_is_not_a_top_level_fallback_separator() -> None:
    left, default = Sigil._split_fallback_expression("call({a|b}) | default")
    assert left == "call({a|b})"
    assert default == "default"


def test_colon_prefixed_fallback_is_literal_text() -> None:
    context = {":offline": "colon-key"}
    assert Sigil("[missing | :offline]").solve(context) == ":offline"


def test_trailing_colon_is_ordinary_lookup_data() -> None:
    context = {"ready": lambda: "called", "ready:": "literal-key"}
    assert Sigil("[ready:]") % context == "literal-key"


def test_colon_with_right_side_does_not_force_call() -> None:
    context = {
        "name": "Alice",
        "greet": lambda value: f"Hello, {value}!",
    }
    assert Sigil("[greet:name]") % context == "[greet:name]"
