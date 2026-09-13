import re

from ..namespace import SafeNamespace
from ..secret import Secret
from ..tools import tools
from .constants import _UNRESOLVED
from .member import MemberResolution, resolve_member
from .pending import PendingCall
from .session import SemanticResolutionSession


def _no_aliases(_key):
    return ()


class ResolutionPrecedenceMixin:
    """Language-level precedence rules layered over the base resolver."""

    _space_structure_only = False

    def _required_positional_count(self, function):
        """Suppress greedy calls during the first whitespace traversal pass."""
        if self._space_structure_only:
            return 0
        return super()._required_positional_count(function)

    def _begin_resolution_session(self, context):
        """Return the active evaluation session and whether this call owns it."""
        session = getattr(self, "_resolution_session", None)
        if session is not None:
            return session, False
        session = SemanticResolutionSession(context)
        self._resolution_session = session
        return session, True

    def _finish_resolution_session(self, session, owns_session):
        """Persist the completed state for later introspection and clear scope."""
        if not owns_session:
            return
        self._last_resolution_state = session.state
        self._last_resolution_memo_size = len(session.memo)
        del self._resolution_session

    def _resolve_expression(self, expression, context):
        """Scope semantic state and memoization to one expression evaluation."""
        session, owns_session = self._begin_resolution_session(context)
        try:
            return super()._resolve_expression(expression, context)
        finally:
            self._finish_resolution_session(session, owns_session)

    def _semantic_member(self, session, owner, key, index, protected_path):
        """Resolve one production traversal segment with root precedence intact."""
        raw_owner = owner.reveal() if isinstance(owner, Secret) else owner

        if isinstance(raw_owner, SafeNamespace):
            return session.resolve_member(
                owner,
                key,
                aliases=self._key_aliases,
                segment=index,
                protected_path=protected_path,
                phase="safe_namespace",
            )

        if protected_path:
            return session.resolve_member(
                owner,
                key,
                aliases=_no_aliases,
                segment=index,
                protected_path=True,
                phase="protected",
            )

        if index == 0:
            exact = session.resolve_member(
                owner,
                key,
                aliases=_no_aliases,
                segment=index,
                protected_path=False,
                allow_attributes=False,
                phase="root_exact",
            )
            if exact.resolved:
                return exact
            if key in tools:
                value = tools[key]
                session.record(
                    "root_tool_lookup",
                    segment=index,
                    outcome="success",
                    detail=key,
                    value=value,
                )
                return MemberResolution(value, False)

        return session.resolve_member(
            owner,
            key,
            aliases=self._key_aliases,
            segment=index,
            protected_path=False,
            phase="structural",
        )

    def _safe_continuation_candidate(self, session, context, key, index):
        """Probe a root continuation without invoking attributes or callables."""
        raw_context = context.reveal() if isinstance(context, Secret) else context
        if isinstance(raw_context, SafeNamespace):
            result = session.resolve_member(
                context,
                key,
                aliases=self._key_aliases,
                segment=index,
                protected_path=False,
                phase="continuation_probe",
            )
            candidate = result.value if result.resolved else _UNRESOLVED
        elif isinstance(raw_context, dict):
            result = session.resolve_member(
                context,
                key,
                aliases=self._key_aliases,
                segment=index,
                protected_path=False,
                allow_attributes=False,
                phase="continuation_probe",
            )
            candidate = result.value if result.resolved else _UNRESOLVED
        elif key in tools:
            candidate = tools[key]
            session.record(
                "root_tool_lookup",
                segment=index,
                outcome="probe",
                detail=key,
                value=candidate,
            )
        else:
            return _UNRESOLVED

        if isinstance(candidate, Secret):
            candidate = candidate.reveal()
        return candidate if callable(candidate) else _UNRESOLVED

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
        """Use the bounded beam to rank member and continuation interpretations."""
        candidates = []
        if result.resolved and result.value is not None:
            member_score = 30 if result.alias is None else 25
            candidates.append(
                (
                    "member",
                    result.value,
                    member_score,
                    result.value if callable(result.value) else None,
                    result.protected,
                )
            )
        if callable(continuation):
            candidates.append(("continuation", value, 20, continuation, protected_path))
        if not candidates:
            return None
        return session.select_candidate(candidates, segment=index)

    def _resolve_traversal(self, expression, context, *, invoke_final=True):
        """Resolve ordinary traversal through traced, bounded semantic state."""
        session, owns_session = self._begin_resolution_session(context)
        keys = [key for key in re.split(r"[.\s]+", expression.strip()) if key]
        value = context
        protected_path = False
        greedy_path = "." in expression or bool(re.search(r"\s", expression))
        index = 0
        try:
            while index < len(keys):
                key = keys[index]
                parent_protected = isinstance(value, Secret)
                result = self._semantic_member(
                    session, value, key, index, protected_path
                )
                bound_method = result.bound_method
                temp = result.value
                if parent_protected and isinstance(temp, Secret):
                    temp = temp.reveal()
                protected_path = result.protected

                continuation = _UNRESOLVED
                selected_route = None
                if index > 0 and not protected_path:
                    continuation = self._safe_continuation_candidate(
                        session, context, key, index
                    )
                    selection = self._choose_structural_route(
                        session,
                        result,
                        continuation,
                        value,
                        key=key,
                        index=index,
                        protected_path=protected_path,
                    )
                    if selection is not None:
                        selected_route = selection[0]

                if selected_route == "continuation":
                    session.record(
                        "continuation_lookup",
                        segment=index,
                        outcome="selected",
                        detail=key,
                        value=value,
                    )
                    temp = self._run_continuation(continuation, value)
                    if temp is _UNRESOLVED:
                        session.record(
                            "continuation_lookup",
                            segment=index,
                            outcome="failed",
                            detail=key,
                            value=value,
                        )
                        return _UNRESOLVED
                    bound_method = False
                elif (
                    selected_route is None
                    and (not result.resolved or temp is None)
                    and index > 0
                    and not protected_path
                ):
                    session.record(
                        "continuation_lookup",
                        segment=index,
                        outcome="attempted",
                        detail=key,
                        value=value,
                    )
                    continuation = self._resolve_traversal(
                        key, context, invoke_final=False
                    )
                    if callable(continuation):
                        temp = self._run_continuation(continuation, value)
                        if temp is _UNRESOLVED:
                            session.record(
                                "continuation_lookup",
                                segment=index,
                                outcome="failed",
                                detail=key,
                                value=value,
                            )
                            return _UNRESOLVED
                        session.record(
                            "continuation_lookup",
                            segment=index,
                            outcome="selected",
                            detail=key,
                            value=temp,
                            protected=isinstance(temp, Secret),
                        )
                        bound_method = False

                if not result.resolved and temp is _UNRESOLVED:
                    session.record(
                        "traversal_failed",
                        segment=index,
                        outcome="unresolved",
                        detail=key,
                        value=value,
                    )
                    return _UNRESOLVED
                if temp is None or temp is _UNRESOLVED:
                    session.record(
                        "traversal_failed",
                        segment=index,
                        outcome="unresolved",
                        detail=key,
                        value=value,
                    )
                    return _UNRESOLVED

                final = index == len(keys) - 1
                if (
                    greedy_path
                    and index == 0
                    and callable(temp)
                    and not final
                    and not bound_method
                ):
                    required = self._required_positional_count(temp)
                    session.record(
                        "callable_arity",
                        segment=index,
                        outcome="required" if required else "none",
                        detail=str(required or 0),
                        value=temp,
                        callable_state=temp,
                        protected=protected_path,
                    )
                    if required:
                        if protected_path and not self._provider_callable(temp):
                            session.record(
                                "safe_callable_check",
                                segment=index,
                                outcome="rejected",
                                detail=key,
                                value=temp,
                                protected=True,
                            )
                            return _UNRESOLVED
                        available = len(keys) - index - 1
                        if available < required:
                            pending = self._make_pending_call(
                                temp,
                                keys[index + 1 :],
                                required - available,
                                context,
                            )
                            session.record(
                                "pending_call",
                                segment=index,
                                outcome="created",
                                detail=str(required - available),
                                value=pending,
                                callable_state=pending,
                                protected=protected_path,
                            )
                            return pending
                        argument_end = index + 1 + required
                        temp = self._run_greedy_call(
                            temp, keys[index + 1 : argument_end], context
                        )
                        if temp is _UNRESOLVED:
                            session.record(
                                "greedy_call",
                                segment=index,
                                outcome="failed",
                                detail=key,
                                value=value,
                            )
                            return _UNRESOLVED
                        session.record(
                            "greedy_call",
                            segment=index,
                            outcome="success",
                            detail=key,
                            value=temp,
                            protected=isinstance(temp, Secret),
                        )
                        index = argument_end - 1
                        final = index == len(keys) - 1

                if bound_method:
                    try:
                        temp = temp()
                    except (TypeError, ValueError):
                        session.record(
                            "callable_invoked",
                            segment=index,
                            outcome="failed",
                            detail=key,
                            value=value,
                        )
                        return _UNRESOLVED
                    session.record(
                        "callable_invoked",
                        segment=index,
                        outcome="success",
                        detail=key,
                        value=temp,
                        protected=protected_path,
                    )
                elif callable(temp) and final:
                    if protected_path and not self._provider_callable(temp):
                        session.record(
                            "safe_callable_check",
                            segment=index,
                            outcome="rejected",
                            detail=key,
                            value=temp,
                            protected=True,
                        )
                        return _UNRESOLVED
                    if invoke_final:
                        temp = self._run_func(temp, [], value, context)
                        if temp is _UNRESOLVED:
                            session.record(
                                "callable_invoked",
                                segment=index,
                                outcome="failed",
                                detail=key,
                                value=value,
                            )
                            return _UNRESOLVED
                        if temp is None:
                            temp = key
                        session.record(
                            "callable_invoked",
                            segment=index,
                            outcome="success",
                            detail=key,
                            value=temp,
                            protected=protected_path,
                        )

                if parent_protected and not isinstance(temp, Secret):
                    temp = Secret(temp)
                value = temp
                session.record(
                    "segment_resolved",
                    segment=index,
                    outcome="success",
                    detail=key,
                    value=value,
                    protected=protected_path or isinstance(value, Secret),
                )
                index += 1

            result = value if value is not None else _UNRESOLVED
            session.record(
                "traversal_complete",
                segment=max(index - 1, 0),
                outcome="success" if result is not _UNRESOLVED else "unresolved",
                detail=expression,
                value=result,
                protected=protected_path or isinstance(result, Secret),
            )
            return result
        finally:
            self._finish_resolution_session(session, owns_session)

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
