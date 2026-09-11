import re

from .constants import _UNRESOLVED
from .pending import PendingCall


class ResolutionPrecedenceMixin:
    """Language-level precedence rules layered over the base resolver."""

    _space_structure_only = False

    def _required_positional_count(self, function):
        """Suppress greedy calls during the first whitespace traversal pass."""
        if self._space_structure_only:
            return 0
        return super()._required_positional_count(function)

    def _resolve_explicit_pass(self, expression, context):
        """Resolve explicit passing, consuming further values while pending."""
        parts = self._split_explicit_pass(expression)
        if not parts or any(not part for part in parts):
            return _UNRESOLVED
        value = self._resolve_single_expression(parts[0], context)
        if value is _UNRESOLVED:
            return _UNRESOLVED
        for target_expression in parts[1:]:
            if isinstance(value, PendingCall):
                argument = self._resolve_single_expression(target_expression, context)
                if argument is _UNRESOLVED or isinstance(argument, PendingCall):
                    return _UNRESOLVED
                value = self._consume_pending(value, argument)
            else:
                target = self._resolve_traversal(
                    target_expression, context, invoke_final=False
                )
                if target is _UNRESOLVED:
                    return _UNRESOLVED
                if isinstance(target, PendingCall):
                    value = self._consume_pending(target, value)
                elif callable(target):
                    value = self._run_continuation(target, value)
                else:
                    return _UNRESOLVED
            if value is _UNRESOLVED:
                return _UNRESOLVED
        return value

    def _resolve_single_expression(self, expression, context):
        """Prefer whitespace traversal, then greedy calls, then legacy calls."""
        expression = expression.strip()
        if (
            not expression
            or self._split_explicit_pass(expression)
            or ":" in expression
        ):
            return super()._resolve_single_expression(expression, context)
        if not re.search(r"\s", expression):
            return super()._resolve_single_expression(expression, context)

        self._space_structure_only = True
        try:
            traversed = self._resolve_traversal(expression, context)
        finally:
            self._space_structure_only = False
        if traversed is not _UNRESOLVED and not isinstance(traversed, PendingCall):
            return traversed

        traversed = self._resolve_traversal(expression, context)
        if traversed is not _UNRESOLVED and not isinstance(traversed, PendingCall):
            return traversed

        return self._resolve_legacy_expression(expression, context)
