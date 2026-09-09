"""Public built-in tool registry."""

from .functions import *
from .functions import __all__ as _FUNCTION_NAMES

tools = {name: globals()[name] for name in _FUNCTION_NAMES}
tools["tools"] = tools

__all__ = [*_FUNCTION_NAMES, "tools"]
