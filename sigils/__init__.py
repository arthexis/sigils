import re
import threading


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

    def _resolve(self, context, depth=0, execute=True, max_depth=6):
        resolved = {}
        for match in self.pattern.findall(self.template):
            keys = match.split('.')
            value = context
            function_args = []
            try:
                for i, key in enumerate(keys):
                    if ':' in key:
                        key, *function_args = key.split(':')
                    if isinstance(value, dict):
                        temp = value.get(key)
                    elif isinstance(value, list) and key.isdigit():
                        temp = value[int(key)]
                    else:
                        temp = None
                    if temp is None and '-' in key:
                        temp = value.get(key.replace('-', '_')) if isinstance(value, dict) else None
                    if temp is None and hasattr(value, key):
                        temp = getattr(value, key)
                    if temp is None and '-' in key and hasattr(value, key.replace('-', '_')):
                        temp = getattr(value, key.replace('-', '_'))
                    if temp is not None:
                        value = temp
                        if callable(value) and execute:
                            if function_args:
                                resolved_function_args = [Sigil(f'%[{arg[1:]}]').interpolate(context) if arg.startswith('%') else arg for arg in function_args]
                                value = value(*resolved_function_args)
                            else:
                                value = value()
                    else:
                        value = None
                        break
            except (TypeError, AttributeError):
                value = None
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
                    s = Sigil(value)
                    resolved_value = s._resolve(context, depth + 1, execute, max_depth)
                    if resolved_value:
                        resolved[key] = {
                            'value': s.interpolate(context, execute, max_depth),
                            'sub_values': resolved_value
                        }
                    else:
                        resolved[key] = {'value': value}
        return resolved

    def _get_value(self, key, value):
        if isinstance(value, dict):
            temp = value.get(key)
            if temp is None and '-' in key:
                temp = value.get(key.replace('-', '_'))
        elif isinstance(value, list):
            try:
                temp = value[int(key)]
            except (IndexError, ValueError):
                temp = None
        else:
            temp = getattr(value, key, None)
            if temp is None and '-' in key:
                temp = getattr(value, key.replace('-', '_'), None)
        return temp

    def interpolate(self, context, execute=True, max_depth=6, handle_errors="propagate"):
        """
        Interpolate the template with the provided context.

        Args:
            context (dict or object): The context from which to take the values.
            execute (bool, optional): If True, execute any callable values found in the context. Defaults to True.
            max_depth (int, optional): The maximum depth for resolving nested sigils. Defaults to 6.
            handle_errors (str, optional): How to handle errors that occur during interpolation. 
                Can be "propagate" (raise the error), "ignore" (return the original template), 
                or "replace" (replace the template with the error message). Defaults to "propagate".

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
            resolved = self._resolve(context, 0, execute, max_depth)
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
        print(f"Context: {context}")
        result = self.interpolate(context)
        print(f"Interpolated result: {result}") 
        return result
        

__all__ = ['Sigil']
