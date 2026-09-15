from __future__ import annotations

from .constants import _UNRESOLVED
from .modes import ResolutionMode
from .pending import PendingCall


class ColonDataMixin:
    """Treat colon-bearing expressions as opaque lookup data.

    ``:``, ``::``, ``:=``, trailing colons, and colon-prefixed fallback branches
    have no grammatical meaning. Calls use ordinary whitespace/traversal
    semantics instead.
    """

    def _resolve_single_expression(self, expression, context):
        expression = expression.strip()
        if self._split_explicit_pass(expression):
            return super()._resolve_single_expression(expression, context)
        if ":" not in expression:
            return super()._resolve_single_expression(expression, context)

        value = self._resolve_traversal(
            expression,
            context,
            mode=ResolutionMode.LOOKUP,
        )
        if isinstance(value, PendingCall):
            return _UNRESOLVED
        return value
