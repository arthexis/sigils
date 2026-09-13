from __future__ import annotations

from sigils import Sigil


def test_production_traversal_records_real_resolution_events() -> None:
    sigil = Sigil("[service.client.status]")
    context = {"service": {"client": {"status": "ready"}}}

    assert sigil.solve(context) == "ready"

    state = sigil._last_resolution_state
    kinds = [event.kind for event in state.trace]
    assert kinds.count("member_lookup") >= 3
    assert "segment_resolved" in kinds
    assert kinds[-1] == "traversal_complete"
    assert state.value == "ready"
    assert state.position == 2


def test_whitespace_retry_reuses_segment_memo_for_greedy_call() -> None:
    sigil = Sigil("[join left right]")
    context = {
        "join": lambda left, right: f"{left}:{right}",
        "left": "a",
        "right": "b",
    }

    assert sigil.solve(context) == "a:b"

    memo_events = [
        event
        for event in sigil._last_resolution_state.trace
        if event.kind == "segment_memo"
    ]
    assert any(event.outcome == "miss" for event in memo_events)
    assert any(event.outcome == "hit" for event in memo_events)
    assert sigil._last_resolution_memo_size > 0


def test_segment_memo_avoids_repeating_descriptor_lookup_across_retry() -> None:
    class Service:
        def __init__(self) -> None:
            self.reads = 0

        @property
        def status(self) -> str:
            self.reads += 1
            return "ready"

    service = Service()
    sigil = Sigil("[service status missing]")

    sigil.solve({"service": service})

    assert service.reads == 1
    assert any(
        event.kind == "segment_memo" and event.outcome == "hit"
        for event in sigil._last_resolution_state.trace
    )


def test_continuation_behavior_is_preserved_under_semantic_traversal() -> None:
    sigil = Sigil("[name.slugify]")
    context = {
        "name": "Hello World",
        "slugify": lambda value: value.lower().replace(" ", "-"),
    }

    assert sigil.solve(context) == "hello-world"
    assert any(
        event.kind == "continuation_lookup" and event.outcome == "selected"
        for event in sigil._last_resolution_state.trace
    )


def test_each_solve_gets_a_fresh_semantic_session() -> None:
    sigil = Sigil("[value]")

    assert sigil.solve({"value": "first"}) == "first"
    first_state = sigil._last_resolution_state
    first_memo_size = sigil._last_resolution_memo_size

    assert sigil.solve({"value": "second"}) == "second"
    second_state = sigil._last_resolution_state

    assert first_state.value == "first"
    assert second_state.value == "second"
    assert first_memo_size > 0
    assert sigil._last_resolution_memo_size > 0
    assert second_state.trace[0].outcome == "miss"
