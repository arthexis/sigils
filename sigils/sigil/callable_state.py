from __future__ import annotations

import inspect
import re
from dataclasses import dataclass

from ..secret import Secret
from .constants import _UNRESOLVED
from .modes import CallableState, ResolutionMode


@dataclass(frozen=True, slots=True)
class CallableArity:
    """Typed arity evidence used by greedy and pending callable resolution."""

    required: int | None

    @property
    def known(self) -> bool:
        return self.required is not None

    @property
    def needs_arguments(self) -> bool:
        return bool(self.required)


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

    def _callable_arity(self, value) -> CallableArity:
        """Return required positional arity from the typed callable representation."""
        state = value if isinstance(value, CallableState) else self._callable_state(value)
        if not state.ready:
            return CallableArity(None)
        try:
            parameters = inspect.signature(state.function).parameters.values()
        except (TypeError, ValueError):
            return CallableArity(None)
        positional_kinds = {
            inspect.Parameter.POSITIONAL_ONLY,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
        }
        required = sum(
            parameter.kind in positional_kinds
            and parameter.default is inspect.Parameter.empty
            for parameter in parameters
        )
        return CallableArity(required)

    def _required_positional_count(self, function):
        """Preserve the resolver API while sourcing arity from typed evidence."""
        return self._callable_arity(function).required

    def _continuation_state(self, value, *, protected: bool = False) -> CallableState:
        """Classify continuation viability through the shared callable model."""
        return self._callable_state(value, protected=protected)

    def _safe_continuation_candidate(self, session, context, key, index):
        """Keep semantic continuation probes inside CallableState policy."""
        candidate = super()._safe_continuation_candidate(session, context, key, index)
        if candidate is _UNRESOLVED:
            return _UNRESOLVED
        state = self._continuation_state(candidate)
        session.record(
            "callable_state",
            segment=index,
            outcome=state.kind.value,
            detail=key,
            value=candidate,
            callable_state=state if state.callable else None,
            protected=state.protected,
        )
        return state.value if state.ready and state.approved else _UNRESOLVED

    def _choose_structural_route(
        self,
        session,
        result,
        continuation,
        value,
        *,
        key,
        index,
        protected_path,
    ):
        """Let typed callable state decide whether continuation is a viable route."""
        if continuation is not _UNRESOLVED:
            state = self._continuation_state(
                continuation,
                protected=protected_path,
            )
            if not state.ready or not state.approved:
                continuation = _UNRESOLVED
        return super()._choose_structural_route(
            session,
            result,
            continuation,
            value,
            key=key,
            index=index,
            protected_path=protected_path,
        )

    def _run_continuation(self, function, value):
        """Invoke continuations only after typed callable-state validation."""
        state = self._continuation_state(
            function,
            protected=isinstance(value, Secret),
        )
        if not state.ready or not state.approved:
            return _UNRESOLVED
        return super()._run_continuation(state.value, value)

    def _record_callable_transition(
        self,
        previous: CallableState,
        current: CallableState,
        *,
        detail: str,
    ) -> None:
        session = getattr(self, "_resolution_session", None)
        if session is None:
            return
        remaining = current.missing if current.pending else 0
        session.record(
            "callable_transition",
            segment=0,
            outcome=current.kind.value,
            detail=f"{detail}:{previous.missing}->{remaining}",
            value=current.value,
            callable_state=current if current.callable else None,
            protected=current.protected,
        )

    def _consume_pending_state(
        self,
        state: CallableState,
        value,
        *,
        detail: str = "pending",
    ) -> tuple[object, CallableState]:
        """Consume one leading value and return both value and updated callable state."""
        if not state.pending:
            unresolved_state = self._callable_state(_UNRESOLVED)
            return _UNRESOLVED, unresolved_state

        protected = isinstance(value, Secret)
        argument = value.reveal() if protected else value
        try:
            result = state.value.consume(argument, protected=protected)
        except Exception:
            unresolved_state = self._callable_state(_UNRESOLVED)
            self._record_callable_transition(
                state,
                unresolved_state,
                detail=f"{detail}:failed",
            )
            return _UNRESOLVED, unresolved_state

        result_state = self._callable_state(result, local=state.local)
        if result_state.pending:
            self._record_callable_transition(state, result_state, detail=detail)
            return result, result_state

        result_value, protected_result = result
        if result_value is None:
            unresolved_state = self._callable_state(_UNRESOLVED)
            self._record_callable_transition(
                state,
                unresolved_state,
                detail=f"{detail}:empty",
            )
            return _UNRESOLVED, unresolved_state
        if protected_result and not isinstance(result_value, Secret):
            result_value = Secret(result_value)
        next_state = self._callable_state(
            result_value,
            protected=protected_result,
            local=state.local,
        )
        self._record_callable_transition(state, next_state, detail=detail)
        return result_value, next_state

    def _consume_pending(self, pending, value):
        """Preserve the resolver API while returning through a typed transition."""
        result, _state = self._consume_pending_state(
            self._callable_state(pending),
            value,
        )
        return result

    def _resolve_explicit_pass(self, expression, context):
        """Resolve explicit passing using CallableState for every callable branch."""
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
            elif ":" in target_expression and "::" not in target_expression:
                target_parts = target_expression.split(":")
                target_name = target_parts[0].strip()
                argument_sets = target_parts[1:]
                if not target_name:
                    return _UNRESOLVED
                target = self._resolve_traversal(
                    target_name,
                    context,
                    mode=ResolutionMode.LOOKUP,
                )
                target_state = self._callable_state(target)
                if not target_state.ready or not target_state.approved:
                    return _UNRESOLVED
                value = self._run_structured_call(
                    target_state.value,
                    argument_sets,
                    context,
                    incoming=value,
                )
                value_state = self._callable_state(value)
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
                    value, value_state = self._consume_pending_state(
                        target_state,
                        value,
                        detail=target_expression,
                    )
                elif target_state.ready:
                    value = self._run_continuation(target_state.value, value)
                    value_state = self._callable_state(value)
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
