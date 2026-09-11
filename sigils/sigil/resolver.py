import inspect
import re

from ..namespace import SafeNamespace
from ..secret import Secret
from ..tools import tools
from .calls import CallMixin
from .constants import _UNRESOLVED


class ResolverMixin(CallMixin):
    @staticmethod
    def _key_aliases(key):
        """Return non-exact separator and reversed two-word aliases for a key."""
        aliases = []
        if "-" in key:
            separator_alias = key.replace("-", "_")
        elif "_" in key:
            separator_alias = key.replace("_", "-")
        else:
            separator_alias = None
        if separator_alias and separator_alias != key:
            aliases.append(separator_alias)

        words = key.replace("-", "_").split("_")
        if len(words) == 2 and all(words):
            for alias in (f"{words[1]}_{words[0]}", f"{words[1]}-{words[0]}"):
                if alias != key and alias not in aliases:
                    aliases.append(alias)
        return tuple(aliases)

    @staticmethod
    def _space_alias_candidates(expression):
        """Combine one whitespace-separated pair without crossing explicit dots."""
        segments = expression.strip().split(".")
        candidates = []
        for segment_index, segment in enumerate(segments):
            words = segment.split()
            if len(words) < 2:
                continue
            for word_index in range(len(words) - 1):
                left = words[word_index]
                right = words[word_index + 1]
                merged_words = [
                    *words[:word_index],
                    f"{left}-{right}",
                    *words[word_index + 2 :],
                ]
                candidate_segments = [*segments]
                candidate_segments[segment_index] = ".".join(merged_words)
                candidate = ".".join(candidate_segments)
                if candidate not in candidates:
                    candidates.append(candidate)
        return tuple(candidates)

    def _resolve_space_alias(self, expression, context, *, invoke_final=True):
        """Resolve a single unambiguous adjacent-word merge as a key alias."""
        matches = []
        for candidate in self._space_alias_candidates(expression):
            value = self._resolve_traversal(candidate, context, invoke_final=False)
            if value is not _UNRESOLVED:
                matches.append(candidate)
        if len(matches) != 1:
            return _UNRESOLVED
        return self._resolve_traversal(matches[0], context, invoke_final=invoke_final)

    @staticmethod
    def _run_continuation(function, value):
        """Pass the current resolved value into a newly resolved callable."""
        protected = isinstance(value, Secret)
        argument = value.reveal() if protected else value
        try:
            result = function(argument)
        except Exception:
            return _UNRESOLVED
        if protected and result is not None and not isinstance(result, Secret):
            return Secret(result)
        return result if result is not None else _UNRESOLVED

    @staticmethod
    def _required_positional_count(function):
        """Return the number of required positional arguments for a callable."""
        try:
            parameters = inspect.signature(function).parameters.values()
        except (TypeError, ValueError):
            return None
        positional_kinds = {
            inspect.Parameter.POSITIONAL_ONLY,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
        }
        return sum(
            parameter.kind in positional_kinds
            and parameter.default is inspect.Parameter.empty
            for parameter in parameters
        )

    def _run_greedy_call(self, function, argument_keys, context):
        """Resolve root segments as positional arguments and invoke a callable."""
        arguments = []
        protected = False
        for argument_key in argument_keys:
            argument = self._resolve_traversal(argument_key, context)
            if argument is _UNRESOLVED:
                return _UNRESOLVED
            if isinstance(argument, Secret):
                protected = True
                argument = argument.reveal()
            arguments.append(argument)
        try:
            result = function(*arguments)
        except Exception:
            return _UNRESOLVED
        if protected and result is not None and not isinstance(result, Secret):
            return Secret(result)
        return result if result is not None else _UNRESOLVED

    def _greedy_root_requires_arguments(self, expression, context):
        """Return whether a dotted expression starts with an argument-taking callable."""
        if "." not in expression:
            return False
        first = expression.split(".", 1)[0].strip()
        if not first:
            return False
        function = self._resolve_traversal(first, context, invoke_final=False)
        if function is _UNRESOLVED or not callable(function):
            return False
        return bool(self._required_positional_count(function))

    def _resolve_traversal(self, expression, context, *, invoke_final=True):
        keys = [key for key in re.split(r"[.\s]+", expression.strip()) if key]
        value = context
        protected_path = False
        greedy_path = "." in expression
        index = 0
        while index < len(keys):
            key = keys[index]
            parent_protected = isinstance(value, Secret)
            lookup_value = value.reveal() if parent_protected else value
            bound_method = False
            if isinstance(lookup_value, SafeNamespace):
                temp = _UNRESOLVED
                for candidate in (key, *self._key_aliases(key)):
                    try:
                        temp = lookup_value.resolve(candidate)
                        break
                    except KeyError:
                        continue
                if temp is _UNRESOLVED:
                    return _UNRESOLVED
                protected_path = True
            elif protected_path:
                if isinstance(lookup_value, dict) and key in lookup_value:
                    temp = lookup_value.get(key)
                elif isinstance(lookup_value, list) and key.lstrip("+-").isdigit():
                    try:
                        temp = lookup_value[int(key)]
                    except IndexError:
                        return _UNRESOLVED
                else:
                    temp = None
            elif isinstance(lookup_value, dict) and key in lookup_value:
                temp = lookup_value.get(key)
            elif isinstance(lookup_value, list) and key.lstrip("+-").isdigit():
                try:
                    temp = lookup_value[int(key)]
                except IndexError:
                    return _UNRESOLVED
            elif index == 0 and key in tools:
                temp = tools[key]
            else:
                temp = None
            if temp is None and isinstance(lookup_value, dict):
                for alias in self._key_aliases(key):
                    if alias in lookup_value:
                        temp = lookup_value.get(alias)
                        break
            if temp is None and lookup_value is not None and not protected_path:
                for candidate in (key, *self._key_aliases(key)):
                    if hasattr(lookup_value, candidate):
                        temp = getattr(lookup_value, candidate)
                        bound_method = callable(temp)
                        break
            if temp is None and index > 0 and not protected_path:
                continuation = self._resolve_traversal(key, context, invoke_final=False)
                if callable(continuation):
                    temp = self._run_continuation(continuation, value)
                    if temp is _UNRESOLVED:
                        return _UNRESOLVED
            if temp is None or temp is _UNRESOLVED:
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
                if required:
                    argument_end = index + 1 + required
                    if argument_end > len(keys):
                        return _UNRESOLVED
                    temp = self._run_greedy_call(
                        temp, keys[index + 1 : argument_end], context
                    )
                    if temp is _UNRESOLVED:
                        return _UNRESOLVED
                    index = argument_end - 1
                    final = index == len(keys) - 1

            if bound_method:
                try:
                    temp = temp()
                except (TypeError, ValueError):
                    return _UNRESOLVED
            elif callable(temp) and final:
                if protected_path and not self._provider_callable(temp):
                    return _UNRESOLVED
                if invoke_final:
                    temp = self._run_func(temp, [], value, context)
                    if temp is _UNRESOLVED:
                        return _UNRESOLVED
                    if temp is None:
                        temp = key
            if parent_protected and not isinstance(temp, Secret):
                temp = Secret(temp)
            value = temp
            index += 1
        return value if value is not None else _UNRESOLVED

    def _resolve_legacy_expression(self, expression, context):
        keys = expression.split(".")
        value = context
        func_args = []
        protected_path = False
        for key in keys:
            if " " in key:
                key_parts = key.split()
                key = key_parts[0]
                func_args = key_parts[1:]
            parent_protected = isinstance(value, Secret)
            lookup_value = value.reveal() if parent_protected else value
            if isinstance(lookup_value, SafeNamespace):
                if func_args:
                    return _UNRESOLVED
                temp = _UNRESOLVED
                for candidate in (key, *self._key_aliases(key)):
                    try:
                        temp = lookup_value.resolve(candidate)
                        break
                    except KeyError:
                        continue
                if temp is _UNRESOLVED:
                    return _UNRESOLVED
                protected_path = True
            elif protected_path:
                if func_args:
                    return _UNRESOLVED
                if isinstance(lookup_value, dict) and key in lookup_value:
                    temp = lookup_value.get(key)
                elif isinstance(lookup_value, list) and key.lstrip("+-").isdigit():
                    try:
                        temp = lookup_value[int(key)]
                    except IndexError:
                        return _UNRESOLVED
                else:
                    temp = None
            elif isinstance(lookup_value, dict) and key in lookup_value:
                temp = lookup_value.get(key)
                if isinstance(temp, SafeNamespace) and func_args:
                    return _UNRESOLVED
                if callable(temp):
                    temp = self._run_func(temp, func_args, value, context)
                    if temp is None:
                        temp = key
            elif isinstance(lookup_value, list) and key.lstrip("+-").isdigit():
                try:
                    temp = lookup_value[int(key)]
                except IndexError:
                    return _UNRESOLVED
            elif key in tools:
                tool_func = tools[key]
                if callable(tool_func):
                    temp = self._run_func(tool_func, func_args, value, context)
                    if temp is None:
                        temp = key
                else:
                    temp = tool_func
            else:
                temp = None
            if temp is None and isinstance(lookup_value, dict):
                for alias in self._key_aliases(key):
                    if alias not in lookup_value:
                        continue
                    temp = lookup_value.get(alias)
                    if isinstance(temp, SafeNamespace) and func_args:
                        return _UNRESOLVED
                    if callable(temp):
                        temp = self._run_func(temp, func_args, value, context)
                        if temp is None:
                            temp = key
                    break
            if protected_path and callable(temp) and not self._provider_callable(temp):
                return _UNRESOLVED
            if temp is _UNRESOLVED:
                return _UNRESOLVED
            if temp and callable(temp):
                if self._provider_callable(temp):
                    temp = self._run_func(temp, [], value, context)
                    if temp is _UNRESOLVED:
                        return _UNRESOLVED
                else:
                    temp = temp()
            if temp is None and lookup_value is not None and not protected_path:
                for candidate in (key, *self._key_aliases(key)):
                    if hasattr(lookup_value, candidate):
                        temp = getattr(lookup_value, candidate)
                        break
            if temp is None:
                return _UNRESOLVED
            if parent_protected and not isinstance(temp, Secret):
                temp = Secret(temp)
            value = temp
        return value if value is not None else _UNRESOLVED

    @staticmethod
    def _fallback_truthy(value):
        if value is _UNRESOLVED:
            return False
        raw_value = value.reveal() if isinstance(value, Secret) else value
        return bool(raw_value)

    @staticmethod
    def _strict_fallback_missing(value):
        if value is _UNRESOLVED:
            return True
        raw_value = value.reveal() if isinstance(value, Secret) else value
        return raw_value is None or (
            isinstance(raw_value, (set, frozenset)) and not raw_value
        )

    def _resolve_single_expression(self, expression, context):
        expression = expression.strip()
        if not expression:
            return _UNRESOLVED
        if expression.endswith(":"):
            return expression[:-1].strip()
        if ":" in expression:
            parts = expression.split(":")
            target = parts[0].strip()
            function = self._resolve_traversal(target, context, invoke_final=False)
            if function is _UNRESOLVED and re.search(r"\s", target):
                function = self._resolve_space_alias(
                    target, context, invoke_final=False
                )
            if function is _UNRESOLVED or not callable(function):
                return _UNRESOLVED
            return self._run_structured_call(function, parts[1:], context)
        traversed = self._resolve_traversal(expression, context)
        if traversed is not _UNRESOLVED:
            return traversed
        if self._greedy_root_requires_arguments(expression, context):
            return _UNRESOLVED
        if re.search(r"\s", expression):
            legacy = self._resolve_legacy_expression(expression, context)
            if legacy is not _UNRESOLVED:
                return legacy
            return self._resolve_space_alias(expression, context)
        return self._resolve_legacy_expression(expression, context)

    @staticmethod
    def _split_fallback_expression(expression):
        parts = re.split(r"(\|\|?)", expression)
        branches = [parts[0]]
        operators = []
        for index in range(1, len(parts), 2):
            operators.append(parts[index])
            branches.append(parts[index + 1])
        return branches, operators

    def _resolve_expression(self, expression, context):
        if "|" not in expression:
            return self._resolve_single_expression(expression, context)
        branches, operators = self._split_fallback_expression(expression)
        value = self._resolve_single_expression(branches[0], context)
        for operator, branch in zip(operators, branches[1:], strict=True):
            should_fallback = (
                not self._fallback_truthy(value)
                if operator == "|"
                else self._strict_fallback_missing(value)
            )
            if not should_fallback:
                return value
            branch = branch.strip()
            if branch.startswith(":"):
                return branch[1:]
            value = self._resolve_single_expression(branch, context)
        return value
