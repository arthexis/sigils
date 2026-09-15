from __future__ import annotations

from .constants import _UNRESOLVED
from .modes import ResolutionMode
from .pending import PendingCall


class ColonDataMixin:
    """Keep colon-bearing expressions out of the legacy explicit-call grammar.

    ``:`` used to force a call and ``::`` selected a local callable.  Calls are
    now expressed by the ordinary whitespace/traversal semantics instead, so a
    colon inside an expression is treated as part of the lookup key.  The
    existing ``|:literal`` fallback marker is handled by the fallback parser
    before this hook and remains unchanged.
    """

    def _resolve_single_expression(self, expression, context):
        expression = expression.strip()
        if ":" not in expression:
            return super()._resolve_single_expression(expression, context)

        value = self._resolve_traversal(
            expression,
            context,
            mode=ResolutionMode.CALL,
        )
        if isinstance(value, PendingCall):
            return _UNRESOLVED
        return value
