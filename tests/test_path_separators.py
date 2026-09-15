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


def test_colon_does_not_force_a_call() -> None:
    def probe(value: str) -> str:
        return f"called:{value}"

    context = {"probe": probe, "status": "argument"}

    assert Sigil("[probe:status]").solve(context) == "[probe:status]"


def test_colon_is_part_of_an_exact_lookup_key() -> None:
    context = {"logs:read": "scope", "12:30": "time"}

    assert Sigil("[logs:read]").solve(context) == "scope"
    assert Sigil("[12:30]").solve(context) == "time"


def test_colon_bearing_literal_templates_stay_opaque() -> None:
    values = (
        "https://logs.arthexis.com",
        "foo:bar:baz",
        "scope=logs:read",
    )

    for value in values:
        assert Sigil(value).solve({}) == value


def test_double_colon_is_not_a_local_call_operator() -> None:
    context = {
        "service": {"send": lambda value: f"local:{value}"},
        "payload": "data",
    }

    assert Sigil("[service::send]").solve(context) == "[service::send]"


def test_final_callable_invokes_without_colon() -> None:
    context = {"now": lambda: "current"}

    assert Sigil("[now]").solve(context) == "current"
    assert Sigil("[now:]").solve(context) == "[now:]"
