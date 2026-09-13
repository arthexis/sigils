from __future__ import annotations

import re

from ..secret import Secret
from .constants import _UNRESOLVED
from .modes import CallableState, ResolutionMode


class CallableStateMixin:
    """Centralize callable classification and policy for production resolution."""

    @staticmethod
    def _callable_state(
        value,
        *,
        bound: bool = False,
        protected: bool = False,
        local: bool = False,
    ) -> CallableState:
        return CallableState.classify(
            value,
            bound=bound,
            protected=protected,
            local=local,
        )

    @staticmethod
    def _provider_callable(value):
        """Preserve the provider-safe hook through the typed callable model."""
        return CallableState.classify(value).provider_safe

    def _resolve_explicit_pass(self, expression, context):
        """Resolve explicit passing using CallableState for every callable branch."""
        parts = self._split_explicit_pass(expression)
        if not parts or any(not part for part in parts):
            return _UNRESOLVED

        value = self._resolve_single_expression(parts[0], context)
        if value is _UNRESOLVED:
            return _UNRESOLVED

        for target_expression in parts[1:]:
            value_state = self._callable_state(value)
            if value_state.pending:
                argument = self._resolve_single_expression(target_expression, context)
                argument_state = self._callable_state(argument)
                if argument is _UNRESOLVED or argument_state.pending:
                    return _UNRESOLVED
                value = self._consume_pending(value_state.value, argument)
            else:
                target = self._resolve_traversal(
                    target_expression,
                    context,
                    mode=ResolutionMode.LOOKUP,
                )
                if target is _UNRESOLVED:
                    return _UNRESOLVED

                target_state = self._callable_state(target)
                if target_state.pending:
                    value = self._consume_pending(target_state.value, value)
                elif target_state.ready:
                    value = self._run_continuation(target_state.value, value)
                else:
                    return _UNRESOLVED

            if value is _UNRESOLVED:
                return _UNRESOLVED

        return value

    def _resolve_local_owner(self, expression, context):
        """Resolve a local-call owner while rejecting pending callable state."""
        keys = [key for key in re.split(r"[.\s]+", expression.strip()) if key]
        if not keys:
            return _UNRESOLVED

        owner = self._resolve_traversal(
            keys[0],
            context,
            mode=ResolutionMode.LOOKUP,
        )
        if owner is _UNRESOLVED or self._callable_state(owner).pending:
            return _UNRESOLVED
        if len(keys) == 1:
            return owner

        owner, _ = self._resolve_local_member(owner, ".".join(keys[1:]))
        return owner

    def _resolve_local_call(self, expression, context):
        """Invoke a strict local callable through the unified callable state."""
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

        callable_state = self._callable_state(
            function,
            protected=protected_path,
            local=True,
        )
        session = getattr(self, "_resolution_session", None)
        if session is not None:
            session.record(
                "callable_state",
                segment=0,
                outcome=callable_state.kind.value,
                detail=member_expression,
                value=function,
                callable_state=callable_state if callable_state.callable else None,
                protected=protected_path,
            )

        if function is _UNRESOLVED or not callable_state.ready:
            return _UNRESOLVED
        if not callable_state.approved:
            if session is not None:
                session.record(
                    "safe_callable_check",
                    segment=0,
                    outcome="rejected",
                    detail=member_expression,
                    value=function,
                    protected=True,
                    callable_state=callable_state,
                )
            return _UNRESOLVED

        result = self._run_structured_call(
            callable_state.value,
            argument_sets,
            context,
        )
        if result is _UNRESOLVED:
            return _UNRESOLVED
        if protected_path and result is not None and not isinstance(result, Secret):
            return Secret(result)
        return result
