from __future__ import annotations

from sigils import Sigil


def _candidate_events(metadata, kind):
    return [event for event in metadata["candidates"] if event["kind"] == kind]


def test_structural_whitespace_route_is_selected_first() -> None:
    metadata = Sigil("[service status]").explain(
        {"service": {"status": "ready"}}
    )

    assert metadata["resolved"] is True
    assert metadata["selected_interpretation"] == "whitespace_traverse"
    created = _candidate_events(metadata, "candidate_created")
    assert [event["detail"] for event in created[:3]] == [
        "whitespace_traverse",
        "whitespace_call",
        "legacy_whitespace",
    ]


def test_legacy_whitespace_runs_only_after_semantic_routes_fail() -> None:
    def echo(value="default"):
        return value

    metadata = Sigil("[echo name]").explain(
        {"echo": echo, "name": "Ada"}
    )

    assert metadata["resolved"] is True
    assert metadata["selected_interpretation"] == "legacy_whitespace"
    failed = [
        event["detail"]
        for event in _candidate_events(metadata, "candidate_pruned")
        if event["outcome"] == "failed"
    ]
    assert failed[:2] == ["whitespace_traverse", "whitespace_call"]


def test_lower_ranked_legacy_route_is_not_speculatively_executed() -> None:
    calls = 0

    def service(value):
        nonlocal calls
        calls += 1
        return value

    service.action = "ready"

    result = Sigil("[service action]").solve({"service": service})

    assert result == "ready"
    assert calls == 0


def test_whitespace_route_beam_never_exceeds_global_limit() -> None:
    metadata = Sigil("[service status]").explain(
        {"service": {"status": "ready"}}
    )

    created = _candidate_events(metadata, "candidate_created")
    route_candidates = [
        event
        for event in created
        if event["detail"]
        in {"whitespace_traverse", "whitespace_call", "legacy_whitespace"}
    ]
    assert 0 < len(route_candidates) <= 4


def test_existing_whitespace_call_behavior_is_preserved() -> None:
    context = {
        "double": lambda value: value * 2,
        "number": 4,
    }

    assert Sigil("[double number]").solve(context) == "8"
