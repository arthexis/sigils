from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Iterable

from .member import MemberResolution, resolve_member
from .semantic import ResolutionEvent, ResolutionState, SegmentMemo

_MISSING = object()


@dataclass(slots=True)
class SemanticResolutionSession:
    """Carry one production resolution state and memo through an evaluation."""

    root: object
    memo: SegmentMemo = field(default_factory=SegmentMemo)
    state: ResolutionState = field(init=False)

    def __post_init__(self) -> None:
        self.state = ResolutionState(0, self.root)

    def record(
        self,
        kind: str,
        *,
        segment: int | None = None,
        outcome: str | None = None,
        detail: str | None = None,
        value: object | None = None,
        protected: bool | None = None,
        callable_state: object | None = None,
    ) -> ResolutionState:
        """Advance the current state while retaining the full production trace."""
        event = ResolutionEvent(kind, segment=segment, outcome=outcome, detail=detail)
        self.state = ResolutionState(
            self.state.position if segment is None else segment,
            self.state.value if value is None else value,
            callable_state=callable_state,
            protected=self.state.protected if protected is None else protected,
            score=self.state.score,
            trace=(*self.state.trace, event),
            bindings_key=self.state.bindings_key,
        )
        return self.state

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
        memo_key = (
            "member",
            phase,
            id(owner),
            key,
            protected_path,
            allow_attributes,
        )
        result = self.memo.get(memo_key, _MISSING)
        memo_outcome = "hit"
        if result is _MISSING:
            result = resolve_member(
                owner,
                key,
                aliases=aliases,
                protected_path=protected_path,
                allow_attributes=allow_attributes,
            )
            self.memo.set(memo_key, result)
            memo_outcome = "miss"

        self.record(
            "segment_memo",
            segment=segment,
            outcome=memo_outcome,
            detail=phase,
        )
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
