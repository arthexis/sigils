from __future__ import annotations

from sigils import SafeNamespace, Secret, Sigil


def _candidate_events(metadata, kind):
    return [event for event in metadata["candidates"] if event["kind"] == kind]


def test_structural_whitespace_route_is_selected_first() -> None:
    metadata = Sigil("[service status]").explain(
        {"service": {"status": "ready"}}
    )

    assert metadata["resolved"] is True
    assert metadata["selected_interpretation"] == "whitespace_traverse"
    assert metadata["score"] >= 30
    created = _candidate_events(metadata, "candidate_created")
    assert [event["detail"] for event in created[:3]] == [
        "whitespace_traverse",
        "whitespace_call",
        "legacy_whitespace",
    ]
    not_selected = [
        event["detail"]
        for event in _candidate_events(metadata, "candidate_pruned")
        if event["outcome"] == "not_selected"
    ]
    assert "whitespace_call" in not_selected
    assert "legacy_whitespace" in not_selected


def test_legacy_whitespace_runs_only_after_semantic_routes_fail() -> None:
    def echo(value="default"):
        return value

    metadata = Sigil("[echo name]").explain(
        {"echo": echo, "name": "Ada"}
    )

    assert metadata["resolved"] is True
    assert metadata["selected_interpretation"] == "legacy_whitespace"
    assert metadata["score"] >= 10
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


def test_failed_whitespace_routes_reuse_segment_memo() -> None:
    metadata = Sigil("[missing value]").explain({})

    assert metadata["resolved"] is False
    assert metadata["memo"]["misses"] > 0
    assert metadata["memo"]["hits"] > 0


def test_whitespace_alias_resolution_preserves_semantic_route() -> None:
    metadata = Sigil("[service start-server]").explain(
        {"service": {"start_server": "ready"}}
    )

    assert metadata["resolved"] is True
    assert metadata["selected_interpretation"] == "whitespace_traverse"
    assert any(event["kind"] == "alias_selected" for event in metadata["trace"])


def test_whitespace_secret_traversal_remains_protected() -> None:
    metadata = Sigil("[account token]").explain(
        {"account": Secret({"token": "swordfish"})}
    )

    assert metadata["resolved"] is True
    assert metadata["protected"] is True
    assert metadata["value_type"] == "Secret"
    assert "swordfish" not in repr(metadata)


def test_whitespace_safe_namespace_traversal_remains_protected() -> None:
    metadata = Sigil("[node hostname]").explain(
        {"node": SafeNamespace({"hostname": "gway-001"})}
    )

    assert metadata["resolved"] is True
    assert metadata["protected"] is True
    assert metadata["selected_interpretation"] == "whitespace_traverse"


def test_whitespace_continuation_behavior_is_preserved() -> None:
    context = {
        "name": "Hello World",
        "slugify": lambda value: value.lower().replace(" ", "-"),
    }

    assert Sigil("[name slugify]").solve(context) == "hello-world"


def test_pending_whitespace_route_does_not_escape_as_success() -> None:
    def add(left, right):
        return left + right

    metadata = Sigil("[add left]").explain({"add": add, "left": 2})

    assert metadata["resolved"] is False
    assert metadata["selected_interpretation"] != "whitespace_call"


def test_existing_whitespace_call_behavior_is_preserved() -> None:
    context = {
        "double": lambda value: value * 2,
        "number": 4,
    }

    assert Sigil("[double number]").solve(context) == "8"
