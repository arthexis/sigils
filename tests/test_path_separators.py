from __future__ import annotations

from sigils import Sigil


def test_space_and_dot_both_traverse_nested_values() -> None:
    context = {"health": {"errors": 3}}

    assert Sigil("[health.errors]").solve(context) == "3"
    assert Sigil("[health errors]").solve(context) == "3"


def test_space_traverses_callable_attributes_before_calling() -> None:
    def probe(value: str) -> str:
        return f"called:{value}"

    probe.status = "ready"
    context = {"probe": probe, "status": "argument"}

    assert Sigil("[probe status]").solve(context) == "ready"


def test_space_falls_back_to_call_when_traversal_fails() -> None:
    def probe(value: str) -> str:
        return f"called:{value}"

    context = {"probe": probe, "name": "Alice"}

    assert Sigil("[probe name]").solve(context) == "called:Alice"


def test_colon_always_calls_instead_of_traversing() -> None:
    def probe(value: str) -> str:
        return f"called:{value}"

    probe.status = "ready"
    context = {"probe": probe, "status": "argument"}

    assert Sigil("[probe:status]").solve(context) == "called:argument"


def test_colon_supports_keyword_arguments() -> None:
    def ip(interface: str) -> str:
        return f"ip:{interface}"

    context = {"network": {"ip": ip}, "wlan0": "wlan0"}

    assert Sigil("[network ip : interface=wlan0]").solve(context) == "ip:wlan0"


def test_colon_supports_positional_arguments() -> None:
    def ip(interface: str) -> str:
        return f"ip:{interface}"

    context = {"network": {"ip": ip}, "wlan0": "wlan0"}

    assert Sigil("[network ip : wlan0]").solve(context) == "ip:wlan0"


def test_multiple_colons_support_multiple_positional_arguments() -> None:
    def combine(left: str, right: str) -> str:
        return f"{left}/{right}"

    context = {"combine": combine, "first": "A", "second": "B"}

    assert Sigil("[combine:first:second]").solve(context) == "A/B"


def test_multiple_colons_support_multiple_keyword_arguments() -> None:
    def combine(left: str, right: str) -> str:
        return f"{left}/{right}"

    context = {"combine": combine, "first": "A", "second": "B"}

    expression = "[combine:left=first:right=second]"
    assert Sigil(expression).solve(context) == "A/B"


def test_multiple_colons_can_mix_positional_and_keyword_arguments() -> None:
    def combine(left: str, *, right: str) -> str:
        return f"{left}/{right}"

    context = {"combine": combine, "first": "A", "second": "B"}

    assert Sigil("[combine:first:right=second]").solve(context) == "A/B"


def test_percent_prefix_keeps_structured_argument_literal() -> None:
    def echo(value: str) -> str:
        return value

    context = {"echo": echo, "wlan0": "resolved"}

    assert Sigil("[echo:%wlan0]").solve(context) == "wlan0"


def test_final_callable_invokes_without_colon_and_trailing_colon_is_literal() -> None:
    context = {"now": lambda: "current"}

    assert Sigil("[now]").solve(context) == "current"
    assert Sigil("[now:]").solve(context) == "now"


def test_colon_requires_callable_left_side() -> None:
    context = {"health": {"errors": 3}}

    assert Sigil("[health:errors]").solve(context) == "[health:errors]"
