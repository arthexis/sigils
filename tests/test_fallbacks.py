"""Fallback-chain behavior for Sigils."""

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


def test_fallback_resolves_normal_branch_from_context() -> None:
    context = {"offline": "offline", "missing_too": "should-not-be-read"}
    assert Sigil("[missing|offline|missing_too]") % context == "offline"


def test_colon_prefixed_fallback_is_an_ordinary_lookup_key() -> None:
    context = {":offline": "colon-key"}
    assert Sigil("[missing|:offline]") % context == "colon-key"


def test_trailing_colon_is_ordinary_lookup_data() -> None:
    context = {"ready": lambda: "called", "ready:": "literal-key"}
    assert Sigil("[ready:]") % context == "literal-key"


def test_colon_with_right_side_does_not_force_call() -> None:
    context = {
        "name": "Alice",
        "greet": lambda value: f"Hello, {value}!",
    }
    assert Sigil("[greet:name]") % context == "[greet:name]"
