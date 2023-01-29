import os
import uuid
import collections
import contextlib
import threading

from lru import LRU

# Try to import django.utils.timezone as datetime if exists
# If it doesn't, just normal datetime
try:
    from django.utils import timezone as datetime
except ImportError:
    from datetime import datetime


class System:
    """Used for the SYS default context."""

    class _Env:
        def __getitem__(self, item):
            return os.getenv(item.upper())

    _env = _Env()

    @property
    def env(self):
        return System._env
    
    @property
    def now(self):
        return datetime.now()

    @property
    def today(self):
        return datetime.today()

    @property
    def uuid(self):
        return str(uuid.uuid4()).replace('-', '')


class ThreadLocal(threading.local):
    def __init__(self):
        self.ctx = collections.ChainMap({
            "SYS": System(),
            "JOIN": lambda o, s: (s or "").join(str(i) for i in o),
            "REAL": lambda x: float(x) if "." in x else int(x),
            "FOLD": lambda x: str(x).casefold(),
            "LOWER": lambda x: str(x).lower(),
            "UPPER": lambda x: str(x).upper(),
            "TRIM": lambda x: str(x).strip(),
            "STRIP": lambda x: str(x).strip(),
            "OR": lambda x, y: x or y,
            "AND": lambda x, y: x and y,
            "NOT": lambda x: not x,
            "BOOL": lambda x: bool(x),
            "INT": lambda x: int(x),
            "FLOAT": lambda x: float(x),
            "STR": lambda x: str(x),
            "LEN": lambda x: len(x),
            "LIST": lambda x: list(x),
            "TUPLE": lambda x: tuple(x),
            "SET": lambda x: set(x),
            "DICT": lambda x: dict(x),
            "REVERSE": lambda x: x[::-1],
            "SORT": lambda x: sorted(x),
        })
        self.lru = LRU(128)


_local = ThreadLocal()


@contextlib.contextmanager
def context(*args, **kwargs) -> None:
    """Update the local context used for resolving sigils temporarily.

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
