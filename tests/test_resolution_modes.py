from __future__ import annotations

from sigils import Sigil
from sigils.sigil.modes import CallableKind, CallableState, ResolutionMode
from sigils.sigil.pending import PendingCall


def test_resolution_modes_encode_current_traversal_contract() -> None:
    assert ResolutionMode.CALL.invoke_final
    assert ResolutionMode.CALL.greedy_calls
    assert ResolutionMode.TRAVERSE.invoke_final
    assert not ResolutionMode.TRAVERSE.greedy_calls
    assert not ResolutionMode.LOOKUP.invoke_final
    assert ResolutionMode.LOOKUP.greedy_calls
    assert not ResolutionMode.LOCAL.continuation
    assert not ResolutionMode.LOCAL.root_lookup


def test_callable_state_classifies_value_ready_bound_and_pending() -> None:
    def function(value=None):
        return value

    pending = PendingCall(function=function, missing=2)

    assert CallableState.classify("value").kind is CallableKind.VALUE
    assert CallableState.classify(function).kind is CallableKind.READY
    assert CallableState.classify(function, bound=True).kind is CallableKind.BOUND
    pending_state = CallableState.classify(pending)
    assert pending_state.kind is CallableKind.PENDING
    assert pending_state.missing == 2


def test_whitespace_first_pass_records_traverse_mode() -> None:
    sigil = Sigil("[record name]")

    assert sigil.solve({"record": {"name": "value"}}) == "value"
    mode_events = [
        event
        for event in sigil._last_resolution_state.trace
        if event.kind == "resolution_mode"
    ]
    assert mode_events
    assert mode_events[0].detail == "traverse"


def test_greedy_whitespace_retry_records_call_mode() -> None:
    sigil = Sigil("[join left right]")
    context = {
        "join": lambda left, right: f"{left}:{right}",
        "left": "a",
        "right": "b",
    }

    assert sigil.solve(context) == "a:b"
    modes = [
        event.detail
        for event in sigil._last_resolution_state.trace
        if event.kind == "resolution_mode"
    ]
    assert "traverse" in modes
    assert "call" in modes


def test_lookup_mode_does_not_invoke_final_callable() -> None:
    calls = []

    def transform(value):
        calls.append(value)
        return value

    sigil = Sigil("[value - transform]")

    assert sigil.solve({"value": "x", "transform": transform}) == "x"
    assert calls == ["x"]


def test_callable_trace_uses_typed_state() -> None:
    sigil = Sigil("[value.transform]")
    context = {
        "value": "x",
        "transform": lambda value: value.upper(),
    }

    assert sigil.solve(context) == "X"
    callable_states = [
        state
        for state in (
            getattr(event, "detail", None)
            for event in sigil._last_resolution_state.trace
            if event.kind == "callable_state"
        )
    ]
    assert callable_states
