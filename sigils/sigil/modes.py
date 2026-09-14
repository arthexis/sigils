from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .pending import PendingCall


class ResolutionMode(Enum):
    """Explicit traversal behavior used by the semantic resolver."""

    CALL = (True, True, True, True)
    TRAVERSE = (True, False, True, True)
    LOOKUP = (False, True, True, True)
    LOCAL = (False, False, False, False)

    def __init__(
        self,
        invoke_final: bool,
        greedy_calls: bool,
        continuation: bool,
        root_lookup: bool,
    ) -> None:
        self.invoke_final = invoke_final
        self.greedy_calls = greedy_calls
        self.continuation = continuation
        self.root_lookup = root_lookup


class CallableKind(Enum):
    """Semantic callable state independent of traversal syntax."""

    VALUE = "value"
    READY = "ready"
    BOUND = "bound"
    PENDING = "pending"


@dataclass(frozen=True, slots=True)
class CallableState:
    """Describe how a resolved value participates in callable resolution."""

    kind: CallableKind
    value: object
    protected: bool = False
    missing: int = 0
    provider_safe: bool = False
    local: bool = False

    @classmethod
    def classify(
        cls,
        value: object,
        *,
        bound: bool = False,
        protected: bool = False,
        local: bool = False,
    ) -> CallableState:
        """Classify values while retaining callable policy and pending metadata."""
        if isinstance(value, PendingCall):
            function = value.function
            return cls(
                CallableKind.PENDING,
                value,
                protected=protected or value.protected,
                missing=value.missing,
                provider_safe=bool(
                    getattr(function, "__sigils_safe_callable__", False)
                ),
                local=local,
            )

        provider_safe = callable(value) and bool(
            getattr(value, "__sigils_safe_callable__", False)
        )
        if bound and callable(value):
            return cls(
                CallableKind.BOUND,
                value,
                protected=protected,
                provider_safe=provider_safe,
                local=local,
            )
        if callable(value):
            return cls(
                CallableKind.READY,
                value,
                protected=protected,
                provider_safe=provider_safe,
                local=local,
            )
        return cls(
            CallableKind.VALUE,
            value,
            protected=protected,
            local=local,
        )

    @property
    def callable(self) -> bool:
        """Return whether this state represents executable or pending callable work."""
        return self.kind is not CallableKind.VALUE

    @property
    def ready(self) -> bool:
        """Return whether the callable can be invoked without another passed value."""
        return self.kind in {CallableKind.READY, CallableKind.BOUND}

    @property
    def pending(self) -> bool:
        """Return whether the callable still needs leading positional values."""
        return self.kind is CallableKind.PENDING

    @property
    def approved(self) -> bool:
        """Apply the existing protected-call policy through typed state.

        Bound methods retain their historical direct-invocation behavior. Other
        callables reached through protected data must opt in as provider-safe.
        """
        return (
            not self.protected
            or self.kind is CallableKind.BOUND
            or self.provider_safe
        )

    @property
    def function(self) -> object:
        """Return the underlying callable, including for a pending call."""
        if self.pending:
            return self.value.function
        return self.value

    @property
    def trailing_args(self) -> tuple[object, ...]:
        """Expose captured trailing arguments without unpacking PendingCall elsewhere."""
        if self.pending:
            return self.value.trailing_args
        return ()
