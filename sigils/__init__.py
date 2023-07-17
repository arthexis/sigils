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

    def __init__(self, template):
        """
        Initialize a new Sigil instance.

        Args:
            template (str): The template string.

        Example usage:

        ```python
        s = Sigil("Hello, %[name]!")
        ```

        """
        self.template = template
        self.pattern = getattr(self._cache, 'value', {}).get(template)
        if self.pattern is None:
            self.pattern = re.compile(r'%\[(.*?)\]')
            self._cache.value = {template: self.pattern}

    def _run_func_with_sigil_args(self, func, func_args, value, context, execute, max_depth, debug):
        num_args = func.__code__.co_argcount
        if func_args:
            if debug:
                print(f"Tool: {func}, value: {value}, func_args: {func_args}")
            resolved_args = [Sigil(f'%[{arg}]').interpolate(
                context, execute, max_depth
            ) for arg in func_args]
            if debug:
                print(f"Resolved args: {resolved_args}")
            if num_args > 0:
                if resolved_args and '%[' not in resolved_args[0]:
                    return func(resolved_args[0], *resolved_args[1:num_args - 1])
                else:
                    return func(func_args[0], *func_args[1:num_args - 1])
            else:
                return func()
        else:
            if num_args == 1:
                return func(str(value))
            else:
                return func()

    def _resolve(self, context, depth=0, execute=True, max_depth=6, debug=False):
        resolved = {}
        for match in self.pattern.findall(self.template):
            if debug:
                print(f"Found match: {match}")
            keys = match.split('.')
            if debug:
                print(f"Split keys: {keys}")
            value = context
            func_args = []
            for i, key in enumerate(keys):
                if ':' in key:
                    key_parts = key.split(':')
                    key = key_parts[0]
                    func_args = key_parts[1:]
                if debug:
                    print(f"Processing key: {key}, func_args: {func_args}")
                literal = False
                if key.startswith('%'):
                    key = key[1:]
                    literal = True
                if literal:
                    temp = key
                elif value and isinstance(value, dict) and key in value:
                    if debug:
                        print(f"Value is a dict with the key: {value}")
                    temp = value.get(key, None)
                    if callable(temp):
                        temp = self._run_func_with_sigil_args(
                            temp, func_args, value, context, execute, max_depth, debug)
                elif value and isinstance(value, list) and key.isdigit():
                    if debug:
                        print(f"Value is a list: {value}")
                    temp = value[int(key)]
                elif key in tools:
                    if debug:
                        print(f"Found tool: {key}")
                    tool_func = tools[key]
                    if callable(tool_func):
                        temp = self._run_func_with_sigil_args(
                            tool_func, func_args, value, context, execute, max_depth, debug)
                    else:
                        if debug:
                            print(f"Non-callable tool: {tool_func}")
                        temp = tool_func
                else:
                    if debug:
                        print(f"Value is an object: {value}")
                    temp = None
                if debug:
                    print(f"Temp value: {temp}")
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
                    if debug:
                        print(f"Could not find value for key: {key}")
                    value = None
                    break
            if value is not None:
                resolved[match] = value
            else:
                global_context = getattr(Sigil.Context._context, 'value', {})
                value = global_context.get(match.replace('-', '_'), None)
                if value is not None:
                    resolved[match] = value
        if depth < max_depth:
            for key, value in list(resolved.items()):
                if isinstance(value, str) and '%' in value:
                    if debug:
                        print(f"Found nested sigil: {value}")
                    s = Sigil(value)
                    resolved_value = s._resolve(context, depth + 1, execute, max_depth, debug)
                    if resolved_value:
                        resolved[key] = {
                            'value': s.interpolate(context, execute, max_depth, debug),
                            'sub_values': resolved_value
                        }
                    else:
                        resolved[key] = {'value': value}
        return resolved

    def interpolate(self, context, execute=True, max_depth=6, handle_errors="propagate", debug=False):
        """
        Interpolate the template with the provided context.

        Args:
            context (dict or object): The context from which to take the values.
            execute (bool, optional): If True, execute any callable values found in the context. Defaults to True.
            max_depth (int, optional): The maximum depth for resolving nested sigils. Defaults to 6.
            handle_errors (str, optional): How to handle errors that occur during interpolation. 
                Can be "propagate" (raise the error), "ignore" (return the original template), 
                "replace" (replace the template with the error message). Defaults to "propagate".

        Returns:
            str: The interpolated string.

        Raises:
            Exception: If handle_errors is set to "propagate" and an error occurs during interpolation.

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
            resolved = self._resolve(context, 0, execute, max_depth, debug)
        except Exception as e:
            if handle_errors == "propagate":
                raise e
            elif handle_errors == "ignore":
                return self.template
            else:  # handle_errors == "replace"
                return str(e)
        parts = self.pattern.split(self.template)
        for i in range(1, len(parts), 2):
            value = resolved.get(parts[i])
            if isinstance(value, dict):
                parts[i] = value['value']
            else:
                parts[i] = str(value) if value is not None else f'%[{parts[i]}]'
        result = ''.join(parts)
        return result

    def sigils(self, context):
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
        Operator overload for the modulus (%) operator. This allows for easy interpolation of the template 
        with the provided context.

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
        

__all__ = ['Sigil']
