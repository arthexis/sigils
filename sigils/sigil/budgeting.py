from __future__ import annotations

from .constants import _UNRESOLVED


class ResolutionBudgetMixin:
    """Enforce hard semantic-session budgets around production traversal."""

    @staticmethod
    def _state_budget_exhausted(state) -> bool:
        if state is None:
            return False
        return any(
            event.kind == "complexity_budget" and event.outcome == "exhausted"
            for event in state.trace
        )

    def _resolve_traversal(self, *args, **kwargs):
        """Return unresolved rather than a partial value after budget exhaustion."""
        active_session = getattr(self, "_resolution_session", None)
        value = super()._resolve_traversal(*args, **kwargs)

        if active_session is not None:
            exhausted = active_session.exhausted
        else:
            exhausted = self._state_budget_exhausted(
                getattr(self, "_last_resolution_state", None)
            )
        return _UNRESOLVED if exhausted else value
