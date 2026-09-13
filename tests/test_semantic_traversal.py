from __future__ import annotations

import threading

from sigils import Sigil
from sigils.sigil import session as session_module
from sigils.sigil.session import SemanticResolutionSession


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


def test_segment_memo_rejects_stale_entry_when_owner_identity_changes(monkeypatch) -> None:
    """An id collision must not reuse another owner's cached resolution."""

    class Owner:
        def __init__(self, value: str) -> None:
            self.value = value

    monkeypatch.setattr(session_module, "id", lambda _owner: 1, raising=False)
    session = SemanticResolutionSession({})
    first = Owner("first")
    second = Owner("second")

    first_result = session.resolve_member(first, "value", aliases=lambda _key: (), segment=0)
    second_result = session.resolve_member(second, "value", aliases=lambda _key: (), segment=0)

    assert first_result.value == "first"
    assert second_result.value == "second"
    memo_events = [event for event in session.state.trace if event.kind == "segment_memo"]
    assert [event.outcome for event in memo_events] == ["miss", "collision"]


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


def test_same_sigil_can_solve_concurrently_with_isolated_sessions() -> None:
    sigil = Sigil("[value]")
    barrier = threading.Barrier(2)
    session_ids = []
    results = []

    original_begin = sigil._begin_resolution_session

    def synchronized_begin(context):
        session, owns_session = original_begin(context)
        session_ids.append(id(session))
        barrier.wait()
        return session, owns_session

    sigil._begin_resolution_session = synchronized_begin

    def solve(value):
        results.append(sigil.solve({"value": value}))

    threads = [threading.Thread(target=solve, args=(value,)) for value in ("a", "b")]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert sorted(results) == ["a", "b"]
    assert len(set(session_ids)) == 2
