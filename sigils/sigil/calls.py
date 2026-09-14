from ..secret import Secret
from .constants import _UNRESOLVED
from .sequences import split_top_level_sequence


class CallMixin:
    def _resolve_call_argument(self, argument, context):
        """Resolve one call argument, including comma-delimited tuple values."""
        argument = argument.strip()
        sequence = split_top_level_sequence(argument)
        if sequence is not None:
            return tuple(
                self._resolve_call_argument(item, context)
                for item in sequence
            )
        if argument.startswith("%"):
            return argument[1:].strip()
        resolved = self._resolve_expression(argument, context)
        if resolved is _UNRESOLVED:
            return argument
        return resolved

    def _unwrap_protected_argument(self, value):
        """Reveal Secret values in tuple arguments and report protection."""
        if isinstance(value, Secret):
            return value.reveal(), True
        if isinstance(value, tuple):
            protected = False
            items = []
            for item in value:
                item, item_protected = self._unwrap_protected_argument(item)
                protected = protected or item_protected
                items.append(item)
            return tuple(items), protected
        return value, False

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
                value, value_protected = self._unwrap_protected_argument(value)
                protected = protected or value_protected
                args.append(value)
                continue

            if "=" in argument:
                name, raw_value = argument.split("=", 1)
                name = name.strip()
                if not name or not name.isidentifier():
                    return _UNRESOLVED
                value = self._resolve_call_argument(raw_value, context)
                value, value_protected = self._unwrap_protected_argument(value)
                protected = protected or value_protected
                kwargs[name] = value
            else:
                value = self._resolve_call_argument(argument, context)
                value, value_protected = self._unwrap_protected_argument(value)
                protected = protected or value_protected
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
