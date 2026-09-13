from __future__ import annotations

from ..secret import Secret
from .constants import _UNRESOLVED
from .pending import PendingCall


_FAILURE_REASONS = {
    ("safe_callable_check", "rejected"): "unsafe_callable",
    ("callable_invoked", "failed"): "call_failed",
    ("greedy_call", "failed"): "call_failed",
    ("continuation_lookup", "failed"): "continuation_failed",
    ("traversal_failed", "unresolved"): "missing_member",
}


def _event_dict(event):
    """Return one public, serializable event without internal values."""
    return {
        "kind": event.kind,
        "segment": event.segment,
        "outcome": event.outcome,
        "detail": event.detail,
    }


def project_resolution(state, value, *, expression):
    """Project an already-produced semantic state into public metadata.

    The projection never resolves, invokes, reveals, or serializes the resolved
    payload. It only reads state and events produced by the normal resolver.
    """
    trace = tuple(state.trace)
    protected = state.protected or isinstance(value, Secret)
    pending = isinstance(value, PendingCall)
    budget_event = next(
        (
            event
            for event in reversed(trace)
            if event.kind == "complexity_budget" and event.outcome == "exhausted"
        ),
        None,
    )
    complete = value is not _UNRESOLVED and not pending and budget_event is None

    selected_interpretation = None
    resolution_mode = None
    callable_state = None
    pending_arguments = value.missing if pending else 0
    failure_reason = None

    for event in trace:
        if event.kind == "candidate_selected":
            selected_interpretation = event.detail
        elif event.kind == "resolution_mode":
            resolution_mode = event.detail
        elif event.kind == "callable_state":
            callable_state = event.outcome
        elif event.kind == "pending_call" and event.outcome == "created":
            callable_state = "pending"
            try:
                pending_arguments = int(event.detail or 0)
            except (TypeError, ValueError):
                pending_arguments = 0

    if not complete:
        if budget_event is not None:
            failure_reason = f"{budget_event.detail}_budget_exceeded"
        elif pending:
            failure_reason = "insufficient_arguments"
        else:
            for event in reversed(trace):
                reason = _FAILURE_REASONS.get((event.kind, event.outcome))
                if reason is not None:
                    failure_reason = reason
                    break
            if failure_reason is None:
                failure_reason = "no_interpretation"

    memo_events = [event for event in trace if event.kind == "segment_memo"]
    candidates = [
        _event_dict(event)
        for event in trace
        if event.kind in {"candidate_created", "candidate_pruned", "candidate_selected"}
    ]

    if value is _UNRESOLVED:
        value_type = None
    elif protected:
        value_type = "Secret"
    else:
        value_type = type(value).__name__

    return {
        "resolved": complete,
        "expression": expression,
        "selected_interpretation": selected_interpretation,
        "resolution_mode": resolution_mode,
        "value_type": value_type,
        "protected": protected,
        "callable_state": callable_state,
        "pending_arguments": pending_arguments,
        "failure_reason": failure_reason,
        "score": state.score,
        "budget": {
            "exhausted": budget_event is not None,
            "reason": budget_event.detail if budget_event is not None else None,
        },
        "memo": {
            "hits": sum(event.outcome == "hit" for event in memo_events),
            "misses": sum(event.outcome == "miss" for event in memo_events),
            "collisions": sum(event.outcome == "collision" for event in memo_events),
        },
        "candidates": candidates,
        "trace": [_event_dict(event) for event in trace],
    }


class IntrospectionMixin:
    """Public explanation API over the production semantic resolver."""

    def _explain_expression(self):
        """Return the single Sigil expression represented by this instance."""
        matches = list(self.pattern.finditer(self._template))
        if len(matches) != 1 or matches[0].span() != (0, len(self._template)):
            raise ValueError("explain() requires a template containing exactly one Sigil")
        return matches[0].group("expression")

    def explain(self, context=None):
        """Resolve this Sigil once and return serializable semantic metadata.

        Explanation is tooling behavior, not language syntax: it reuses the same
        production resolver, state, memo, candidate decisions, and trace as an
        ordinary evaluation while leaving punctuation such as ``?`` reserved for
        future language features.
        """
        context = {} if context is None else context
        expression = self._explain_expression()
        value = self._resolve_expression(expression, context)
        state = getattr(self, "_last_resolution_state", None)
        if state is None:
            raise RuntimeError("semantic resolution did not produce a state")
        return project_resolution(state, value, expression=expression)
