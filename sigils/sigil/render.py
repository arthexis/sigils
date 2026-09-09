import inspect

from ..context import Context
from ..secret import Secret
from .constants import _UNRESOLVED


class RenderMixin:
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
                    value = Secret(raw_value) if isinstance(secret, Secret) else raw_value
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
