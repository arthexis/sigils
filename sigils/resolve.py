import logging
from typing import Any

from .extract import extract
from .parse import parser
from .transform import SigilResolver
from .exceptions import SigilError

logger = logging.getLogger(__name__)

__all__ = ["set_context", "resolve"]


def _joiner(data):
    def inner(sep):
        return (sep or "").join(data)
    return inner


# Global default context
# Don't modify this directly, use set_context()
_context = {
    "JOIN": _joiner
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


# noinspection PyBroadException
def resolve(text: str, context: dict = None, required=False, coerce=str) -> str:
    """
    Resolve all sigils found in text, using the specified context.
    If the sigil can't be resolved, return it unchanged unless
    required is True, in which case raise SigilError.

    :param text: The text containing sigils.
    :param context: Optional dict of context used for resolution.
    :param required: If True, raise SigilError if a sigil can't resolve.
    :param coerce: Callable used to coerce resolved sigils, default str.

    >>> # Resolving sigils using local context:
    >>> context = {"ENV": {"HOST": "localhost"}, "USER": "arthexis"}
    >>> resolve("Connect to [ENV.HOST] as [USER]", context)
    'Connect to localhost as arthexis'
    """
    global _context

    context = {**_context, **(context or {})}
    if not context:
        raise ValueError("context is required")
    if text.startswith('[') and text.endswith(']'):
        sigils = {text}
    else:
        sigils = set(extract(text))
    if not sigils:
        logger.debug("No sigils found in '%s'", text)
        return text
    logger.debug("Found sigils: %s", sigils)
    for sigil in sigils:
        try:
            tree = parser.parse(sigil)
            value = SigilResolver(context).transform(tree).children[0]
            logger.debug("Sigil %s resolved to '%s'", sigil, value)
            text = text.replace(sigil, coerce(value) if coerce else value)
        except Exception as ex:
            if required:
                raise SigilError(sigil) from ex
            logger.debug("Sigil %s not resolved", sigil)
    return text
