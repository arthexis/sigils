import logging
from typing import ChainMap

from lark import Transformer, v_args

__all__ = ["SigilResolver"]

logger = logging.getLogger(__name__)


class SigilResolver(Transformer):

    def __init__(self, context: ChainMap):
        super().__init__()
        self.ctx = context or {}

    @v_args(inline=True)
    def sigil(self, *nodes):
        parent = None  # The current parent object
        for node in nodes:
            key, arg = node

            # We don't have a parent object yet: its the first node
            # Try finding the object in context only
            if not parent:
                try:
                    if callable(parent := self.ctx[key]):
                        parent = parent(None, arg)
                except KeyError as ex:
                    logger.error("Key %s not in context", key)
                    obj = None
                    raise ex
                continue

            obj = None  # The current object
            called = False
            try:
                # We have a parent object already: this is not the first node
                # Try the following in order:
                # 1. Find the object as an item in the parent
                # 2. Find the object as an attribute of the parent
                # 3. Find a function with that name in the context and
                #    call it by passing the parent as the argument
                # Make the result the new parent object
                try:
                    obj = parent[key]
                except KeyError as ex:
                    logger.error("Key %s not an item in %s", key, obj)
                    obj = None
                    raise ex
                except TypeError as ex:
                    folded = key.casefold()
                    if folded.startswith("_"):
                        obj = None
                        raise AttributeError("Key %s cannot be private", key)
                    try:
                        obj = getattr(parent, folded)
                        continue
                    except AttributeError as ex:
                        if callable(func := self.ctx.get(key, None)):
                            logger.debug("Apply %s to %s", func, obj)
                            called = True
                            obj = func(parent, arg)
                            continue
                        logger.error("Key %s not an attribute of %s", key, obj)
                        obj = None
                        raise ex
            finally:
                # Ensure callable nodes are always called once
                # If not callable, but arg was provided, subscript
                if not called:
                    if callable(obj):
                        if hasattr(obj, '__self__'):
                            # Already a bound method, don't pass parent
                            obj = obj(arg)
                        else:
                            # Unbound method or function, pass parent
                            obj = obj(parent, arg)
                    elif arg is not None:
                        obj = obj[arg]

                # Last, make the current object the new parent
                parent = obj

        return parent

    # Flatten nodes (otherwise a Tree is returned)
    @v_args(inline=True)
    def node(self, key, arg=None):
        return [str(key), arg]

    # Flatten node args (otherwise a Tree is returned)
    @v_args(inline=True)
    def arg(self, value=None):
        return value

    null: bool = lambda self, _: ""
