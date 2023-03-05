import io
import ast
import contextlib
from enum import Enum
from typing import Union, Tuple, Text, Iterator, Callable, Any, Optional, TextIO

from . import errors, parsing, contexts

import logging
logger = logging.getLogger(__name__)


# Rewrite the constants as an enum
class OnError(str, Enum):
    CONTINUE = "continue"
    RAISE = "raise"
    REMOVE = "remove"
    DEFAULT = "default"


def splice(
        text: Union[str, TextIO],
        serializer: Callable[[Any], str] = str,
        on_error: str = OnError.DEFAULT,
        default: Optional[str] = "",
        recursion_limit: int = 1,
        cache: bool = True,
) -> str:
    """
    Resolve all sigils found in text, using the local context.
    If the text contains no sigils, it will be returned unchanged.

    :param text: The text containing sigils.
    :param on_error: What to do if a sigil cannot be resolved:
        OnError.DEFAULT: Replace the sigil with the default value (the default).
        OnError.CONTINUE: Ignore the error and leave the text unchanged.
        OnError.RAISE: Raise a SigilError detailing the problem.
        OnError.REMOVE: Remove the sigil from the text output.
    :param serializer: Function used to serialize the sigil value, defaults to str.
    :param default: Value to use when the sigils resolves to None, defaults to "".
    :param recursion_limit: If greater than zero, and the output of a resolved sigil
        contains other sigils, resolve them as well until no sigils remain or
        until the recursion limit is reached (default 1).
    :param cache: Use an LRU cache to store resolved sigils (default True).

    >>> # Resolving sigils using context:
    >>> with context(ENV={"HOST": "localhost"}, USER="arthexis"}):
    >>>     resolve("Connect to [ENV.HOST] as [USER]")
    'Connect to localhost as arthexis'
    """

    if not isinstance(text, str):
        text = text.read()
    sigils = set(parsing.pull(text))

    if not sigils:
        # logger.debug(f"No more sigils in '{text}'.")
        return text  # Not an error, just do nothing

    results = []
    # logger.debug(f"Extracted sigils: {sigils}.")
    for sigil in sigils:
        try:
            # By using a lark transformer, we parse and resolve
            # each sigil in isolation and in a single pass
            if cache and sigil in contexts._local.lru:
                value = contexts._local.lru[sigil]
                # logger.debug("Sigil '%s' value from cache '%s'.", sigil, value)
            else:
                tree = parsing.parse(sigil[1:-1])
                transformer = parsing.SigilContextTransformer(contexts._local.ctx)
                value = transformer.transform(tree).children[0]
                # logger.debug("Sigil '%s' resolved to '%s'.", sigil, value)
                if cache:
                    contexts._local.lru[sigil] = value
            if value is not None:
                fragment = serializer(value)
                if recursion_limit > 0:
                    fragment = splice(
                        fragment,
                        serializer,
                        on_error,
                        default,
                        recursion_limit=(recursion_limit - 1)
                    )
                text = text.replace(sigil, fragment)
        except Exception as ex:
            if on_error == OnError.RAISE:
                raise errors.SigilError(sigil) from ex
            elif on_error == OnError.REMOVE:
                text = text.replace(sigil, "")
            elif on_error == OnError.DEFAULT:
                text = text.replace(sigil, str(default))
            # logger.debug(f"Sigil '{sigil}' could not be resolved:\n{ex}")
    if results:
        return str(results) if len(results) > 1 else str(results[0])
    return text


def vanish(
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

    sigils = list(parsing.pull(text))
    _iter = (iter(pattern) if isinstance(pattern, Iterator) 
             else iter(pattern * len(sigils)))
    for sigil in set(sigils):
        text = (text.replace(sigil, str(next(_iter)) or sigil))
    return text, tuple(sigils)

__exec = exec

def exec(
        code: str,
        on_error: str = OnError.DEFAULT,
        default: Optional[str] = "",
        recursion_limit: int = 1,
        cache: bool = True,
        _locals: Optional[dict[str, Any]] = None,
        _globals: Optional[dict[str, Any]] = None,
) -> Union[str, None]:
    """Execute a Python code block after resolving any sigils appearing in 
    it's strings. Sigils appearing outside of strings are not resolved
    to avoid unintended side effects. If the executed code block prints to stdout,
    it's output is returned. If the code prints to stderr, a SigilError is raised.
    """
    tree = ast.parse(code)
    for node in ast.walk(tree):
        if isinstance(node, ast.Str):
            node.s = splice(
                node.s, 
                on_error=on_error, 
                default=default, 
                recursion_limit=recursion_limit, 
                cache=cache
            )   
    with contextlib.redirect_stdout(io.StringIO()) as f:
        with contextlib.redirect_stderr(io.StringIO()) as err:
            __exec(compile(tree, "<string>", "exec"), _globals, _locals)
            if err.getvalue():
                raise errors.SigilError(err.getvalue())
    return f.getvalue()


__all__ = ["splice", "vanish", "exec", "OnError"]
