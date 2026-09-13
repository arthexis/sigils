from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Iterable

MAX_STATES = 4
MAX_INTERPRETATION_EXPANSIONS = 64
MAX_SEMANTIC_STEPS = 512
MAX_NESTED_RESOLUTION_DEPTH = 16
MAX_FALLBACK_DEPTH = 8


@dataclass(frozen=True, slots=True)
class ResolutionEvent:
    """One semantic decision made while resolving a Sigil expression."""

    kind: str
    segment: int | None = None
    outcome: str | None = None
    detail: str | None = None


@dataclass(frozen=True, slots=True)
class ResolutionState:
    """A bounded candidate interpretation at one point in an expression."""

    position: int
    value: object
    callable_state: object | None = None
    protected: bool = False
    score: int = 0
    trace: tuple[ResolutionEvent, ...] = ()
    bindings_key: object | None = None

    def event(self, event: ResolutionEvent, *, score: int = 0) -> ResolutionState:
        """Return a new state with a resolution event and optional score delta."""
        return replace(self, score=self.score + score, trace=(*self.trace, event))

    def dominance_key(self) -> tuple[object, ...]:
        """Identify states that are semantically equivalent for future work."""
        return (
            self.position,
            id(self.value),
            id(self.callable_state) if self.callable_state is not None else None,
            self.protected,
            self.bindings_key,
        )


@dataclass(slots=True)
class ResolutionBudget:
    """Evaluation-scoped hard limits for semantic resolution work."""

    max_expansions: int = MAX_INTERPRETATION_EXPANSIONS
    max_steps: int = MAX_SEMANTIC_STEPS
    max_nested_depth: int = MAX_NESTED_RESOLUTION_DEPTH
    max_fallback_depth: int = MAX_FALLBACK_DEPTH
    expansions: int = 0
    steps: int = 0
    nested_depth: int = 0
    fallback_depth: int = 0
    exhausted_reason: str | None = None

    def __post_init__(self) -> None:
        if self.max_expansions < 1:
            raise ValueError("interpretation expansion budget must be positive")
        if self.max_steps < 1:
            raise ValueError("semantic step budget must be positive")
        if self.max_nested_depth < 1:
            raise ValueError("nested resolution depth budget must be positive")
        if self.max_fallback_depth < 0:
            raise ValueError("fallback depth budget cannot be negative")

    @property
    def exhausted(self) -> bool:
        return self.exhausted_reason is not None

    def _exhaust(self, reason: str) -> bool:
        if self.exhausted_reason is None:
            self.exhausted_reason = reason
        return False

    def consume_expansions(self, count: int) -> bool:
        """Consume candidate-expansion capacity without exceeding the hard limit."""
        if self.exhausted:
            return False
        if count < 0:
            raise ValueError("candidate expansion count cannot be negative")
        if self.expansions + count > self.max_expansions:
            return self._exhaust("interpretation_expansions")
        self.expansions += count
        return True

    def consume_step(self) -> bool:
        """Consume one semantic decision/event slot."""
        if self.exhausted:
            return False
        if self.steps + 1 > self.max_steps:
            return self._exhaust("semantic_steps")
        self.steps += 1
        return True

    def enter_resolution(self) -> bool:
        """Enter one nested production traversal level."""
        if self.exhausted:
            return False
        if self.nested_depth + 1 > self.max_nested_depth:
            return self._exhaust("nested_resolution_depth")
        self.nested_depth += 1
        return True

    def leave_resolution(self) -> None:
        if self.nested_depth:
            self.nested_depth -= 1

    def enter_fallback(self) -> bool:
        """Enter one compatibility fallback level."""
        if self.exhausted:
            return False
        if self.fallback_depth + 1 > self.max_fallback_depth:
            return self._exhaust("fallback_depth")
        self.fallback_depth += 1
        return True

    def leave_fallback(self) -> None:
        if self.fallback_depth:
            self.fallback_depth -= 1


class BoundedResolutionBeam:
    """Rank, merge, and cap live semantic interpretations."""

    def __init__(self, states: Iterable[ResolutionState] = (), *, limit: int = MAX_STATES):
        if limit < 1:
            raise ValueError("resolution beam limit must be positive")
        self.limit = limit
        self._states = self._normalize(states)

    @property
    def states(self) -> tuple[ResolutionState, ...]:
        return self._states

    def replace(self, states: Iterable[ResolutionState]) -> tuple[ResolutionState, ...]:
        """Replace live candidates after dominance merging and ranking."""
        self._states = self._normalize(states)
        return self._states

    def extend(self, states: Iterable[ResolutionState]) -> tuple[ResolutionState, ...]:
        """Add candidates, merge equivalent states, and keep the best four."""
        return self.replace((*self._states, *states))

    def _normalize(self, states: Iterable[ResolutionState]) -> tuple[ResolutionState, ...]:
        dominant: dict[tuple[object, ...], ResolutionState] = {}
        for state in states:
            key = state.dominance_key()
            current = dominant.get(key)
            if current is None or self._rank_key(state) > self._rank_key(current):
                dominant[key] = state
        ranked = sorted(dominant.values(), key=self._rank_key, reverse=True)
        return tuple(ranked[: self.limit])

    @staticmethod
    def _rank_key(state: ResolutionState) -> tuple[int, int]:
        # Prefer higher semantic evidence. For ties prefer the shorter path.
        return state.score, -len(state.trace)


class SegmentMemo:
    """Evaluation-scoped cache for reusable segment resolution work."""

    def __init__(self):
        self._values: dict[tuple[object, ...], object] = {}

    def get(self, key: tuple[object, ...], default=None):
        return self._values.get(key, default)

    def set(self, key: tuple[object, ...], value: object) -> object:
        self._values[key] = value
        return value

    def clear(self) -> None:
        self._values.clear()

    def __len__(self) -> int:
        return len(self._values)
