from __future__ import annotations

from ..secret import Secret
from .constants import _UNRESOLVED
from .member import MemberResolution


class DirectionalBindingMixin:
    """Resolve evaluation-local ``->`` / ``<-`` intermediate bindings."""

    @property
    def _binding_scope(self):
        return getattr(self._resolution_local, "bindings", None)

    def _begin_binding_scope(self):
        bindings = self._binding_scope
        if bindings is not None:
            return bindings, False
        bindings = {}
        self._resolution_local.bindings = bindings
        return bindings, True

    def _finish_binding_scope(self, owns_scope):
        if not owns_scope:
            return
        try:
            del self._resolution_local.bindings
        except AttributeError:
            pass

    @staticmethod
    def _split_directional_binding(expression):
        """Return ``(source, target)`` for one top-level arrow, else ``None``."""
        quote = None
        escaped = False
        depth = 0
        found = None
        index = 0
        while index < len(expression):
            char = expression[index]
            if quote is not None:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == quote:
                    quote = None
                index += 1
                continue
            if char in {"'", '"'}:
                quote = char
                index += 1
                continue
            if char in "([{":
                depth += 1
                index += 1
                continue
            if char in ")]}":
                depth = max(depth - 1, 0)
                index += 1
                continue
            if depth == 0:
                operator = None
                if expression.startswith("->", index):
                    operator = "->"
                elif expression.startswith("<-", index):
                    operator = "<-"
                if operator is not None:
                    if found is not None:
                        return None
                    found = (index, operator)
                    index += 2
                    continue
            index += 1

        if found is None:
            return None
        position, operator = found
        left = expression[:position].strip()
        right = expression[position + 2 :].strip()
        if operator == "->":
            source, target = left, right
        else:
            target, source = left, right
        if not source or not target or not target.isidentifier():
            return None
        return source, target

    def _resolve_single_expression(self, expression, context):
        binding = self._split_directional_binding(expression)
        if binding is None:
            return super()._resolve_single_expression(expression, context)

        source, target = binding
        bindings, owns_scope = self._begin_binding_scope()
        try:
            value = super()._resolve_single_expression(source, context)
            if value is _UNRESOLVED:
                return _UNRESOLVED
            bindings[target] = value
            session = getattr(self, "_resolution_session", None)
            if session is not None:
                session.record(
                    "binding_created",
                    segment=0,
                    outcome="success",
                    detail=target,
                    value=value,
                    protected=isinstance(value, Secret),
                )
            return value
        finally:
            self._finish_binding_scope(owns_scope)

    def _semantic_member(
        self,
        session,
        owner,
        key,
        index,
        protected_path,
        *,
        mode,
    ):
        bindings = self._binding_scope
        if index == 0 and mode.root_lookup and bindings is not None and key in bindings:
            value = bindings[key]
            protected = isinstance(value, Secret)
            session.record(
                "binding_lookup",
                segment=index,
                outcome="success",
                detail=key,
                value=value,
                protected=protected,
            )
            return MemberResolution(value, protected)
        return super()._semantic_member(
            session,
            owner,
            key,
            index,
            protected_path,
            mode=mode,
        )
