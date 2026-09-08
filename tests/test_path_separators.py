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


def test_colon_can_force_zero_argument_call() -> None:
    context = {"now": lambda: "current"}

    assert Sigil("[now:]").solve(context) == "current"


def test_colon_requires_callable_left_side() -> None:
    context = {"health": {"errors": 3}}

    assert Sigil("[health:errors]").solve(context) == "[health:errors]"
