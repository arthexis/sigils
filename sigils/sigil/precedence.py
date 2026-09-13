import re

from ..secret import Secret
from .constants import _UNRESOLVED
from .member import resolve_member
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

    def _resolve_local_member(self, value, expression):
        """Resolve a member path only from ``value``, never from root context."""
        keys = [key for key in re.split(r"[.\s]+", expression.strip()) if key]
        if not keys:
            return _UNRESOLVED, False

        protected_path = False
        for key in keys:
            result = resolve_member(
                value,
                key,
                aliases=self._key_aliases,
                protected_path=protected_path,
            )
            if not result.resolved:
                return _UNRESOLVED, protected_path
            value = result.value
            protected_path = result.protected

        return value, protected_path

    def _resolve_local_owner(self, expression, context):
        """Resolve a local-call owner without continuation or implicit invocation."""
        keys = [key for key in re.split(r"[.\s]+", expression.strip()) if key]
        if not keys:
            return _UNRESOLVED

        owner = self._resolve_traversal(keys[0], context, invoke_final=False)
        if owner is _UNRESOLVED or isinstance(owner, PendingCall):
            return _UNRESOLVED
        if len(keys) == 1:
            return owner

        owner, _ = self._resolve_local_member(owner, ".".join(keys[1:]))
        return owner

    def _resolve_local_call(self, expression, context):
        """Invoke a callable extracted strictly from the value left of ``::``."""
        if expression.count("::") != 1:
            return _UNRESOLVED

        left_expression, local_expression = expression.split("::", 1)
        left_expression = left_expression.strip()
        if not left_expression or not local_expression.strip():
            return _UNRESOLVED

        local_parts = local_expression.split(":")
        member_expression = local_parts[0].strip()
        argument_sets = local_parts[1:]
        if not member_expression:
            return _UNRESOLVED

        owner = self._resolve_local_owner(left_expression, context)
        if owner is _UNRESOLVED:
            return _UNRESOLVED

        function, protected_path = self._resolve_local_member(owner, member_expression)
        if isinstance(function, Secret):
            protected_path = True
            function = function.reveal()
        if function is _UNRESOLVED or not callable(function):
            return _UNRESOLVED
        if protected_path and not self._provider_callable(function):
            return _UNRESOLVED

        result = self._run_structured_call(function, argument_sets, context)
        if result is _UNRESOLVED:
            return _UNRESOLVED
        if protected_path and result is not None and not isinstance(result, Secret):
            return Secret(result)
        return result

    def _resolve_single_expression(self, expression, context):
        """Apply explicit operators before whitespace traversal precedence."""
        expression = expression.strip()
        if "::" in expression:
            return self._resolve_local_call(expression, context)
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
