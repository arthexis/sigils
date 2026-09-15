from __future__ import annotations

from .constants import _UNRESOLVED


def split_top_level_sequence(expression: str) -> tuple[str, ...] | None:
    """Split top-level comma items without crossing quotes or nested groups."""
    parts = []
    start = 0
    depth = 0
    quote = None
    escaped = False

    for index, character in enumerate(expression):
        if escaped:
            escaped = False
            continue
        if character == "\\" and quote is not None:
            escaped = True
            continue
        if quote is not None:
            if character == quote:
                quote = None
            continue
        if character in {"'", '"'}:
            quote = character
            continue
        if character in "([{":
            depth += 1
            continue
        if character in ")]}":
            depth = max(0, depth - 1)
            continue
        if character == "," and depth == 0:
            parts.append(expression[start:index].strip())
            start = index + 1

    if not parts:
        return None
    parts.append(expression[start:].strip())
    if any(not part for part in parts):
        return None
    return tuple(parts)


class SequenceMixin:
    """Resolve comma-separated expressions as tuples below explicit operators."""

    def _resolve_single_expression(self, expression, context):
        expression = expression.strip()
        if self._split_explicit_pass(expression):
            return super()._resolve_single_expression(expression, context)

        sequence = split_top_level_sequence(expression)
        if sequence is None:
            return super()._resolve_single_expression(expression, context)

        values = []
        for item in sequence:
            value = self._resolve_expression(item, context)
            if value is _UNRESOLVED:
                return _UNRESOLVED
            values.append(value)
        return tuple(values)
