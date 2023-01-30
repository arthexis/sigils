import os
import uuid
import collections
import contextlib
import threading

from lru import LRU

import logging
logger = logging.getLogger(__name__)

try:
    if not os.environ.get("DJANGO_SETTINGS_MODULE"):
        logger.debug("No DJANGO_SETTINGS_MODULE set, using datetime.datetime")
        raise ImportError
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
    def env(self): return System._env
    
    @property
    def now(self): return datetime.now()

    @property
    def today(self): return datetime.today()

    @property
    def uuid(self): return str(uuid.uuid4()).replace('-', '')

    @property
    def pid(self): return os.getpid()

    @property
    def cwd(self): return os.getcwd()

    @property
    def os_login(self): return os.getlogin()

    @property
    def os_name(self): return os.name


class ThreadLocal(threading.local):
    def __init__(self):
        self.ctx = collections.ChainMap({
            "SYS": System(),
            "JOIN": lambda o, s: (s or "").join(str(i) for i in o),
            "REAL": lambda x: float(x) if "." in x else int(x),
            "NUMBER": lambda x: float(x) if "." in x else int(x),
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
            "TUPLE": lambda x: tuple(x),
            "LIST": lambda x: list(x),
            "SET": lambda x: set(x),
            "DICT": lambda x: dict(x),
            "REVERSE": lambda x: x[::-1],
            "SORT": lambda x: sorted(x),
            "ITEM": lambda x, y: x[y],
            "INDEX": lambda x, y: x.index(y),
            "KEY": lambda x, y: x.get(y),
            "ISO": lambda x: x.isoformat(),
            "ANY": lambda x: any(x),
            "ALL": lambda x: all(x),
            "SUM": lambda x: sum(x),
            "MIN": lambda x: min(x),
            "MAX": lambda x: max(x),
            "FIRST": lambda x: x[0],
            "LAST": lambda x: x[-1],
            "COUNT": lambda x: x.count(),
            "ADD": lambda x, y: x + y,
            "SUB": lambda x, y: x - y,
            "MUL": lambda x, y: x * y,
            "DIV": lambda x, y: x / y,
            "MOD": lambda x, y: x % y,
            "EQ": lambda x, y: x == y,
            "NEQ": lambda x, y: x != y,
            "LT": lambda x, y: x < y,
            "LTE": lambda x, y: x <= y,
            "GT": lambda x, y: x > y,
            "GTE": lambda x, y: x >= y,
            "IN": lambda x, y: x in y,
            "CONTAINS": lambda x, y: y in x,
            "STARTS": lambda x, y: x.startswith(y),	
            "ENDS": lambda x, y: x.endswith(y),
            "TYPE": lambda x: type(x).__name__,
            "IS": lambda x, y: isinstance(x, y),
            "FLAT": lambda x: [i for j in x for i in j],
            "PREFIX": lambda x, y: f"{y}{x}",
            "SUFFIX": lambda x, y: f"{x}{y}",
            "LSPLIT": lambda x, y: str(x).split(y, 1)[0],
            "RSPLIT": lambda x, y: str(x).rsplit(y, 1)[1],
            "SPLIT": lambda x, y: str(x).split(y),
        })
        self.lru = LRU(128)
        # Add default context sources and thread local variables here


_local = ThreadLocal()


@contextlib.contextmanager
def context(*args, **kwargs) -> collections.ChainMap:
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
    logger.debug("Context: %s", _local.ctx)
    yield _local.ctx
    _local.ctx = _local.ctx.parents
    _local.lru.clear()
