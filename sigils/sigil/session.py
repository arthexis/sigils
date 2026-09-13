from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Callable, Iterable

from .constants import _UNRESOLVED
from .member import MemberResolution, resolve_member
from .semantic import (
    BoundedResolutionBeam,
    ResolutionBudget,
    ResolutionEvent,
    ResolutionState,
    SegmentMemo,
)

_MISSING = object()
_KEEP = object()


@dataclass(slots=True)
class SemanticResolutionSession:
    """Carry production resolution state, memo, and bounded candidates."""

    root: object
    memo: SegmentMemo = field(default_factory=SegmentMemo)
    budget: ResolutionBudget = field(default_factory=ResolutionBudget)
    state: ResolutionState = field(init=False)
    _budget_event_recorded: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        self.state = ResolutionState(0, self.root)

    @property
    def exhausted(self) -> bool:
        return self.budget.exhausted

    def _record_budget_exhaustion(self, *, segment: int | None = None) -> None:
        """Emit exactly one structured exhaustion event outside the step budget."""
        if self._budget_event_recorded or not self.budget.exhausted:
            return
        self.state = self.state.event(
            ResolutionEvent(
                "complexity_budget",
                segment=segment,
                outcome="exhausted",
                detail=self.budget.exhausted_reason,
            )
        )
        self._budget_event_recorded = True

    def record(
        self,
        kind: str,
        *,
        segment: int | None = None,
        outcome: str | None = None,
        detail: str | None = None,
        value: object = _KEEP,
        protected: bool | None = None,
        callable_state: object | None = None,
    ) -> ResolutionState:
        """Advance the current state while retaining the full production trace."""
        if not self.budget.consume_step():
            self._record_budget_exhaustion(segment=segment)
            return self.state
        event = ResolutionEvent(kind, segment=segment, outcome=outcome, detail=detail)
        self.state = ResolutionState(
            self.state.position if segment is None else segment,
            self.state.value if value is _KEEP else value,
            callable_state=callable_state,
            protected=self.state.protected if protected is None else protected,
            score=self.state.score,
            trace=(*self.state.trace, event),
            bindings_key=self.state.bindings_key,
        )
        return self.state

    def select_candidate(
        self,
        candidates: Iterable[tuple[str, object, int, object | None, bool]],
        *,
        segment: int,
    ) -> tuple[str, ResolutionState] | None:
        """Rank semantic candidates, keep at most four, and select the strongest."""
        candidates = tuple(candidates)
        if not candidates:
            return None
        if not self.budget.consume_expansions(len(candidates)):
            self._record_budget_exhaustion(segment=segment)
            return None

        base = self.state
        for label, _value, _score, _callable_state, _protected in candidates:
            base = base.event(
                ResolutionEvent(
                    "candidate_created",
                    segment=segment,
                    outcome="viable",
                    detail=label,
                )
            )

        states = []
        labels: dict[int, str] = {}
        for label, value, score, callable_state, protected in candidates:
            candidate = replace(
                base,
                position=segment,
                value=value,
                callable_state=callable_state,
                protected=protected,
                score=base.score + score,
            )
            states.append(candidate)
            labels[id(candidate)] = label

        beam = BoundedResolutionBeam(states)
        kept_ids = {id(state) for state in beam.states}
        selected = beam.states[0]
        selected_label = labels[id(selected)]
        self.state = selected

        for candidate in states:
            label = labels[id(candidate)]
            if id(candidate) == id(selected):
                continue
            outcome = "beam_dropped" if id(candidate) not in kept_ids else "not_selected"
            self.state = self.state.event(
                ResolutionEvent(
                    "candidate_pruned",
                    segment=segment,
                    outcome=outcome,
                    detail=label,
                )
            )

        self.state = self.state.event(
            ResolutionEvent(
                "candidate_selected",
                segment=segment,
                outcome="selected",
                detail=selected_label,
            )
        )
        return selected_label, self.state

    def resolve_member(
        self,
        owner: object,
        key: str,
        *,
        aliases: Callable[[str], Iterable[str]],
        segment: int,
        protected_path: bool = False,
        allow_attributes: bool = True,
        phase: str = "structural",
    ) -> MemberResolution:
        """Resolve and memoize one structural segment within this evaluation."""
        if self.exhausted:
            self._record_budget_exhaustion(segment=segment)
            return MemberResolution(_UNRESOLVED, protected_path)

        memo_key = (
            "member",
            phase,
            id(owner),
            key,
            protected_path,
            allow_attributes,
        )
        entry = self.memo.get(memo_key, _MISSING)
        memo_outcome = "hit"
        if entry is _MISSING or entry[0] is not owner:
            result = resolve_member(
                owner,
                key,
                aliases=aliases,
                protected_path=protected_path,
                allow_attributes=allow_attributes,
            )
            self.memo.set(memo_key, (owner, result))
            memo_outcome = "miss" if entry is _MISSING else "collision"
        else:
            result = entry[1]

        self.record(
            "segment_memo",
            segment=segment,
            outcome=memo_outcome,
            detail=phase,
        )
        if self.exhausted:
            return MemberResolution(_UNRESOLVED, protected_path)

        detail = result.alias or key
        self.record(
            "member_lookup",
            segment=segment,
            outcome="success" if result.resolved else "missing",
            detail=detail,
            value=result.value if result.resolved else owner,
            protected=result.protected,
        )
        if result.alias is not None:
            self.record(
                "alias_selected",
                segment=segment,
                outcome="success",
                detail=result.alias,
            )
        return result
