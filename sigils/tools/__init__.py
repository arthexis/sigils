"""Public built-in tool registry."""

from . import functions as _functions

_FUNCTION_NAMES = tuple(name for name in _functions.__all__ if name != "tools")
globals().update({name: getattr(_functions, name) for name in _FUNCTION_NAMES})

tools = {name: globals()[name] for name in _FUNCTION_NAMES}
tools["tools"] = tools

__all__ = [*_FUNCTION_NAMES, "tools"]
