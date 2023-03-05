import os
import sys
import uuid
import json
import base64
import urllib.parse
import collections
import contextlib
import threading
from typing import Generator, Optional, Any

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
    def uuid(self): return str(uuid.uuid4()).replace('-', '')

    @property
    def pid(self): return os.getpid()

    @property
    def cwd(self): return os.getcwd()

    @property
    def os(self): return os.name

    @property
    def python(self): return sys.executable

    @property
    def argv(self): return sys.argv

    @property
    def version(self): return sys.version


class ThreadLocal(threading.local):
    def __init__(self):
        # These will be the default filters and objects
        self.ctx = collections.ChainMap({
            "SYS": System(),
            "NUM": lambda x: float(x) if "." in x else int(x),
            "UPPER": lambda x: str(x).upper(),
            "LOWER": lambda x: str(x).lower(),
            "TRIM": lambda x: str(x).strip(),
            "STRIP": lambda x: str(x).strip(),
            "SLUG": lambda x: str(x).replace(" ", "-"),
            "ZFILL": lambda x, y: str(x).zfill(y),
            "F": lambda x, *args, **kwargs: x.format(*args, **kwargs),
            "STYLE": lambda x: dict(i.split(":") for i in x.split(";") if i),
            "JOIN": lambda o, s: (s or "").join(str(i) for i in o),
            "SPLIT": lambda x, y: str(x).split(y),
            "OR": lambda x, y: x or y,
            "AND": lambda x, y: x and y,
            "NOT": lambda x: not x,
            "BOOL": lambda x: bool(x),
            "INT": lambda x: int(x),
            "FLOAT": lambda x: float(x),
            "TUPLE": lambda x: tuple(x),
            "LIST": lambda x: list(x),
            "SET": lambda x: set(x),
            "JSON": lambda x: json.dumps(x),
            "B64": lambda x: base64.b64encode(x),
            "B64D": lambda x: base64.b64decode(x),
            "URL": lambda x: urllib.parse.quote(x),
            "URLD": lambda x: urllib.parse.unquote(x),
            "LEN": lambda x: len(x),
            "REV": lambda x: x[::-1],
            "SORT": lambda x: sorted(x),
            "ITEM": lambda x, y: x[y],
            "KEY": lambda x, y: x[y],
            "ATTR": lambda x, y: getattr(x, y),
            "ANY": lambda x: any(x),
            "ALL": lambda x: all(x),
            "NONE": lambda x: not any(x),
            "SUM": lambda x: sum(x),
            "MIN": lambda x: min(x),
            "MAX": lambda x: max(x),
            "AVG": lambda x: sum(x) / len(x),
            "ABS": lambda x: abs(x),
            "ROUND": lambda x, y: round(x, y or 0),
            "CEIL": lambda x: int(x) + 1,
            "FLOOR": lambda x: int(x),
            "TRUNC": lambda x: int(x),
            "MOD": lambda x, y: x % y,
            "ADD": lambda x, y: x + y,
            "SUB": lambda x, y: x - y,
            "MUL": lambda x, y: x * y,
            "DIV": lambda x, y: x / y,
            "FDIV": lambda x, y: x // y,
            "EQ": lambda x, y: str(x) == str(y),
            "NE": lambda x, y: str(x) != str(y),
            "LT": lambda x, y: x < y,
            "LE": lambda x, y: x <= y,
            "GT": lambda x, y: x > y,
            "GE": lambda x, y: x >= y,
            "IN": lambda x, y: x in y,
            "CONTAINS": lambda x, y: y in x,
            "FIRST": lambda x: x[0],
            "LAST": lambda x: x[-1],
            "HEAD": lambda x, y: x[:y],
            "TAIL": lambda x, y: x[-y:],
            "TYPE": lambda x: type(x).__name__,
            "FLAT": lambda x: [i for j in x for i in j],
            "ESC": lambda x: x.replace("\\", "\\\\").replace('"', '\\"'),
            "UNIQ": lambda x: list(set(x)),
            "ZIP": lambda x, y: list(zip(x, y)),
            "WORD": lambda x, y: x.split()[y],
        })
        self.lru = LRU(128)
        # Add default context sources and thread local variables here


_local = ThreadLocal()


@contextlib.contextmanager
def local_context(*args, **kwargs) -> Generator[collections.ChainMap, None, None]:
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


def global_context(key: Optional[str] = None, value: Any = None) -> Any:
    """Get or set a global context value.
    
    :param key: The key to get or set.
    :param value: The value to set.
    :return: The value of the key or the entire context.

    >>> # Get the entire context
    >>> global_context()
    >>> # Get a value from the context
    >>> global_context("TEXT")
    >>> # Set a value in the context
    >>> global_context("TEXT", "hello world")
    """
    global _local
    if key and value is None:
        return _local.ctx[key]
    elif key and value is not None:
        _local.ctx[key] = value
    return _local.ctx


__all__ = ["local_context", "global_context"]	
