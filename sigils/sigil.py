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
        """Initialize a sigil template.

        ``[...]`` tokens are lazy and are only resolved by ``solve()`` or the
        ``%`` operator. ``%[...]`` tokens are eager and are resolved during
        construction from the current execution context.
        """
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
        """Return the template with captured eager secrets redacted."""
        return self._replace_captured(self._template, reveal=False)

    @staticmethod
    def _ambient_context():
        """Return the Python execution context used by eager sigils."""
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
        """Resolve all remaining sigils with the provided context."""
        context = {} if context is None else context
        rendered = self._render_template(self._template, context, sep=sep)
        return self._replace_captured(
            rendered,
            reveal=True,
            sep=sep,
            context=context,
        )

    def _capture_secret(self, value, *, depth=0):
        """Store an eager secret out-of-band and return an opaque marker."""
        index = len(self._captured_secrets)
        marker = f"\x00SIGILS_SECRET_{index}\x00"
        while marker in self._template or marker in self._captured_secrets:
            index += 1
            marker = f"\x00SIGILS_SECRET_{index}\x00"
        self._captured_secrets[marker] = (value, depth)
        return marker

    def _replace_captured(self, template, *, reveal, sep="|", context=None):
        """Replace captured-secret markers with redacted or revealed text."""
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
        """Render matching sigils in *template* using the requested resolution phase."""
        if depth > self.max_depth:
            return template

        def replace(match):
            """Resolve one regular-expression match or preserve it when unresolved."""
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
        """Recursively unwrap protected values for intentional template output."""
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
        """Recursively replace protected values with the redaction marker."""
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
        """Convert a resolved value to template text using *sep* for mappings."""
        value = cls._reveal_value(value)
        if isinstance(value, dict):
            if "value" in value:
                return str(value["value"])
            return sep.join(str(key) for key in value)
        return str(value)

    def _run_func(self, func, func_args, value, context):
        """Resolve function arguments, invoke *func*, and preserve secret taint."""
        num_args = func.__code__.co_argcount
        protected = isinstance(value, Secret)
        call_value = value.reveal() if protected else value

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
            result = func(None)

        if protected and result is not None and not isinstance(result, Secret):
            return Secret(result)
        return result

    def _resolve_expression(self, expression, context):
        """Resolve a dotted sigil expression against context, attributes, and tools."""
        keys = expression.split(".")
        value = context
        func_args = []
        protected_path = False

        for key in keys:
            if " " in key:
                key_parts = key.split(" ")
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

            if protected_path and callable(temp):
                return _UNRESOLVED

            if temp and callable(temp):
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

    def _solve(self, context, depth=0, template=None):
        """Return resolved values for sigils in a template."""
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
        """Return resolved sigil values with protected data redacted."""
        return self._redact_value(self._solve(context))

    def __mod__(self, context):
        """Resolve the template using the modulus operator."""
        return self.solve(context)


__all__ = ["Sigil"]
