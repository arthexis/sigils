import os
import logging
import threading
import contextlib
import collections
import uuid
from typing import (
    Mapping, Union, Tuple, Text, Iterator, Callable, Any, Optional, TextIO
)

# noinspection PyUnresolvedReferences
from lru import LRU

# Try to import django.utils.timezone as datetime if exists
# If it doesn't, just normal datetime
try:
    from django.utils import timezone as datetime
except ImportError:
    from datetime import datetime

from . import parsing, exceptions

logger = logging.getLogger(__name__)

__all__ = [
    "context",
    "replace",
    "resolve",
    "RAISE",
    "DEFAULT",
    "CONTINUE",
    "REMOVE",
    "Sigil",
]


class System:
    """Used for the SYS default context."""

    class _Env:
        def __getitem__(self, item):
            return os.getenv(item)

    _env = _Env()

    @property
    def env(self):
        return self._env

    @property
    def now(self):
        return datetime.now()

    @property
    def today(self):
        return datetime.today()

    @property
    def uuid(self):
        return str(uuid.uuid4()).replace('-', '')


# Thread local context
class ThreadLocal(threading.local):
    def __init__(self):
        self.ctx: Mapping = collections.ChainMap({
            "JOIN": lambda o, s: (s or "").join(str(i) for i in o),
            "SYS": System(),
            "NUMBER": lambda x: float(x) if "." in x else int(x),
            "LOWER": lambda x: str(x).lower(),
            "UPPER": lambda x: str(x).upper(),
            "FOLD": lambda x: str(x).casefold(),
        })
        self.lru = LRU(128)


_local = ThreadLocal()


# noinspection PyUnresolvedReferences
@contextlib.contextmanager
def context(*args, **kwargs) -> None:
    """Update the local context used by resolve.

    :param args: A tuple of context sources.
    :param kwargs: A mapping of context selectors to Resolvers.

    >>> # Add to context using kwargs
    >>> with context(TEXT="hello world") as ctx:
    >>>     assert ctx["TEXT"] == "hello world"
    """
    global _local

    _local.ctx = _local.ctx.new_child(kwargs)
    for arg in args:
        for key, val in arg.items():
            _local.ctx[key] = val
    yield _local.ctx
    _local.ctx = _local.ctx.parents
    _local.lru.clear()


# Resolve on_error constants
CONTINUE = "continue"
RAISE = "raise"
REMOVE = "remove"
DEFAULT = "default"


# noinspection PyBroadException,PyDefaultArgument
def resolve(
        text: Union[str, TextIO],
        serializer: Callable[[Any], str] = str,
        on_error: str = DEFAULT,
        default: Optional[str] = "",
        recursion_limit: int = 20,
        cache: bool = True,
) -> str:
    """
    Resolve all sigils found in text, using the local context.
    If the text contains no sigils, it will be returned unchanged.

    :param text: The text containing sigils.
    :param on_error: What to do if a sigil cannot be resolved:
        DEFAULT: Replace the sigil with the default value (the default).
        CONTINUE: Ignore the error and leave the text unchanged.
        RAISE: Raise a SigilError detailing the problem.
        REMOVE: Remove the sigil from the text output.
    :param serializer: Function used to serialize the sigil value, defaults to str.
    :param default: Value to use when the sigils resolves to None, defaults to "".
    :param recursion_limit: If greater than zero, and the output of a resolved sigil
        contains other sigils, resolve them as well until no sigils remain or
        until the recursion limit is reached (default 20).
    :param cache: Use an LRU cache to store resolved sigils (default True).

    >>> # Resolving sigils using context:
    >>> with context(ENV={"HOST": "localhost"}, USER="arthexis"}):
    >>>     resolve("Connect to [ENV.HOST] as [USER]")
    'Connect to localhost as arthexis'
    """

    if not isinstance(text, str):
        text = text.read()
    sigils = set(parsing.extract(text))

    if not sigils:
        logger.debug(f"No sigils in '{text}'.")
        return text  # Not an error, just do nothing

    results = []
    logger.debug(f"Extracted sigils: {sigils}.")
    for sigil in sigils:
        try:
            # By using a lark transformer, we parse and resolve
            # each sigil in isolation and in a single pass
            if cache and sigil in _local.lru:
                value = _local.lru[sigil]
                logger.debug("Sigil '%s' value from cache '%s'.", sigil, value)
            else:
                tree = parsing.parse(sigil)
                transformer = parsing.ContextTransformer(_local.ctx)
                value = transformer.transform(tree).children[0]
                logger.debug("Sigil '%s' resolved to '%s'.", sigil, value)
                if cache:
                    _local.lru[sigil] = value
            if value is None:
                text = text.replace(sigil, default)
            else:
                fragment = serializer(value)
                if recursion_limit > 0:
                    fragment = resolve(
                        fragment,
                        serializer,
                        on_error,
                        default,
                        recursion_limit=(recursion_limit - 1)
                    )
                text = text.replace(sigil, fragment)
        except Exception as ex:
            if on_error == RAISE:
                raise exceptions.SigilError(sigil) from ex
            elif on_error == REMOVE:
                text = text.replace(sigil, "")
            elif on_error == DEFAULT:
                text = text.replace(sigil, default)
            logger.debug("Sigil '%s' not resolved.", sigil)

    if results:
        return results if len(results) > 1 else results[0]
    return text


def replace(
        text: str,
        pattern: Union[Text, Iterator],
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
    n = hasattr(pattern, "__next__")
    for sigil in set(sigils):
        text = text.replace(sigil, str(next(pattern)) if n else pattern)
    return text, tuple(sigils)


class Sigil:
    """Encapsulate a string that can contain sigils.
    When an instance of this class has its __str__ method called,
    the text gets passed through resolve automatically.
    """

    def __init__(self, original: str, **kwargs):
        self.original = original
        self.kwargs = kwargs

    def __str__(self):
        """Resolve the sigil."""
        return resolve(self.original, **self.kwargs)

    def __call__(self, *args, **kwargs):
        """Send all args and kwargs to context, then resolve."""
        with context(*args, **kwargs):
            return str(self)

