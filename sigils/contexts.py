import os
import sys
import uuid
import math
import json
import random
import base64
import socket
import urllib.parse
import collections
import contextlib
import threading
from typing import Generator, Optional, Any

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

    # TODO: Check user privileges before accessing SYS 
    # TODO: Missing tests

    class _Env:
        def __getitem__(self, item):
            return os.getenv(item.upper())
        
        def __str__(self):
            return str(','.join(os.environ.keys()))

    _env = _Env()

    @property
    def env(self): return System._env
            
    @property
    def args(self): return sys.argv[1:]

    @property
    def now(self): return datetime.now()

    @property
    def today(self): return datetime.now().date()

    @property
    def time(self): return datetime.now().time()

    @property
    def uuid(self): return str(uuid.uuid4()).replace('-', '')

    @property
    def rng(self): return random.random()

    @property
    def pid(self): return os.getpid()

    @property   
    def pi(self): return math.pi

    @property
    def os(self): return os.name

    @property
    def arch(self): return sys.platform

    @property
    def host(self): return socket.gethostname()

    @property
    def ip(self): return socket.gethostbyname(socket.gethostname())

    @property
    def user(self): return os.getlogin()

    @property
    def home(self): return os.path.expanduser("~")

    @property
    def python(self): return sys.executable

    @property
    def py_ver(self): return sys.version

    @property
    def sig_ver(self): 
        # TODO: Missing tests
        with open(os.path.join(os.path.dirname(__file__), "..", "pyproject.toml")) as f:
            return json.loads(f.read())["project"]["version"]
        
    @property
    def pwd(self): return os.getcwd()

    @property
    def cwd(self): return os.getcwd()
        
    @property
    def tmp(self): return os.path.join(os.getcwd(), "tmp")

class ThreadLocal(threading.local):
    def __init__(self):
        # These will be the default filters and objects
        self.context = collections.ChainMap({
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
            "SIG": lambda x: f"[[{x}]]",
            "WORD": lambda x, y: x.split()[y],
        })
        # Add default context sources and thread local variables here


_threadlocal = ThreadLocal()


# Function that recursively changes the keys of a dictionary
# to uppercase. This is used to make the context dictionary uniform.
def _upper_keys(d):
    if isinstance(d, dict):
        return {k.upper(): _upper_keys(v) for k, v in d.items()}
    else:
        return d



@contextlib.contextmanager
def context(*args, **kwargs) -> Generator[collections.ChainMap, None, None]:
    """Context manager that updates the local context used by sigils.

    :param args: A tuple of context sources.
    :param kwargs: A mapping of context keys to values or functions.

    >>> # Add to context using kwargs
    >>> with context(TEXT="hello world") as ctx:
    >>>     assert ctx["TEXT"] == "hello world"
    """
    global _threadlocal
    _threadlocal.context = _threadlocal.context.new_child(kwargs)

    for arg in args:
        if isinstance(arg, dict):
            _threadlocal.context = _threadlocal.context.new_child(arg)
        elif callable(arg):
            _threadlocal.context = _threadlocal.context.new_child(arg())
        elif isinstance(arg, str):
            if "=" in arg:
                key, value = arg.split("=", 1)
                _threadlocal.context[str(key).upper()] = value  # type: ignore
            else:
                file_data = {}
                # Convert arg to an absolute path
                arg = os.path.abspath(arg)
                if arg.endswith(".toml"):
                    import tomllib
                    with open(arg, 'r') as f:
                        file_data = _upper_keys(tomllib.loads(f.read()))
                elif arg.endswith(".json"):
                    import json
                    with open(arg, 'r') as f:
                        file_data = _upper_keys(json.loads(f.read()))
                elif arg.endswith(".yaml") or arg.endswith(".yml"):
                    import yaml
                    with open(arg, 'r') as f:
                        file_data = _upper_keys(yaml.safe_load(f.read()))
                elif arg.endswith(".ini"):
                    import configparser
                    config = configparser.ConfigParser()
                    config.read(arg)
                    # Loop over every section and add it to the context
                    for section in config.sections():
                        file_data[section.upper()] = _upper_keys(dict(config.items(section)))
                elif arg.endswith(".env"):
                    import dotenv
                    file_data = _upper_keys(dotenv.dotenv_values(arg))
                else:
                    raise ValueError(f"Unknown file type: {arg}")
                _threadlocal.context = _threadlocal.context.new_child(file_data)
            
    yield _threadlocal.context
    _threadlocal.context = _threadlocal.context.parents


def global_context(key: Optional[str] = None, value: Any = None) -> Any:
    """Get or set a global context value.
    You should normally use the context() function instead.
    
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
    global _threadlocal
    if key and value is None:
        return _threadlocal.context[key]
    elif key and value is not None:
        _threadlocal.context[key] = value
    return _threadlocal.context


__all__ = ["context", "global_context"]	
