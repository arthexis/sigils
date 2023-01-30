
from ..transforms import *  # Module under test
from ..contexts import context


def test_join_list():
    with context(LIST=["Hello", "World"]):
        assert resolve("[LIST.JOIN=', ']") == "Hello, World"


def test_sys_context_env_path():
    import os
    assert resolve("[SYS.ENV.PATH]") == os.getenv("PATH")


def test_sys_uuid_length():
    assert len(resolve("[SYS.UUID]")) == 32


# Test adding a custom function to context
def test_custom_function():
    def custom_func():
        return "Hello World"

    with context(CUSTOM=custom_func):
        assert resolve("[CUSTOM]") == "Hello World"


# Test chaining two functions
def test_chained_functions():
    def custom_func():
        return "Hello World"

    with context(CUSTOM=custom_func):
        assert resolve("[CUSTOM.UPPER]") == "HELLO WORLD"


# Test a custom two parameter function
def test_two_parameter_function():
    def func_add_to_self(self, other):
        return self + other

    with context(APPEND=func_add_to_self, HELLO="Hello "):
        assert resolve("[HELLO.APPEND='World']") == "Hello World"


# Test a custom filter that does nothing
# TODO: Fix this test
def test_noop_filter():
    def custom_func(self):
        return self
    
    with context(NOOP=custom_func, HELLO="Hello World"):
        assert resolve("[HELLO.NOOP]") == "Hello World"


# Test a custom function with a default parameter
# TODO: Fix this test
def test_default_parameter_function():
    def concat_func(self, other="World"):
        return f"{self}{other}"

    with context(CONCAT=concat_func, HELLO="Hello "):
        assert resolve("[HELLO.CONCAT]") == "Hello World"
