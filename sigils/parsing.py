import logging
import io
from typing import Iterator, Mapping, Union, TextIO

import lark

logger = logging.getLogger(__name__)

GRAMMAR = r"""
    start    : sigil
    sigil    : "[" node ("." node)* "]"
    node     : CNAME ["=" arg]
    arg      : sigil
             | "'" /[^']+/ "'"
             | "\"" /[^"]+/ "\""
             | integer
             | CNAME
             | "True"
             | "False"
             | "None"
             | null
    null     : "NULL"
    integer  : INT

    %import common.CNAME
    %import common.INT
    %import common.WS
    %ignore WS
"""

_parser = lark.Lark(GRAMMAR)
parse = _parser.parse


def extract(
        text: Union[str, TextIO],
        left: str = "[",
        right: str = "]"
) -> Iterator[str]:
    """Generator that extracts top-level sigils from text.

    :param text: The text to extract the sigils from.
    :param left: Left delimiter, defaults to "[".
    :param right: Right delimiter, defaults to "]".
    :return: An iterable of sigil strings.

    >>> # Extract simple sigils from text
    >>> list(extract("Connect to [ENV.HOST] as [USER]"))
    ['[ENV.HOST]', '[USER]']

    >>> # Nested sigils are allowed, only top level is extracted
    >>> list(extract("Environ [ENV=[SRC]]"))
    ['[ENV=[SRC]]']

    >>> # Malformed sigils are not extracted (no errors raised).
    >>> list(extract("Connect to [ENV.HOST as USER"))
    []
    """

    buffer = []
    depth = 0
    if isinstance(text, str): text = io.StringIO(text)
    while char := text.read(1):
        if char == left: depth += 1
        if depth > 0:
            buffer.append(char)
            if char == right:
                depth -= 1
                if depth == 0:
                    token = ''.join(buffer)
                    if token.count("'") % 2 == 0 and token.count('"') % 2 == 0:
                        yield token
                    buffer.clear()


def _try_get_item(obj, key):
    try:
        return obj[key]
    except (KeyError, TypeError):
        return None


def _try_call(func, *args) -> Union[None, str]:
    if callable(func):
        logger.debug(f"Callable, try with {args=}.")
        args = tuple(arg for arg in args if arg is not None)
        if args: return func(*args)
        else: return func()
    else:
        logger.debug(f"Non-callable {func}.")
        return None


def _try_manager(model):
    return getattr(model, "objects", None)


class ContextTransformer(lark.Transformer):

    def __init__(self, context: Mapping):
        super().__init__()
        self.ctx = context

    def _ctx_lookup(self, key):
        logger.debug(f"Context lookup: {key}")
        try:
            value = self.ctx[key]
            logger.debug(f"Found {type(value)} {value}")
            return value
        except KeyError as ex:
            logger.debug(f"{key} not found.")
            raise ex

    @lark.v_args(inline=True)
    def sigil(self, *nodes):
        stack = list(nodes[::-1])
        logger.debug(f"Resolving node stack {stack}.")
        # Process the first node (root)
        name, param = stack.pop()
        if isinstance(param, lark.Token): param = param.value
        if not (target := self._ctx_lookup(name)):
            logger.debug(f"Root '{name}' not found in context.")
            return
        if manager := _try_manager(target):
            # We don't want to find managers after the first node
            logger.debug("Found 'objects' attribute, treat as Django Model.")
            if param:
                logger.debug(f"Search by pk={param}")
                if instance := manager.get(pk=param):
                    logger.debug(f"Found instance with pk={param}.")
                    target = instance
                elif instance := manager.get_by_natural_key(param):
                    logger.debug(f"Found instance with natural key: {param}.")
                    target = instance
            else:
                try:
                    logger.debug("Lookahead into the next node.")
                    name, param = stack.pop()
                    if param:
                        target = manager.get(**{name.casefold(): param})
                    else:
                        stack.append((name, param))
                except IndexError:
                    pass  # Nothing to append back, pop failed
                except RuntimeError as ex:
                    stack.append((name, param))
        elif callable(target):
            logger.debug("Root is callable, try to call.")
            target = _try_call(target, param)
        elif param:
            if isinstance(param, int):
                param -= 1
            if value := _try_get_item(target, param):
                logger.debug(f"Lookup param '{param}' found.")
                target = value
        else:
            logger.debug(f"No param, no lookup. Root: {name=}.")
        # Process additional nodes after the first (root)
        logger.debug(f"Target: {target} {stack=}.")
        while stack:
            # TODO: Use a match statement?
            name, param = stack.pop()
            if isinstance(param, lark.Token): param = param.value
            logger.debug(f"Consume {name=} {param=}.")
            if field := _try_get_item(target, name):
                # This finds items only (not attributes)
                logger.debug(f"Field (exact) {name} found in {target}.")
                target = _try_call(field, param) or field
            elif field := getattr(target, name.casefold(), None):
                # Casefold is used to find Model fields, properties and methods
                logger.debug(f"Field (casefold) {name} found in {target}.")
                target = _try_call(field, param) or field
            elif _filter := self._ctx_lookup(name):
                logger.debug(f"Filter {name} found in context.")
                # Filters are called with the current target as the first arg
                # This will fail if the function does not accept parameters
                target = _try_call(_filter, target, param)
            else:
                logger.debug("Unable to consume complete sigil at {name} in {target}.") 
        return target

    # Flatten nodes (otherwise a Tree is returned)
    @lark.v_args(inline=True)
    def node(self, key, arg=None):
        return [str(key), arg]

    # Flatten node args (otherwise a Tree is returned)
    @lark.v_args(inline=True)
    def arg(self, value=None):
        return value

    @lark.v_args(inline=True)
    def integer(self, value=None):
        return int(value)

    null: bool = lambda self, _: ""
