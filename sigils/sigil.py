import inspect
import re
import threading

from .context import Context
from .tools import tools


_UNRESOLVED = object()


class Sigil:
    cache = threading.local()

    max_depth = 6
    debug = False

    def __init__(self, template, *, max_depth=None, debug=None):
        """Initialize a sigil template.

        ``[...]`` tokens are lazy and are only resolved by ``solve()`` or the
        ``%`` operator. ``%[...]`` tokens are eager and are resolved during
        construction from the current execution context.
        """
        self.template = str(template)
        self.max_depth = max_depth if max_depth is not None else self.__class__.max_depth
        self.debug = debug if debug is not None else self.__class__.debug

        self.pattern = re.compile(r"(?P<eager>%)?\[(?P<expression>.*?)\]")
        self.template = self._render_template(
            self.template,
            self._ambient_context(),
            eager_only=True,
        )

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
        return self._render_template(self.template, context, sep=sep)

    def _render_template(self, template, context, *, sep="|", depth=0, eager_only=False):
        if depth > self.max_depth:
            return template

        def replace(match):
            if eager_only and not match.group("eager"):
                return match.group(0)

            expression = match.group("expression")
            value = self._resolve_expression(expression, context)
            if value is _UNRESOLVED:
                return match.group(0)

            if (
                isinstance(value, str)
                and depth < self.max_depth
                and self.pattern.search(value)
            ):
                value = self._render_template(
                    value,
                    context,
                    sep=sep,
                    depth=depth + 1,
                    eager_only=eager_only,
                )

            return self._stringify(value, sep)

        return self.pattern.sub(replace, template)

    @staticmethod
    def _stringify(value, sep):
        if isinstance(value, dict):
            if "value" in value:
                return str(value["value"])
            return sep.join(str(key) for key in value)
        return str(value)

    def _run_func(self, func, func_args, value, context):
        num_args = func.__code__.co_argcount
        if func_args:
            solved_args = [
                self._render_template(f"[{arg}]", context)
                for arg in func_args
            ]
            if num_args > 0:
                if solved_args and "[" not in solved_args[0]:
                    return func(solved_args[0], *solved_args[1:num_args - 1])
                return func(func_args[0], *func_args[1:num_args - 1])
            return func()

        if num_args == 1:
            return func(value)
        return func(None)

    def _resolve_expression(self, expression, context):
        keys = expression.split(".")
        value = context
        func_args = []

        for key in keys:
            if " " in key:
                key_parts = key.split(" ")
                key = key_parts[0]
                func_args = key_parts[1:]

            literal = False
            if key.startswith("%"):
                key = key[1:]
                literal = True

            if literal:
                temp = key
            elif isinstance(value, dict) and key in value:
                temp = value.get(key)
                if callable(temp):
                    temp = self._run_func(temp, func_args, value, context)
                    if temp is None:
                        temp = key
            elif isinstance(value, list) and key.lstrip("+-").isdigit():
                temp = value[int(key)]
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

            if temp and callable(temp):
                temp = temp()

            if temp is None and "-" in key and not literal:
                temp = (
                    value.get(key.replace("-", "_"))
                    if isinstance(value, dict)
                    else None
                )

            if temp is None and value is not None and hasattr(value, key) and not literal:
                temp = getattr(value, key)

            if (
                temp is None
                and value is not None
                and "-" in key
                and hasattr(value, key.replace("-", "_"))
                and not literal
            ):
                temp = getattr(value, key.replace("-", "_"))

            if temp is None:
                return _UNRESOLVED

            value = temp

        return value if value is not None else _UNRESOLVED

    def _solve(self, context, depth=0, template=None):
        """Return resolved values for sigils in a template."""
        context = {} if context is None else context
        template = self.template if template is None else template
        solved = {}

        for match in self.pattern.finditer(template):
            expression = match.group("expression")
            value = self._resolve_expression(expression, context)
            if value is _UNRESOLVED:
                continue

            if (
                isinstance(value, str)
                and depth < self.max_depth
                and self.pattern.search(value)
            ):
                sub_values = self._solve(context, depth + 1, value)
                if sub_values:
                    solved[expression] = {
                        "value": self._render_template(value, context, depth=depth + 1),
                        "sub_values": sub_values,
                    }
                    continue

            solved[expression] = value

        return solved

    def results(self, context):
        """Return a dictionary with the sigils and their resolved values."""
        return self._solve(context)

    def __mod__(self, context):
        """Resolve the template using the modulus operator."""
        return self.solve(context)


__all__ = ["Sigil"]
