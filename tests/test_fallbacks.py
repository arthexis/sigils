"""Fallback-chain and literal-value behavior for Sigils."""

from sigils import Sigil


def test_fallback_uses_first_truthy_value() -> None:
    context = {"primary": "", "secondary": "ready", "tertiary": "later"}
    assert Sigil("[primary|secondary|tertiary]") % context == "ready"


def test_fallback_skips_unresolved_and_false_values() -> None:
    context = {"disabled": False, "count": 0, "name": "live"}
    assert Sigil("[missing|disabled|count|name]") % context == "live"


def test_fallback_returns_last_falsey_value_when_none_are_truthy() -> None:
    context = {"disabled": False, "count": 0}
    assert Sigil("[disabled|count]") % context == "0"


def test_literal_fallback_is_terminal() -> None:
    context = {"missing_too": "should-not-be-read"}
    assert Sigil("[missing|:offline|missing_too]") % context == "offline"


def test_literal_fallback_can_include_spaces() -> None:
    assert Sigil("[missing|:not available]") % {} == "not available"


def test_trailing_colon_returns_left_side_as_literal() -> None:
    context = {"ready": lambda: "called"}
    assert Sigil("[ready:]") % context == "ready"


def test_colon_with_right_side_still_forces_call() -> None:
    context = {
        "name": "Alice",
        "greet": lambda value: f"Hello, {value}!",
    }
    assert Sigil("[greet:name]") % context == "Hello, Alice!"
