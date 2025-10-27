import re
import threading

from .tools import tools
from .context import Context


class Sigil:
    cache = threading.local()

    # Default settings at the class level
    max_depth = 6
    debug = False

    def __init__(self, template, *, max_depth=None, debug=None):
        """
        Initialize a new Sigil instance.

        Args:
            template (str): The template string.
            max_depth (int, optional): Maximum depth for resolving sigils.
            debug (bool, optional): Enable debug logging.
        """
        self.template = template

        # Use instance-specific values or fall back to class defaults
        self.max_depth = max_depth if max_depth is not None else self.__class__.max_depth
        self.debug = debug if debug is not None else self.__class__.debug

        self.pattern = getattr(self.cache, 'value', {}).get(template)
        if self.pattern is None:
            self.pattern = re.compile(r'%\[(.*?)\]')
            self.cache.value = {template: self.pattern}

    def solve(self, context=None, sep="|"):
        """Solve the template with the provided context."""
        solved = self._solve(context, 0)
        parts = self.pattern.split(self.template)
        for i in range(1, len(parts), 2):
            value = solved.get(parts[i])
            if isinstance(value, dict):
                if "value" in value:
                    parts[i] = value["value"]
                else:
                    parts[i] = sep.join(value.keys())
            else:
                parts[i] = str(value) if value is not None else f'%[{parts[i]}]'
        result = ''.join(parts)
        return result

    def _run_func(self, func, func_args, value, context):
        num_args = func.__code__.co_argcount
        if func_args:
            solved_args = [Sigil(f'%[{arg}]').solve(context) for arg in func_args]
            if num_args > 0:
                if solved_args and '%[' not in solved_args[0]:
                    return func(solved_args[0], *solved_args[1:num_args - 1])
                else:
                    return func(func_args[0], *func_args[1:num_args - 1])
            else:
                return func()
        else:
            if num_args == 1:
                return func(value)
            else:
                return func(None)

    def _solve(self, context, depth=0):
        solved = {}
        for match in self.pattern.findall(self.template):
            temp = None
            original = str(match)
            keys = match.split('.')
            value = context
            func_args = []
            for i, key in enumerate(keys):
                if ' ' in key:
                    key_parts = key.split(' ')
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
                        temp = self._run_func(temp, func_args, value, context)
                        if temp is None:
                            temp = key
                elif value and isinstance(value, list) and key.lstrip("+-").isdigit():
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
                if temp is None and '-' in key and not literal:
                    temp = value.get(key.replace('-', '_')) if isinstance(value, dict) else None
                if temp is None and hasattr(value, key) and not literal:
                    temp = getattr(value, key)
                if temp is None and '-' in key and hasattr(value, key.replace('-', '_')) and not literal:
                    temp = getattr(value, key.replace('-', '_'))
                if temp is not None:
                    value = temp
                else:
                    value = original
                    break
            if value is not None:
                solved[match] = value
            else:
                global_context = getattr(Context.local, 'value', {})
                value = global_context.get(match.replace('-', '_'), None)
                if value is not None:
                    solved[match] = value
        if depth < self.max_depth:
            for key, value in list(solved.items()):
                if isinstance(value, str) and '%' in value:
                    s = Sigil(value)
                    solved_value = s._solve(context, depth + 1)
                    if solved_value:
                        solved[key] = {
                            'value': s.solve(context),
                            'sub_values': solved_value
                        }
                    else:
                        solved[key] = {'value': value}
        return solved

    def results(self, context):
        """Returns a dictionary with all the sigils in the template and their solved values from the context.
        """
        return self._solve(context)

    def __mod__(self, context):
        """Operator overload for the modulus (%) operator. Same as solve method."""
        result = self.solve(context or {})
        return result

    
__all__ = ["Sigil"]
