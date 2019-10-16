import logging
from typing import Any, Callable, Optional

from .extract import extract
from .parse import parser
from .transform import SigilResolver
from .exceptions import SigilError
from .context import _context

logger = logging.getLogger(__name__)

__all__ = ["resolve"]


# noinspection PyBroadException,PyDefaultArgument
def resolve(
            text: str,
            context: Optional[dict] = None,
            required: bool = False,
            coerce: Callable = None,
            default: Optional[dict] = _context,
        ) -> str:
    """
    Resolve all sigils found in text, using the specified context.
    If the sigil can't be resolved, return it unchanged unless
    required is True, in which case raise SigilError.

    :param default:
    :param text: The text containing sigils.
    :param context: Optional dict of context used for resolution.
    :param required: If True, raise SigilError if a sigil can't resolve.
    :param coerce: Callable used to coerce resolved sigils, default str.
    :param default: Default context to use, set to None to disable.

    >>> # Resolving sigils using local context:
    >>> context = {"ENV": {"HOST": "localhost"}, "USER": "arthexis"}
    >>> resolve("Connect to [ENV.HOST] as [USER]", context)
    'Connect to localhost as arthexis'
    """

    context = {**(default or {}), **(context or {})}
    if not context:
        raise ValueError("context is required")
    if text.startswith('[') and text.endswith(']'):
        sigils = {text}  # Don't extract, coerce optional
    else:
        coerce = coerce or str       # Coerce can't be none
        sigils = set(extract(text))  # Extract is necessary
    if not sigils:
        logger.debug("No sigils found in '%s'", text)
        return text  # Not an error, just do nothing
    logger.debug("Found sigils: %s", sigils)
    for sigil in sigils:
        try:
            # By using a lark transformer, we parse and resolve
            # each sigil in isolation and in a single pass
            tree = parser.parse(sigil)
            value = SigilResolver(context).transform(tree).children[0]
            logger.debug("Sigil %s resolved to '%s'", sigil, value)
            if coerce is None:
                return value
            text = text.replace(sigil, coerce(value))
        except Exception as ex:
            if required:
                raise SigilError(sigil) from ex
            logger.debug("Sigil %s not resolved", sigil)
    return text
