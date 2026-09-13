from __future__ import annotations

import json

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
    complete = value is not _UNRESOLVED and not pending

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
        if pending:
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
        "memo": {
            "hits": sum(event.outcome == "hit" for event in memo_events),
            "misses": sum(event.outcome == "miss" for event in memo_events),
            "collisions": sum(event.outcome == "collision" for event in memo_events),
        },
        "candidates": candidates,
        "trace": [_event_dict(event) for event in trace],
    }


class IntrospectionMixin:
    """Language-level ``?`` projection over the active semantic resolver."""

    def _resolve_single_expression(self, expression, context):
        stripped = expression.strip()
        if not stripped.endswith("?"):
            return super()._resolve_single_expression(expression, context)

        inner = stripped[:-1].rstrip()
        if not inner or inner.endswith("?"):
            return super()._resolve_single_expression(expression, context)

        # Resolve exactly once through the ordinary production path. Because
        # _resolve_expression() already owns the semantic session, this nested
        # call reuses the same trace and memo rather than starting diagnostics.
        value = super()._resolve_single_expression(inner, context)
        session = getattr(self, "_resolution_session", None)
        if session is None:
            return _UNRESOLVED

        metadata = project_resolution(session.state, value, expression=inner)
        return json.dumps(metadata, sort_keys=True, separators=(",", ":"))
