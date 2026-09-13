from __future__ import annotations

from .constants import _UNRESOLVED
from .semantic import (
    MAX_FALLBACK_DEPTH,
    MAX_INTERPRETATION_EXPANSIONS,
    MAX_NESTED_RESOLUTION_DEPTH,
    MAX_SEMANTIC_STEPS,
    ResolutionBudget,
)
from .session import SemanticResolutionSession


class ResolutionBudgetMixin:
    """Enforce hard semantic-session budgets around production resolution."""

    max_interpretation_expansions = MAX_INTERPRETATION_EXPANSIONS
    max_semantic_steps = MAX_SEMANTIC_STEPS
    max_nested_resolution_depth = MAX_NESTED_RESOLUTION_DEPTH
    max_fallback_depth = MAX_FALLBACK_DEPTH

    def _begin_resolution_session(self, context):
        """Create an evaluation-scoped session with this Sigil's hard limits."""
        session = getattr(self, "_resolution_session", None)
        if session is not None:
            return session, False
        session = SemanticResolutionSession(
            context,
            budget=ResolutionBudget(
                max_expansions=self.max_interpretation_expansions,
                max_steps=self.max_semantic_steps,
                max_nested_depth=self.max_nested_resolution_depth,
                max_fallback_depth=self.max_fallback_depth,
            ),
        )
        self._resolution_session = session
        return session, True

    @staticmethod
    def _state_budget_exhausted(state) -> bool:
        if state is None:
            return False
        return any(
            event.kind == "complexity_budget" and event.outcome == "exhausted"
            for event in state.trace
        )

    def _budget_exhausted(self, session=None) -> bool:
        if session is not None:
            return session.exhausted
        return self._state_budget_exhausted(getattr(self, "_last_resolution_state", None))

    def _resolve_single_expression(self, expression, context):
        """Keep all interpretation attempts inside one evaluation-scoped budget."""
        session, owns_session = self._begin_resolution_session(context)
        try:
            value = super()._resolve_single_expression(expression, context)
            return _UNRESOLVED if session.exhausted else value
        finally:
            self._finish_resolution_session(session, owns_session)

    def _resolve_traversal(self, expression, context, **kwargs):
        """Bound recursive traversal depth, including continuation lookup recursion."""
        session, owns_session = self._begin_resolution_session(context)
        entered = session.budget.enter_resolution()
        if not entered:
            session._record_budget_exhaustion()
            self._finish_resolution_session(session, owns_session)
            return _UNRESOLVED
        try:
            value = super()._resolve_traversal(expression, context, **kwargs)
            return _UNRESOLVED if session.exhausted else value
        finally:
            session.budget.leave_resolution()
            self._finish_resolution_session(session, owns_session)

    def _resolve_legacy_expression(self, expression, context):
        """Bound compatibility fallback nesting within the active evaluation."""
        session, owns_session = self._begin_resolution_session(context)
        entered = session.budget.enter_fallback()
        if not entered:
            session._record_budget_exhaustion()
            self._finish_resolution_session(session, owns_session)
            return _UNRESOLVED
        try:
            value = super()._resolve_legacy_expression(expression, context)
            return _UNRESOLVED if session.exhausted else value
        finally:
            session.budget.leave_fallback()
            self._finish_resolution_session(session, owns_session)
