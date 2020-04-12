
from ..transforms import *  # Module under test


def test_join_list():
    with context(LIST=["Hello", "World"]):
        assert resolve("[LIST.JOIN=', ']") == "Hello, World"


def test_sys_context_env_path():
    import os
    assert resolve("[SYS.ENV.PATH]") == os.getenv("PATH")
