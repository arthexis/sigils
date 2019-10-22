import threading
from typing import Any
from collections import ChainMap
from contextlib import contextmanager


__all__ = ["set_context"]


def _join(parent, arg):
    """Join parent (a sequence) using sep."""
    return (arg or "").join(str(x) for x in parent)


def _mask(parent, arg):
    """Replaces all characters in a string with a mask."""
    return str(arg or '*') * len(parent)


def _if(parent, arg):
    """Return the value only if condition is met."""
    if parent is None:
        return arg if arg else ''
    return parent if parent == arg else ''


def _null(parent, arg):
    """Return nothing regardless of args or parent."""
    return ''


def _add(parent, arg):
    """Add the values of the parent and the param."""
    return parent + arg if arg else sum(parent)


def _len(parent, arg):
    """Return the length of parent."""
    if arg:
        raise ValueError("Unexpected argument for LEN")
    return len(parent)


def _fold(parent, arg):
    """Apply casefold to parent, useful for string comparisons."""
    if arg:
        raise ValueError("Unexpected argument for LEN")
    return str(parent).casefold()


# Global default context
# Don't modify this directly, use set_context()
_default_context = {
    "JOIN": _join,
    "MASK": _mask,
    "IF": _if,
    "NULL": _null,
    "ADD": _add,
    "LEN": _len,
    "FOLD": _fold,
}

# Thread local context
_thread_locals = threading.local()
_thread_locals.context = {}

# Using a ChainMap allows us to use multiple layers of context
# while avoiding duplication of the default context.
_context = ChainMap(_default_context, _thread_locals.context)


# noinspection PyUnresolvedReferences
def set_context(key: str, value: Any) -> None:
    """
    Set a global default context for resolve.
    This will only apply to the current thread.

    :param key: String key used to lookup context.
    :param value: The context value, usually a callable or instance.

    >>> # Use resolve with only default global context
    >>> set_context("SYS", {"PATH": "/usr/bin"})
    >>> resolve("System path is [SYS.PATH]")
    'System path is /usr/bin'

    >>> # Use set_context to create a global function
    >>> set_context("PERCENT", lambda parent, arg: int(float(parent) * (arg or 100)))
    >>> context = {"VALUE": 0.5}
    >>> resolve("The percent is [VALUE.PERCENT]%", context)
    'The percent is 50%'
    """

    global _thread_locals
    _thread_locals.context[key] = value
