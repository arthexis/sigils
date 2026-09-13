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
    """Describe how a resolved value may participate in callable resolution."""

    kind: CallableKind
    value: object
    protected: bool = False
    missing: int = 0

    @classmethod
    def classify(
        cls,
        value: object,
        *,
        bound: bool = False,
        protected: bool = False,
    ) -> CallableState:
        """Classify an ordinary value, callable, bound callable, or pending call."""
        if isinstance(value, PendingCall):
            return cls(
                CallableKind.PENDING,
                value,
                protected=protected or value.protected,
                missing=value.missing,
            )
        if bound and callable(value):
            return cls(CallableKind.BOUND, value, protected=protected)
        if callable(value):
            return cls(CallableKind.READY, value, protected=protected)
        return cls(CallableKind.VALUE, value, protected=protected)

    @property
    def callable(self) -> bool:
        """Return whether this state represents executable or pending callable work."""
        return self.kind is not CallableKind.VALUE
