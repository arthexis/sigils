import re
import threading
from .tools import tools


class Sigil:
    _cache = threading.local()

    class Context:
        _context = threading.local()

        def __init__(self, context):
            self.local_context = context

        def __enter__(self):
            self.old_context = getattr(self._context, 'value', {})
            self._context.value = self.local_context
            return self._context.value

        def __exit__(self, exc_type, exc_val, exc_tb):
            self._context.value = self.old_context

    # Default settings at the class level
    executable = True
    max_depth = 6
    debug = False
    on_error = "propagate"

    def __init__(self, template, executable=None, max_depth=None, debug=None, on_error=None):
        """
        Initialize a new Sigil instance.

        Args:
            template (str): The template string.
            executable (bool, optional): Whether to executable callable values.
            max_depth (int, optional): Maximum depth for resolving sigils.
            debug (bool, optional): Enable debug logging.
            on_error (str, optional): Error handling mechanism, one of:
                propagate - Re-raise the error (program may fail)
                ignore - Supress the error (behave as unresolved sigil)
                replace - Replace the sigil with the exception itself
        """
        self.template = template

        # Use instance-specific values or fall back to class defaults
        self.executable = executable if executable is not None else self.__class__.executable
        self.max_depth = max_depth if max_depth is not None else self.__class__.max_depth
        self.debug = debug if debug is not None else self.__class__.debug
        self.on_error = on_error if on_error is not None else self.__class__.on_error

        self.pattern = getattr(self._cache, 'value', {}).get(template)
        if self.pattern is None:
            self.pattern = re.compile(r'%\[(.*?)\]')
            self._cache.value = {template: self.pattern}

    def _run_function(self, func, func_args, value, context):
        num_args = func.__code__.co_argcount
        if func_args:
            resolved_args = [Sigil(f'%[{arg}]').interpolate(context) for arg in func_args]
            if num_args > 0:
                if resolved_args and '%[' not in resolved_args[0]:
                    return func(resolved_args[0], *resolved_args[1:num_args - 1])
                else:
                    return func(func_args[0], *func_args[1:num_args - 1])
            else:
                return func()
        else:
            if num_args == 1:
                return func(value)
            else:
                return func()

    def _resolve(self, context, depth=0):
        resolved = {}
        for match in self.pattern.findall(self.template):
            keys = match.split('.')
            value = context
            func_args = []
            for i, key in enumerate(keys):
                if ':' in key:
                    key_parts = key.split(':')
                    key = key_parts[0]
                    func_args = key_parts[1:]
                literal = False
                if key.startswith('%'):
                    key = key[1:]
                    literal = True
                if literal:
                    temp = key
                elif value and isinstance(value, dict) and key in value:
                    temp = value.get(key, None)
                    if callable(temp):
                        temp = self._run_function(temp, func_args, value, context)
                elif value and isinstance(value, list) and key.lstrip("+-").isdigit():
                    temp = value[int(key)]
                elif key in tools:
                    tool_func = tools[key]
                    if callable(tool_func):
                        temp = self._run_function(tool_func, func_args, value, context)
                    else:
                        temp = tool_func
                else:
                    temp = None
                if temp and callable(temp):
                    temp = temp()
                if temp is None and '-' in key and not literal:
                    temp = value.get(key.replace('-', '_')) if isinstance(value, dict) else None
                if temp is None and hasattr(value, key) and not literal:
                    temp = getattr(value, key)
                if temp is None and '-' in key and hasattr(value, key.replace('-', '_')) and not literal:
                    temp = getattr(value, key.replace('-', '_'))
                if temp is not None:
                    value = temp
                else:
                    value = None
                    break
            if value is not None:
                resolved[match] = value
            else:
                global_context = getattr(Sigil.Context._context, 'value', {})
                value = global_context.get(match.replace('-', '_'), None)
                if value is not None:
                    resolved[match] = value
        if depth < self.max_depth:
            for key, value in list(resolved.items()):
                if isinstance(value, str) and '%' in value:
                    s = Sigil(value)
                    resolved_value = s._resolve(context, depth + 1)
                    if resolved_value:
                        resolved[key] = {
                            'value': s.interpolate(context),
                            'sub_values': resolved_value
                        }
                    else:
                        resolved[key] = {'value': value}
        return resolved

    def interpolate(self, context):
        """
        Interpolate the template with the provided context.

        Args:
            context (dict or object): The context from which to take the values.

        Returns:
            str: The interpolated string.

        Raises:
            Exception: If on_error is set to "propagate" and an error occurs during interpolation.

        Example usage:

        ```python
        s = Sigil("Hello, %[name]!")
        context = {"name": "Alice"}
        print(s.interpolate(context))  # Outputs: "Hello, Alice!"
        ```

        """
        if context is None:
            context = Sigil.Context.current_context
        try:
            resolved = self._resolve(context, 0)
        except Exception as e:
            if self.on_error == "propagate":
                raise e
            elif self.on_error == "ignore":
                return self.template
            else:  # on_error == "replace"
                return e
        parts = self.pattern.split(self.template)
        for i in range(1, len(parts), 2):
            value = resolved.get(parts[i])
            if isinstance(value, dict):
                if "value" in value:
                    parts[i] = value["value"]
                else:
                    parts[i] = "|".join(value.keys())
            else:
                parts[i] = str(value) if value is not None else f'%[{parts[i]}]'
        result = ''.join(parts)
        return result

    def results(self, context):
        """
        Returns a dictionary with all the sigils in the template and their resolved values from the context.

        Args:
            context (dict or object): The context from which to take the values.

        Returns:
            dict: A dictionary with all the sigils in the template and their resolved values.

        Example usage:

        ```python
        s = Sigil("Hello, %[name]!")
        context = {"name": "Alice"}
        print(s.sigils(context))  # Outputs: {"name": "Alice"}
        ```

        """
        return self._resolve(context)

    def __mod__(self, context):
        """
        Operator overload for the modulus (%) operator.

        Args:
            context (dict or object): The context from which to take the values.

        Returns:
            str: The interpolated string.

        Example usage:

        ```python
        s = Sigil("Hello, %[name]!")
        context = {"name": "Alice"}
        print(s % context)  # Outputs: "Hello, Alice!"
        ```

        """
        result = self.interpolate(context or {})
        return result
    
