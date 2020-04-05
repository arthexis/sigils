import logging
import threading
import contextlib
import collections
from typing import Mapping, Union, Tuple, Text, Iterator

from . import parsing, filters, exceptions

logger = logging.getLogger(__name__)

__all__ = ["context", "replace", "resolve"]


# Global default context
# Don't modify this directly, use context()
_default_context = {
    "JOIN": filters.join,
}


# Thread local context
class ThreadLocal(threading.local):
    def __init__(self):
        self.ctx: Mapping = collections.ChainMap(_default_context)


_local = ThreadLocal()


# noinspection PyUnresolvedReferences
@contextlib.contextmanager
def context(**kwargs) -> None:
    """Update the local context used by resolve.
    :param kwargs: A mapping of context selectors to Resolvers.

    >>> with context(TEXT="hello world") as ctx:
    >>>     assert ctx["TEXT"] == "hello world"
    """
    global _local

    _local.ctx = _local.ctx.new_child(kwargs)
    yield _local.ctx
    _local.ctx = _local.ctx.parents


# noinspection PyBroadException,PyDefaultArgument
def resolve(
            text: str,
            required: bool = False,
        ) -> str:
    """
    Resolve all sigils found in text, using the local context.

    If the sigil can't be resolved, return it unchanged unless
    required is True, in which case raise SigilError.

    :param text: The text containing sigils.
    :param required: If True, raise SigilError if a sigil can't be resolved.

    >>> # Resolving sigils using context:
    >>> with context(ENV={"HOST": "localhost"}, USER="arthexis"}):
    >>>     resolve("Connect to [ENV.HOST] as [USER]")
    'Connect to localhost as arthexis'
    """

    sigils = set(parsing.extract(text))

    if not sigils:
        logger.debug(f"No sigils in '{text}'.")
        return text  # Not an error, just do nothing

    results = []
    logger.debug(f"Extracted sigils: {sigils}")
    for sigil in sigils:
        try:
            # By using a lark transformer, we parse and resolve
            # each sigil in isolation and in a single pass
            tree = parsing.parse(sigil)
            transformer = parsing.ContextTransformer(_local.ctx)
            value = transformer.transform(tree).children[0]
            logger.debug(f"Sigil {sigil} resolved to '{value}'.")
            text = text.replace(sigil, str(value))
        except Exception as ex:
            if required:
                raise exceptions.SigilError(sigil) from ex
            logger.debug(f"Sigil {sigil} not resolved")

    if results:
        return results if len(results) > 1 else results[0]
    return text


def replace(
        text: str,
        pattern: Union[Text, Iterator]
) -> Tuple[str, Tuple[str]]:
    """
    Replace all sigils in the text with another pattern.
    Returns the replaced text and a list of sigils in found order.
    This will not resolve the sigils by default.

    :param text: The text with the sigils to be replaced.
    :param pattern: A text or iterator used to replace the sigils with.
    :return: A tuple of: replaced text, list of sigil strings.

    >>> # Protect against SQL injection.
    >>> replace("select * from users where username = [USER]", "?")
    ('select * from users where username = ?', ['[USER]'])
    """

    sigils = list(parsing.extract(text))
    use_next = hasattr(pattern, "__next__")
    for sigil in set(sigils):
        if use_next:
            text = text.replace(sigil, str(next(pattern)))
        else:
            text = text.replace(sigil, pattern)
    return text, tuple(sigils)
