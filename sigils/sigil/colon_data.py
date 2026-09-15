from __future__ import annotations

from .constants import _UNRESOLVED
from .modes import ResolutionMode
from .pending import PendingCall


class ColonDataMixin:
    """Keep colon-bearing expressions out of the legacy explicit-call grammar.

    ``:`` used to force a call and ``::`` selected a local callable. Calls are
    now expressed by ordinary whitespace/traversal semantics, so a colon inside
    an expression is treated as data. The existing ``|:literal`` fallback marker
    is handled by the fallback parser and remains unchanged.
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
