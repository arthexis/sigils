import os
import sys
import uuid
import math
import json
import random
import socket
import collections
import contextlib
import threading
from typing import Generator, Optional, Any

import logging
logger = logging.getLogger(__name__)

from .funcs import FUNCTION_MAP


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


FUNCTION_MAP = {
    "SYS": System(),
    **FUNCTION_MAP
}


class ThreadLocal(threading.local):
    def __init__(self):
        # These will be the default filters and objects
        global FUNCTION_MAP
        self.context = collections.ChainMap(FUNCTION_MAP)
        # Add default context sources and thread local variables here


_threadlocal = ThreadLocal()


# Function that recursively changes the keys of a dictionary
# to uppercase. This is used to make the context dictionary uniform.
def _upper_keys(d):
    if isinstance(d, dict):
        return {k.upper(): _upper_keys(v) for k, v in d.items()}
    else:
        return d


def _load_context_file(filename):
    filename = os.path.abspath(filename)
    if filename.endswith(".toml"):
        import tomllib
        with open(filename, 'r') as f:
            return _upper_keys(tomllib.loads(f.read()))
    elif filename.endswith(".json"):
        import json
        with open(filename, 'r') as f:
            return _upper_keys(json.loads(f.read()))
    elif filename.endswith(".yaml") or filename.endswith(".yml"):
        import yaml
        with open(filename, 'r') as f:
            return _upper_keys(yaml.safe_load(f.read()))
    elif filename.endswith(".ini"):
        import configparser
        config = configparser.ConfigParser()
        config.read(filename)
        file_data = {}
        for section in config.sections():
            file_data[section.upper()] = _upper_keys(dict(config.items(section)))
        return file_data
    elif filename.endswith(".env"):
        import dotenv
        return _upper_keys(dotenv.dotenv_values(filename))
    else:
        raise ValueError(f"Unknown file type: {filename}")


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
                file_data = _load_context_file(arg)
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
