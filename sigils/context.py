from typing import Any


__all__ = ["set_context"]


def joiner(data):
    """Return a function that takes a sep and str.joins data."""

    def inner(sep):
        return (sep or "").join(str(x) for x in data)

    return inner


def hider(data):
    """Replaces all characters in a string with a mask."""

    def inner(mask):
        return str(mask) * len(data)

    return inner


# Global default context
# Don't modify this directly, use set_context()
_context = {
    "JOIN": joiner,
    "HIDE": hider,
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
    >>> set_context("PERCENT", lambda x: int(float(x) * 100))
    >>> context = {"VALUE": 0.5}
    >>> resolve("The percent is [VALUE.PERCENT]%", context)
    'The percent is 50%'
    """

    global _context
    _context[key] = value
