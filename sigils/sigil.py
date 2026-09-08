import inspect
import re
import threading

from .context import Context
from .namespace import SafeNamespace
from .secret import Secret
from .tools import tools


_UNRESOLVED = object()


class Sigil:
    """Parse and resolve lazy and eager sigil templates."""

    cache = threading.local()
    max_depth = 6
    debug = False

    def __init__(self, template, *, max_depth=None, debug=None):
        self._captured_secrets = {}
        self._template = str(template)
        self.max_depth = (
            max_depth if max_depth is not None else self.__class__.max_depth
        )
        self.debug = debug if debug is not None else self.__class__.debug
        self.pattern = re.compile(r"(?P<eager>%)?\[(?P<expression>.*?)\]")
        self._template = self._render_template(
            self._template,
            self._ambient_context(),
            eager_only=True,
        )

    @property
    def template(self):
        return self._replace_captured(self._template, reveal=False)

    @staticmethod
    def _ambient_context():
        frame = inspect.currentframe()
        try:
            caller = frame.f_back if frame is not None else None
            while caller is not None:
                module_name = caller.f_globals.get("__name__", "")
                if not module_name.startswith("sigils."):
                    break
                caller = caller.f_back
            ambient = {}
            active_context = getattr(Context.local, "value", {})
            if isinstance(active_context, dict):
                ambient.update(active_context)
            if caller is not None:
                ambient.update(caller.f_globals)
                ambient.update(caller.f_locals)
            return ambient
        finally:
            del frame

    def solve(self, context=None, sep="|"):
        context = {} if context is None else context
        rendered = self._render_template(self._template, context, sep=sep)
        return self._replace_captured(rendered, reveal=True, sep=sep, context=context)

    def _capture_secret(self, value, *, depth=0):
        index = len(self._captured_secrets)
        marker = f"\x00SIGILS_SECRET_{index}\x00"
        while marker in self._template or marker in self._captured_secrets:
            index += 1
            marker = f"\x00SIGILS_SECRET_{index}\x00"
        self._captured_secrets[marker] = (value, depth)
        return marker

    def _replace_captured(self, template, *, reveal, sep="|", context=None):
        rendered = template
        for marker, (secret, depth) in reversed(self._captured_secrets.items()):
            if not reveal:
                replacement = Secret.REDACTED
            else:
                value = secret
                raw_value = value.reveal() if isinstance(value, Secret) else value
                if (
                    context is not None
                    and isinstance(raw_value, str)
                    and depth < self.max_depth
                    and self.pattern.search(raw_value)
                ):
                    raw_value = self._render_template(
                        raw_value,
                        context,
                        sep=sep,
                        depth=depth + 1,
                    )
                    value = (
                        Secret(raw_value) if isinstance(secret, Secret) else raw_value
                    )
                replacement = self._stringify(value, sep)
            rendered = rendered.replace(marker, replacement)
        return rendered

    def _render_template(
        self, template, context, *, sep="|", depth=0, eager_only=False
    ):
        if depth > self.max_depth:
            return template

        def replace(match):
            if eager_only and not match.group("eager"):
                return match.group(0)
            expression = match.group("expression")
            value = self._resolve_expression(expression, context)
            if value is _UNRESOLVED:
                return match.group(0)
            protected = isinstance(value, Secret)
            raw_value = value.reveal() if protected else value
            if (
                isinstance(raw_value, str)
                and depth < self.max_depth
                and self.pattern.search(raw_value)
            ):
                raw_value = self._render_template(
                    raw_value,
                    context,
                    sep=sep,
                    depth=depth + 1,
                    eager_only=eager_only,
                )
                value = Secret(raw_value) if protected else raw_value
            if eager_only and isinstance(value, Secret):
                return self._capture_secret(value, depth=depth)
            return self._stringify(value, sep)

        return self.pattern.sub(replace, template)

    @classmethod
    def _reveal_value(cls, value):
        if isinstance(value, Secret):
            return cls._reveal_value(value.reveal())
        if isinstance(value, dict):
            return {key: cls._reveal_value(item) for key, item in value.items()}
        if isinstance(value, list):
            return [cls._reveal_value(item) for item in value]
        if isinstance(value, tuple):
            return tuple(cls._reveal_value(item) for item in value)
        return value

    @classmethod
    def _redact_value(cls, value):
        if isinstance(value, Secret):
            return Secret.REDACTED
        if isinstance(value, dict):
            return {key: cls._redact_value(item) for key, item in value.items()}
        if isinstance(value, list):
            return [cls._redact_value(item) for item in value]
        if isinstance(value, tuple):
            return tuple(cls._redact_value(item) for item in value)
        return value

    @classmethod
    def _stringify(cls, value, sep):
        value = cls._reveal_value(value)
        if isinstance(value, dict):
            if "value" in value:
                return str(value["value"])
            return sep.join(str(key) for key in value)
        return str(value)

    def _resolve_call_argument(self, argument, context):
        """Resolve one call argument, including comma-delimited tuple values."""
        argument = argument.strip()
        if "," in argument:
            return tuple(
                self._resolve_call_argument(item, context)
                for item in argument.split(",")
            )
        if argument.startswith("%"):
            return argument[1:].strip()
        resolved = self._resolve_expression(argument, context)
        if resolved is _UNRESOLVED:
            return argument
        return resolved

    def _run_structured_call(self, function, argument_sets, context):
        """Invoke a callable from colon-delimited positional/keyword arguments."""
        args = []
        kwargs = {}
        protected = False
        for argument in argument_sets:
            argument = argument.strip()
            if not argument:
                continue

            explicit_positional = argument.startswith("=")
            if explicit_positional:
                raw_value = argument[1:].strip()
                value = self._resolve_call_argument(raw_value, context)
                if isinstance(value, Secret):
                    protected = True
                    value = value.reveal()
                args.append(value)
                continue

            if "=" in argument:
                name, raw_value = argument.split("=", 1)
                name = name.strip()
                if not name or not name.isidentifier():
                    return _UNRESOLVED
                value = self._resolve_call_argument(raw_value, context)
                if isinstance(value, Secret):
                    protected = True
                    value = value.reveal()
                kwargs[name] = value
            else:
                value = self._resolve_call_argument(argument, context)
                if isinstance(value, Secret):
                    protected = True
                    value = value.reveal()
                args.append(value)
        try:
            result = function(*args, **kwargs)
        except (TypeError, ValueError):
            return _UNRESOLVED
        if protected and result is not None and not isinstance(result, Secret):
            return Secret(result)
        return result

    def _run_func(self, func, func_args, value, context):
        protected = isinstance(value, Secret)
        call_value = value.reveal() if protected else value

        if self._provider_callable(func):
            if func_args:
                result = self._run_structured_call(func, func_args, context)
            elif getattr(func, "__sigils_requires_args__", False):
                return _UNRESOLVED
            else:
                result = func()
            if (
                protected
                and result is not _UNRESOLVED
                and not isinstance(result, Secret)
            ):
                return Secret(result)
            return result

        num_args = func.__code__.co_argcount
        if func_args:
            solved_args = []
            for arg in func_args:
                resolved = self._resolve_expression(arg, context)
                if isinstance(resolved, Secret):
                    protected = True
                solved_args.append(self._render_template(f"[{arg}]", context))
            if num_args > 0:
                if solved_args and "[" not in solved_args[0]:
                    result = func(solved_args[0], *solved_args[1:num_args])
                else:
                    result = func(func_args[0], *func_args[1:num_args])
            else:
                result = func()
        elif num_args == 1:
            result = func(call_value)
        else:
            result = func()
        if protected and result is not None and not isinstance(result, Secret):
            return Secret(result)
        return result

    @staticmethod
    def _provider_callable(value):
        return callable(value) and bool(
            getattr(value, "__sigils_safe_callable__", False)
        )

    def _resolve_traversal(self, expression, context, *, invoke_final=True):
        keys = [key for key in re.split(r"[.\s]+", expression.strip()) if key]
        value = context
        protected_path = False
        for index, key in enumerate(keys):
            literal = False
            if key.startswith("%"):
                key = key[1:]
                literal = True
            parent_protected = isinstance(value, Secret)
            lookup_value = value.reveal() if parent_protected else value
            if literal:
                if callable(lookup_value):
                    return _UNRESOLVED
                temp = key
            elif isinstance(lookup_value, SafeNamespace):
                try:
                    temp = lookup_value.resolve(key)
                except KeyError:
                    return _UNRESOLVED
                protected_path = True
            elif protected_path:
                if isinstance(lookup_value, dict) and key in lookup_value:
                    temp = lookup_value.get(key)
                elif isinstance(lookup_value, list) and key.lstrip("+-").isdigit():
                    temp = lookup_value[int(key)]
                else:
                    return _UNRESOLVED
            elif isinstance(lookup_value, dict) and key in lookup_value:
                temp = lookup_value.get(key)
            elif isinstance(lookup_value, list) and key.lstrip("+-").isdigit():
                temp = lookup_value[int(key)]
            elif key in tools:
                temp = tools[key]
            else:
                temp = None
            if temp is None and "-" in key and not literal and not protected_path:
                temp = (
                    lookup_value.get(key.replace("-", "_"))
                    if isinstance(lookup_value, dict)
                    else None
                )
            if (
                temp is None
                and lookup_value is not None
                and hasattr(lookup_value, key)
                and not literal
                and not protected_path
            ):
                temp = getattr(lookup_value, key)
            if (
                temp is None
                and lookup_value is not None
                and "-" in key
                and hasattr(lookup_value, key.replace("-", "_"))
                and not literal
                and not protected_path
            ):
                temp = getattr(lookup_value, key.replace("-", "_"))
            if temp is None:
                return _UNRESOLVED
            final = index == len(keys) - 1
            if callable(temp) and final:
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
            literal = False
            if key.startswith("%"):
                key = key[1:]
                literal = True
            parent_protected = isinstance(value, Secret)
            lookup_value = value.reveal() if parent_protected else value
            if literal:
                temp = key
            elif isinstance(lookup_value, SafeNamespace):
                if func_args:
                    return _UNRESOLVED
                try:
                    temp = lookup_value.resolve(key)
                except KeyError:
                    return _UNRESOLVED
                protected_path = True
            elif protected_path:
                if func_args:
                    return _UNRESOLVED
                if isinstance(lookup_value, dict) and key in lookup_value:
                    temp = lookup_value.get(key)
                elif isinstance(lookup_value, list) and key.lstrip("+-").isdigit():
                    temp = lookup_value[int(key)]
                else:
                    return _UNRESOLVED
            elif isinstance(lookup_value, dict) and key in lookup_value:
                temp = lookup_value.get(key)
                if isinstance(temp, SafeNamespace) and func_args:
                    return _UNRESOLVED
                if callable(temp):
                    temp = self._run_func(temp, func_args, value, context)
                    if temp is None:
                        temp = key
            elif isinstance(lookup_value, list) and key.lstrip("+-").isdigit():
                temp = lookup_value[int(key)]
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
            if temp is None and "-" in key and not literal and not protected_path:
                temp = (
                    lookup_value.get(key.replace("-", "_"))
                    if isinstance(lookup_value, dict)
                    else None
                )
            if (
                temp is None
                and lookup_value is not None
                and hasattr(lookup_value, key)
                and not literal
                and not protected_path
            ):
                temp = getattr(lookup_value, key)
            if (
                temp is None
                and lookup_value is not None
                and "-" in key
                and hasattr(lookup_value, key.replace("-", "_"))
                and not literal
                and not protected_path
            ):
                temp = getattr(lookup_value, key.replace("-", "_"))
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
            if function is _UNRESOLVED or not callable(function):
                return _UNRESOLVED
            return self._run_structured_call(function, parts[1:], context)
        if re.search(r"\s", expression):
            traversed = self._resolve_traversal(expression, context)
            if traversed is not _UNRESOLVED:
                return traversed
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

    def _solve(self, context, depth=0, template=None):
        context = {} if context is None else context
        template = self._template if template is None else template
        solved = {}
        for match in self.pattern.finditer(template):
            expression = match.group("expression")
            value = self._resolve_expression(expression, context)
            if value is _UNRESOLVED:
                continue
            raw_value = value.reveal() if isinstance(value, Secret) else value
            if (
                isinstance(raw_value, str)
                and not isinstance(value, Secret)
                and depth < self.max_depth
                and self.pattern.search(raw_value)
            ):
                sub_values = self._solve(context, depth + 1, raw_value)
                if sub_values:
                    solved[expression] = {
                        "value": self._render_template(
                            raw_value,
                            context,
                            depth=depth + 1,
                        ),
                        "sub_values": sub_values,
                    }
                    continue
            solved[expression] = value
        return solved

    def results(self, context):
        return self._redact_value(self._solve(context))

    def __mod__(self, context):
        return self.solve(context)


__all__ = ["Sigil"]
