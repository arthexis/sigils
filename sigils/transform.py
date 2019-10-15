import logging

from lark import Transformer, v_args

__all__ = ["SigilResolver"]

logger = logging.getLogger(__name__)


class SigilResolver(Transformer):

    def __init__(self, context: dict = None):
        super().__init__()
        self.ctx = context or {}

    @v_args(inline=True)
    def sigil(self, *nodes):
        obj = None  # The current parent object
        for node in nodes:
            key, arg = node
            try:
                # We don't have a parent object yet: its the first node
                # Try finding the object in context only
                if not obj:
                    try:
                        obj = self.ctx[key]
                    except KeyError as ex:
                        logger.error("Key %s not in context", key)
                        obj = None
                        raise ex
                    continue

                # We have a parent object already: this is not the first node
                # Try the following in order:
                # 1. Find the object as an item in the parent
                # 2. Find the object as an attribute of the parent
                # 3. Find a function with that name in the context and
                #    call it by passing the parent as the argument
                # Make the result the new parent object
                try:
                    obj = obj[key]
                except KeyError as ex:
                    logger.error("Key %s not an item in %s", key, obj)
                    obj = None
                    raise ex
                except TypeError as ex:
                    _key = key.casefold()
                    if key.startswith("_"):
                        obj = None
                        raise AttributeError("Key %s cannot be private", key)
                    try:
                        obj = getattr(obj, _key)
                        continue
                    except AttributeError as ex:
                        func = self.ctx.get(key, None)
                        if callable(func):
                            logger.debug("Apply %s to %s", func, obj)
                            obj = func(obj)
                            continue
                        logger.error("Key %s not an attribute of %s", key, obj)
                        obj = None
                        raise ex
            finally:
                # Ensure callable nodes are always called
                # If not callable, but arg was provided, subscript
                if callable(obj):
                    obj = obj(arg)
                elif arg is not None:
                    obj = obj[arg]
        return obj

    # Flatten nodes (otherwise a Tree is returned)
    @v_args(inline=True)
    def node(self, key, arg=None):
        return [str(key), arg]

    # Flatten node args (otherwise a Tree is returned)
    @v_args(inline=True)
    def arg(self, value=None):
        return value
