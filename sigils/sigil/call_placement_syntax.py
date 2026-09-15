from __future__ import annotations

from .constants import _UNRESOLVED
from .modes import ResolutionMode


class ColonlessCallPlacementMixin:
    """Route explicit-pass call arguments without using ``:`` delimiters.

    The right side of an explicit pass first keeps its ordinary traversal
    meaning. If that does not resolve to a callable, the longest callable
    prefix is treated as the target and the remaining whitespace-delimited
    words are structured call arguments. This preserves nested command paths
    while allowing forms such as ``values - collect [2] [*] [1]``.
    """

    def _structured_pass_target(self, expression, context):
        words = expression.split()
        if len(words) < 2:
            return None

        for boundary in range(len(words) - 1, 0, -1):
            target_expression = " ".join(words[:boundary])
            target = self._resolve_traversal(
                target_expression,
                context,
                mode=ResolutionMode.LOOKUP,
            )
            target_state = self._callable_state(target)
            if target_state.ready and target_state.approved:
                return target_state, words[boundary:]
        return None

    def _resolve_explicit_pass(self, expression, context):
        """Resolve explicit passing with whitespace-delimited call arguments."""
        parts = self._split_explicit_pass(expression)
        if not parts or any(not part for part in parts):
            return _UNRESOLVED

        value = self._resolve_single_expression(parts[0], context)
        if value is _UNRESOLVED:
            return _UNRESOLVED
        value_state = self._callable_state(value)

        for target_expression in parts[1:]:
            if value_state.pending:
                argument = self._resolve_single_expression(target_expression, context)
                argument_state = self._callable_state(argument)
                if argument is _UNRESOLVED or argument_state.pending:
                    return _UNRESOLVED
                value, value_state = self._consume_pending_state(
                    value_state,
                    argument,
                    detail=target_expression,
                )
            else:
                target = self._resolve_traversal(
                    target_expression,
                    context,
                    mode=ResolutionMode.LOOKUP,
                )
                target_state = self._callable_state(target)

                if target_state.pending:
                    value, value_state = self._consume_pending_state(
                        target_state,
                        value,
                        detail=target_expression,
                    )
                elif target_state.ready and target_state.approved:
                    value = self._run_continuation(target_state.value, value)
                    value_state = self._callable_state(value)
                else:
                    structured = self._structured_pass_target(target_expression, context)
                    if structured is None:
                        return _UNRESOLVED
                    structured_state, argument_sets = structured
                    value = self._run_structured_call(
                        structured_state.value,
                        argument_sets,
                        context,
                        incoming=value,
                    )
                    value_state = self._callable_state(value)

            if value is _UNRESOLVED:
                return _UNRESOLVED

        return value
