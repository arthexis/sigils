import logging
import typing

import lark

logger = logging.getLogger(__name__)

GRAMMAR = r"""
    start    : sigil
    sigil    : "[" node ("." node)* "]"
    node     : CNAME ["=" arg]
    arg      : sigil
             | "'" /[^']+/ "'"
             | "\"" /[^"]+/ "\""
             | NUMBER
             | null
    null     : "NULL"

    %import common.CNAME
    %import common.NUMBER
    %import common.WS
    %ignore WS
"""

_parser = lark.Lark(GRAMMAR)
parse = _parser.parse


def extract(text: str, left: str = "[", right: str = "]") -> typing.Iterator[str]:
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


class ContextTransformer(lark.Transformer):

    def __init__(self, context: typing.Mapping):
        super().__init__()
        self.ctx = context

    @lark.v_args(inline=True)
    def sigil(self, *nodes):
        parent = None  # The current left object
        for node in nodes:
            selector, reference = node

            # We don't have a left object yet: its the first node
            # Try finding the object in context only
            if not parent:
                try:
                    parent = self.ctx[selector]
                    if callable(parent):
                        parent = parent(None, reference)
                    elif reference:
                        if hasattr(parent, reference):
                            parent = getattr(parent, reference, None)
                        else:
                            parent = parent[reference]
                except KeyError as ex:
                    if not reference:
                        logger.error(f"Key {selector} not in context.")
                    else:
                        logger.error(f"Key {selector} not defined for {reference}.")
                    raise ex
                continue

            obj = None  # The current object
            called = False
            try:
                # We have a left object already: this is not the first node
                # Try the following in order:
                # 1. Find the object as an item in the left
                # 2. Find the object as an attribute of the left
                # 3. Find a function with that name in the context and
                #    call it by passing the left as the argument
                # Make the result the new left object
                try:
                    obj = parent[selector]
                except KeyError as ex:
                    logger.error("Key %s not an item in %s", selector, obj)
                    obj = None
                    raise ex
                except TypeError as ex:
                    folded = selector.casefold()
                    if folded.startswith("_"):
                        obj = None
                        raise AttributeError("Key %s cannot be private", selector)
                    try:
                        obj = getattr(parent, folded)
                        continue
                    except AttributeError as ex:
                        if callable(func := self.ctx.get(selector, None)):
                            logger.debug("Apply %s to %s", func, obj)
                            called = True
                            obj = func(parent, reference)
                            continue
                        logger.error("Key %s not an attribute of %s", selector, obj)
                        obj = None
                        raise ex
            finally:
                # Ensure callable nodes are always called once
                # If not callable, but right was provided, subscript
                if not called:
                    if callable(obj):
                        if hasattr(obj, '__self__'):
                            # Already a bound method, don't pass left
                            obj = obj(reference)
                        else:
                            # Unbound method or function, pass left
                            obj = obj(parent, reference)
                    elif reference is not None:
                        obj = obj[reference]

                # Last, make the current object the new left
                parent = obj

        return parent

    # Flatten nodes (otherwise a Tree is returned)
    @lark.v_args(inline=True)
    def node(self, key, arg=None):
        return [str(key), arg]

    # Flatten node args (otherwise a Tree is returned)
    @lark.v_args(inline=True)
    def arg(self, value=None):
        return value

    null: bool = lambda self, _: ""
