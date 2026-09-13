from __future__ import annotations

from sigils import SafeNamespace, Sigil
from sigils.sigil.modes import CallableKind, CallableState
from sigils.sigil.pending import PendingCall


class ApprovedCall:
    __sigils_safe_callable__ = True

    def __init__(self, function):
        self.function = function

    def __call__(self, *args, **kwargs):
        return self.function(*args, **kwargs)


def test_callable_state_carries_provider_and_local_policy() -> None:
    approved = ApprovedCall(lambda value: value)

    state = CallableState.classify(
        approved,
        protected=True,
        local=True,
    )

    assert state.kind is CallableKind.READY
    assert state.ready is True
    assert state.pending is False
    assert state.provider_safe is True
    assert state.local is True
    assert state.approved is True
    assert state.function is approved


def test_protected_unapproved_ready_callable_is_not_approved() -> None:
    state = CallableState.classify(lambda value: value, protected=True)

    assert state.kind is CallableKind.READY
    assert state.provider_safe is False
    assert state.approved is False


def test_bound_callable_retains_existing_protected_invocation_policy() -> None:
    def function():
        return "ready"

    state = CallableState.classify(function, bound=True, protected=True)

    assert state.kind is CallableKind.BOUND
    assert state.ready is True
    assert state.approved is True


def test_pending_state_exposes_partial_call_metadata() -> None:
    def combine(first, second, suffix):
        return f"{first}:{second}:{suffix}"

    pending = PendingCall(
        function=combine,
        trailing_args=("omega",),
        missing=2,
        protected=True,
    )
    state = CallableState.classify(pending)

    assert state.kind is CallableKind.PENDING
    assert state.pending is True
    assert state.ready is False
    assert state.missing == 2
    assert state.protected is True
    assert state.function is combine
    assert state.trailing_args == ("omega",)


def test_explicit_pass_still_completes_pending_state() -> None:
    def combine(first, second, suffix):
        return f"{first}:{second}:{suffix}"

    context = {
        "first": "alpha",
        "second": "beta",
        "suffix": "omega",
        "combine": combine,
    }

    assert (
        Sigil("[first - combine.suffix - second]").solve(context)
        == "alpha:beta:omega"
    )


def test_explicit_pass_accepts_provider_safe_protected_callable() -> None:
    context = {
        "value": "data",
        "safe": SafeNamespace(
            {"send": ApprovedCall(lambda value: f"approved:{value}")}
        ),
    }

    assert Sigil("[value - safe.send]").solve(context) == "approved:data"


def test_local_call_records_typed_callable_state() -> None:
    metadata = Sigil("[service :: send : payload]").explain(
        {
            "service": {"send": lambda value: f"local:{value}"},
            "payload": "data",
        }
    )

    assert metadata["resolved"] is True
    assert any(
        event["kind"] == "callable_state"
        and event["outcome"] == "ready"
        and event["detail"] == "send"
        for event in metadata["trace"]
    )


def test_local_safe_namespace_still_requires_provider_approval() -> None:
    calls = []

    def unsafe(value):
        calls.append(value)
        return value

    metadata = Sigil("[safe :: send : payload]").explain(
        {
            "safe": SafeNamespace({"send": unsafe}),
            "payload": "data",
        }
    )

    assert metadata["resolved"] is False
    assert metadata["failure_reason"] == "unsafe_callable"
    assert calls == []
