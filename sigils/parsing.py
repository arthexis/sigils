import logging
from typing import Iterator, Mapping

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


def extract(text: str, left: str = "[", right: str = "]") -> Iterator[str]:
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
    for char in text:
        if char == left:
            depth += 1
        if depth > 0:
            buffer.append(char)
            if char == right:
                depth -= 1
                if depth == 0:
                    yield ''.join(buffer)
                    buffer.clear()


def _get(obj, key):
    try:
        return obj[key]
    except (KeyError, TypeError):
        return None


def _manager(model):
    return getattr(model, "objects", None)


class ContextTransformer(lark.Transformer):

    def __init__(self, context: Mapping):
        super().__init__()
        self.ctx = context

    def _ctx_lookup(self, key):
        logger.debug(f"Context lookup: {key}")
        try:
            value = self.ctx[key]
            logger.debug(f"Found: {value}")
            return value
        except KeyError as ex:
            logger.debug(f"Not in context.")
            raise ex

    @lark.v_args(inline=True)
    def sigil(self, *nodes):
        stack: list = list(nodes[::-1])
        logger.debug(f"Resolving node stack {stack}.")
        # Process the first node
        name, param = stack.pop()
        target = self._ctx_lookup(name)
        if manager := _manager(target):
            logger.debug("Found 'objects' attribute, treat as Model.")
            if param:
                logger.debug(f"Search by pk={param}")
                if instance := manager.get(pk=param):
                    logger.debug(f"Found instance with pk={param}.")
                    target = instance
                else:
                    if instance := manager.get_by_natural_key(param):
                        logger.debug(f"Found instance with natural key: {param}.")
                        target = instance
            else:
                try:
                    logger.debug("Lookahead into the next node.")
                    name, param = stack.pop()
                    if param:
                        target = manager.get(**{name.casefold(): param})
                except IndexError:
                    pass  # Nothing to append back, pop failed
                except RuntimeError as ex:
                    stack.append((name, param))
        elif callable(target):
            target = target(param) if param else target()
        elif param:
            if value := _get(target, param):
                logger.debug(f"Lookup param '{param}' found.")
                target = value
        # Process additional nodes after the first
        while stack:
            name, param = stack.pop()
            if field := getattr(target, name.casefold(), None):
                logger.debug(f"Field {name} found in {target}.")
                target = field
            else:
                if not param:
                    target = target[name]
                else:
                    if func := self._ctx_lookup(name):
                        logger.debug(f"Filter {name} found in context.")
                        target = func
            if callable(target):
                target = target(param) if param else target()
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
