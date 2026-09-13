from __future__ import annotations

from sigils import Sigil


def _budget_events(metadata):
    return [
        event
        for event in metadata["trace"]
        if event["kind"] == "complexity_budget" and event["outcome"] == "exhausted"
    ]


def test_nested_resolution_budget_stops_recursive_argument_resolution() -> None:
    context = {
        "double": lambda value: value * 2,
        "number": 4,
    }
    sigil = Sigil("[double.number]")
    sigil.max_nested_resolution_depth = 1

    metadata = sigil.explain(context)

    assert metadata["resolved"] is False
    assert metadata["failure_reason"] == "nested_resolution_depth_budget_exceeded"
    assert metadata["budget"] == {
        "exhausted": True,
        "reason": "nested_resolution_depth",
    }
    assert len(_budget_events(metadata)) == 1


def test_default_nested_budget_preserves_continuation_behavior() -> None:
    context = {
        "value": "hello",
        "transform": lambda value: value.upper(),
    }

    assert Sigil("[value.transform]").solve(context) == "HELLO"


def test_zero_fallback_budget_disables_legacy_compatibility_route() -> None:
    sigil = Sigil("[missing value]")
    sigil.max_fallback_depth = 0

    metadata = sigil.explain({})

    assert metadata["resolved"] is False
    assert metadata["failure_reason"] == "fallback_depth_budget_exceeded"
    assert metadata["budget"] == {"exhausted": True, "reason": "fallback_depth"}
    assert len(_budget_events(metadata)) == 1


def test_depth_budget_is_fresh_for_each_evaluation() -> None:
    sigil = Sigil("[missing value]")
    sigil.max_fallback_depth = 0

    first = sigil.explain({})
    second = sigil.explain({})

    assert first["failure_reason"] == "fallback_depth_budget_exceeded"
    assert second["failure_reason"] == "fallback_depth_budget_exceeded"
    assert len(_budget_events(first)) == 1
    assert len(_budget_events(second)) == 1
