from __future__ import annotations

from sigils import SafeNamespace
from sigils.sigil.member import resolve_member
from sigils.sigil.semantic import (
    MAX_STATES,
    BoundedResolutionBeam,
    ResolutionEvent,
    ResolutionState,
    SegmentMemo,
)


def no_aliases(key: str) -> tuple[str, ...]:
    return ()


def separator_aliases(key: str) -> tuple[str, ...]:
    return (key.replace("-", "_"),) if "-" in key else ()


def test_bounded_resolution_beam_keeps_only_four_states() -> None:
    values = [object() for _ in range(6)]
    states = [ResolutionState(index, value, score=index) for index, value in enumerate(values)]

    beam = BoundedResolutionBeam(states)

    assert len(beam.states) == MAX_STATES == 4
    assert [state.score for state in beam.states] == [5, 4, 3, 2]


def test_bounded_resolution_beam_merges_dominated_equivalent_states() -> None:
    value = object()
    weaker = ResolutionState(1, value, score=10)
    stronger = ResolutionState(1, value, score=20).event(
        ResolutionEvent("member_lookup", segment=1, outcome="success")
    )

    beam = BoundedResolutionBeam([weaker, stronger])

    assert beam.states == (stronger,)


def test_resolution_state_records_events_without_mutating_original() -> None:
    original = ResolutionState(0, object(), score=5)
    event = ResolutionEvent("root_lookup", segment=0, outcome="success")

    updated = original.event(event, score=10)

    assert original.trace == ()
    assert original.score == 5
    assert updated.trace == (event,)
    assert updated.score == 15


def test_segment_memo_reuses_only_explicitly_cached_work() -> None:
    memo = SegmentMemo()
    key = (1, "service", "client")
    value = object()

    assert memo.get(key) is None
    assert memo.set(key, value) is value
    assert memo.get(key) is value
    assert len(memo) == 1

    memo.clear()
    assert memo.get(key) is None


def test_member_resolution_prefers_exact_key_over_alias() -> None:
    owner = {"send-value": "exact", "send_value": "alias"}

    result = resolve_member(owner, "send-value", aliases=separator_aliases)

    assert result.value == "exact"
    assert result.alias is None


def test_member_resolution_reports_selected_alias() -> None:
    owner = {"send_value": "alias"}

    result = resolve_member(owner, "send-value", aliases=separator_aliases)

    assert result.value == "alias"
    assert result.alias == "send_value"


def test_member_resolution_blocks_attributes_after_safe_namespace() -> None:
    class Client:
        send = "attribute"

    owner = SafeNamespace({"client": Client()})
    client = resolve_member(owner, "client", aliases=no_aliases)

    assert client.resolved
    assert client.protected

    send = resolve_member(
        client.value,
        "send",
        aliases=no_aliases,
        protected_path=client.protected,
    )

    assert not send.resolved
    assert send.protected


def test_member_resolution_allows_protected_nested_mapping_aliases() -> None:
    owner = SafeNamespace({"client": {"send_value": "mapped"}})
    client = resolve_member(owner, "client", aliases=no_aliases)

    send = resolve_member(
        client.value,
        "send-value",
        aliases=separator_aliases,
        protected_path=client.protected,
    )

    assert send.resolved
    assert send.protected
    assert send.value == "mapped"
