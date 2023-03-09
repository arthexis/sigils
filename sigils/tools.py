import io
import functools
import contextlib
import multiprocessing as mp
from typing import Union, Text, Iterator, Callable, Any, Optional, TextIO

from . import contexts
from .parser import spool, parse, SigilContextTransformer
from .errors import SigilError, OnError


import logging
logger = logging.getLogger(__name__)


def splice(
        text: Union[str, TextIO],
        on_error: str = OnError.DEFAULT,
        default: Optional[str] = "",
        recursion: int = 6,
        serializer: Callable[[Any], str] = str,
) -> str:
    """
    Resolve all sigils found in text, using the local context, and return the
    resulting text. If the text contains no sigils, it's returned unchanged.

    :param text: The text containing sigils.
    :param on_error: What to do if a sigil cannot be resolved:
        OnError.DEFAULT: Replace the sigil with the default value (the default).
        OnError.IGNORE: Ignore the error and leave the sigil in the text output.
        OnError.RAISE: Raise a SigilError detailing the problem.
        OnError.REMOVE: Remove the sigil from the text output.
    :param serializer: Function used to serialize the sigil value, defaults to str.
    :param default: Value to use when the sigils resolves to None, defaults to "".
    :param max_recursion: If greater than zero, and the output of a resolved sigil
        contains other sigils, resolve them as well until no sigils remain or
        until max_recursion is reached (default is 6).

    >>> # Resolving sigils using context:
    >>> with context(ENV={"HOST": "localhost"}, USER="arthexis"}):
    >>>     resolve("Connect to [ENV.HOST] as [USER]")
    'Connect to localhost as arthexis'
    """

    if not isinstance(text, str):
        text = text.read()
    if not (sigils := set(spool(text))):
        return text  # Not an error, just do nothing
    results = []

    if len(sigils) > 1:
        with mp.Pool() as pool:
            results = pool.starmap(splice, [
                (sigil, on_error, default, recursion)
                for sigil in sigils
            ])
    else:
        sigil = sigils.pop()
        try:
            # By using a lark transformer, we parse and resolve
            # each sigil in isolation and in a single pass
            tree = parse(sigil[1:-1])
            transformer = SigilContextTransformer(contexts._threadlocal.context)
            value = transformer.transform(tree).children[0]
            # logger.debug("Sigil '%s' resolved to '%s'.", sigil, value)
            if value is not None:
                fragment = serializer(value)
                if recursion > 0:
                    fragment = splice(
                        fragment,
                        on_error,
                        default,
                        recursion=(recursion - 1)
                    )
                text = text.replace(sigil, fragment)
        except Exception as ex:
            if on_error == OnError.RAISE:
                raise SigilError(sigil) from ex
            elif on_error == OnError.REMOVE:
                text = text.replace(sigil, "")
            elif on_error == OnError.DEFAULT:
                text = text.replace(sigil, str(default))

    if results:
        for sigil, result in zip(sigils, results):
            text = text.replace(sigil, result)
    return text


# Resolve is a version of splice that defaults to recursion = 0
resolve = functools.partial(splice, recursion=0)


def vanish(
        text: str,
        pattern: Union[Text, Iterator],
) -> tuple[str, tuple[str]]:
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

    sigils = list(spool(text))
    _iter = (iter(pattern) if isinstance(pattern, Iterator) 
             else iter(pattern * len(sigils)))
    for sigil in set(sigils):
        text = (text.replace(sigil, str(next(_iter)) or sigil))
    return text, tuple(sigils)


def unvanish(
        text: str,
        sigils: tuple[str] | list[str],
        pattern: Union[Text, Iterator],
) -> str:
    """
    De-replace all patterns in the text with sigils.

    :param text: The text with the pattern to be replaced.
    :param sigils: A list of sigils to be replaced in.
    :param pattern: A text or iterator used to replace the patterns with.
    :return: A tuple of: de-replaced text.
    """

    _iter = (iter(pattern) if isinstance(pattern, Iterator) 
             else iter(pattern * len(sigils)))
    for sigil in set(sigils):
        text = (text.replace(str(next(_iter)) or sigil, sigil))
    return text


def execute(
        code: str,
        on_error: str = OnError.DEFAULT,
        default: Optional[str] = "",
        recursion_limit: int = 6,
        _locals: Optional[dict[str, Any]] = None,
        _globals: Optional[dict[str, Any]] = None,
) -> Union[str, None]:
    """Execute a Python code block after resolving any sigils appearing in it.
    If the executed code block prints to stdout, it's output is returned. 
    If the code prints to stderr, a SigilError is raised.
    If the code block looks like an expression, it's value is returned.
    If the code block looks like a statement, None is returned.
    If the code block contains no sigils, it's not executed and None is returned.
    """
    if not set(spool(code)):
        return None
    _code = splice(code, on_error=on_error, default=default, 
                    recursion=recursion_limit)
    with contextlib.redirect_stdout(io.StringIO()) as f:
        with contextlib.redirect_stderr(io.StringIO()) as err:
            exec(_code, _globals, _locals)
            if err.getvalue():
                raise SigilError(err.getvalue())
    return f.getvalue()


__all__ = ["spool", "splice", "execute", "vanish", "unvanish", "resolve"]
