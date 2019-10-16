from typing import Any


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
    if arg:
        return parent + arg
    return sum(parent)


# Global default context
# Don't modify this directly, use set_context()
_context = {
    "JOIN": _join,
    "MASK": _mask,
    "IF": _if,
    "NULL": _null,
    "ADD": _add,
}


# noinspection PyUnresolvedReferences
def set_context(key: str, value: Any) -> None:
    """
    Set a global default context for resolve.

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

    global _context
    _context[key] = value
