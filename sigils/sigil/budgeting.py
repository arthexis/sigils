from __future__ import annotations

from .constants import _UNRESOLVED
from .semantic import (
    MAX_INTERPRETATION_EXPANSIONS,
    MAX_SEMANTIC_STEPS,
    ResolutionBudget,
)
from .session import SemanticResolutionSession


class ResolutionBudgetMixin:
    """Enforce hard semantic-session budgets around production resolution."""

    max_interpretation_expansions = MAX_INTERPRETATION_EXPANSIONS
    max_semantic_steps = MAX_SEMANTIC_STEPS

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

    def _resolve_traversal(self, *args, **kwargs):
        """Return unresolved rather than a partial value after budget exhaustion."""
        active_session = getattr(self, "_resolution_session", None)
        value = super()._resolve_traversal(*args, **kwargs)
        return _UNRESOLVED if self._budget_exhausted(active_session) else value

    def _resolve_single_expression(self, *args, **kwargs):
        """Prevent compatibility fallbacks from escaping an exhausted budget."""
        active_session = getattr(self, "_resolution_session", None)
        value = super()._resolve_single_expression(*args, **kwargs)
        return _UNRESOLVED if self._budget_exhausted(active_session) else value
