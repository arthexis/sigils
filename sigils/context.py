from typing import Any


__all__ = ["set_context"]


def _join(parent, sep):
    """Join parent (a sequence) using sep."""
    return (sep or "").join(str(x) for x in parent)


def _hide(parent, mask):
    """Replaces all characters in a string with a mask."""
    return str(mask or '*') * len(parent)


def _if(parent, val):
    """Return the value only if condition is met."""
    if parent is None:
        return val if val else ''
    return parent if parent == val else ''


# Global default context
# Don't modify this directly, use set_context()
_context = {
    "JOIN": _join,
    "HIDE": _hide,
    "IF": _if,
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
