from __future__ import annotations

from sigils import Sigil
from sigils.sigil.session import SemanticResolutionSession


def test_member_and_continuation_branch_without_speculative_invocation() -> None:
    calls = 0

    def normalize(value):
        nonlocal calls
        calls += 1
        return f"root:{value}"

    sigil = Sigil("[record.normalize]")
    result = sigil.solve(
        {
            "record": {"normalize": "mapping"},
            "normalize": normalize,
        }
    )

    assert result == "mapping"
    assert calls == 0
    events = sigil._last_resolution_state.trace
    created = [event.detail for event in events if event.kind == "candidate_created"]
    assert "member" in created
    assert "continuation" in created
    assert any(
        event.kind == "candidate_selected" and event.detail == "member"
        for event in events
    )
    assert any(
        event.kind == "candidate_pruned" and event.detail == "continuation"
        for event in events
    )


def test_continuation_is_selected_when_member_route_is_missing() -> None:
    calls = 0

    def slugify(value):
        nonlocal calls
        calls += 1
        return value.lower().replace(" ", "-")

    sigil = Sigil("[name.slugify]")

    assert sigil.solve({"name": "Hello World", "slugify": slugify}) == "hello-world"
    assert calls == 1
    assert any(
        event.kind == "candidate_selected" and event.detail == "continuation"
        for event in sigil._last_resolution_state.trace
    )


def test_candidate_selection_honors_hard_beam_width() -> None:
    session = SemanticResolutionSession({})
    values = [object() for _ in range(6)]
    candidates = [
        (f"candidate-{index}", value, index, None, False)
        for index, value in enumerate(values)
    ]

    selected = session.select_candidate(candidates, segment=1)

    assert selected is not None
    assert selected[0] == "candidate-5"
    dropped = [
        event
        for event in session.state.trace
        if event.kind == "candidate_pruned" and event.outcome == "beam_dropped"
    ]
    assert len(dropped) == 2
