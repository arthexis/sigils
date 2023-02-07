
from ..transforms import *  # Module under test
from ..contexts import local_context


def test_join_list():
    with local_context(LIST=["Hello", "World"]):
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

    with local_context(CUSTOM=custom_func):
        assert resolve("[CUSTOM]") == "Hello World"


# Test chaining two functions
def test_chained_functions():
    def custom_func():
        return "Hello World"

    with local_context(CUSTOM=custom_func):
        assert resolve("[CUSTOM.UPPER]") == "HELLO WORLD"


# Test a custom two parameter function
def test_two_parameter_function():
    def func_add_to_self(self, other):
        return self + other

    with local_context(APPEND=func_add_to_self, HELLO="Hello "):
        assert resolve("[HELLO.APPEND='World']") == "Hello World"


# Test a custom filter that does nothing
def test_noop_filter():
    def custom_func(self):
        return self
    
    with local_context(NOOP=custom_func, HELLO="Hello World"):
        assert resolve("[HELLO.NOOP]") == "Hello World"


# Test a custom function with a default parameter
def test_default_parameter_function():
    def concat_func(self, other="World"):
        return f"{self}{other}"

    with local_context(CONCAT=concat_func, HELLO="Hello "):
        assert resolve("[HELLO.CONCAT]") == "Hello World"


# Test splitting a string
def test_split_string():
    # TODO: Fix this test
    with local_context(HELLO="Hello World"):
        assert resolve("[HELLO.SPLIT.ITEM=0]") == "Hello"


# Test ADD function
def test_add_function():
    with local_context(HELLO="Hello ", WORLD="World"):
        assert resolve("[HELLO.ADD=WORLD]") == "Hello WORLD"


# Test RSPLIT function
def test_rsplit_function():
    with local_context(HELLO="Hello World"):
        assert resolve("[HELLO.SPLIT.ITEM=1]") == "World"


# Test extracting the second word from a string
def test_second_word():
    with local_context(HELLO="Hello Foo Bar"):
        assert resolve("[HELLO.WORD=1]") == "Foo"


# Test EQ and NEQ
def test_eq():
    with local_context(A=1, B=2):
        assert resolve("[A.EQ=1]") == "True"
        assert resolve("[A.EQ=2]") == "False"
        assert resolve("[A.NEQ=1]") == "False"
        assert resolve("[A.NEQ=2]") == "True"


# Test LT and GT
def test_lt_gt():
    with local_context(A=1, B=2):
        assert resolve("[A.LT=2]") == "True"
        assert resolve("[A.LT=1]") == "False"
        assert resolve("[A.GT=2]") == "False"
        assert resolve("[A.GT=0]") == "True"


# Test LTE and GTE
def test_lte_gte():
    with local_context(A=1, B=2):
        assert resolve("[A.LTE=2]") == "True"
        assert resolve("[A.LTE=1]") == "True"
        assert resolve("[A.LTE=0]") == "False"
        assert resolve("[A.GTE=2]") == "False"
        assert resolve("[A.GTE=1]") == "True"
        assert resolve("[A.GTE=0]") == "True"


# Test arithmetic
def test_arithmetic():
    with local_context(A=1, B=2):
        assert resolve("[A.ADD=[B]]") == "3"
        assert resolve("[A.SUB=[B]]") == "-1"
        assert resolve("[A.MUL=[B]]") == "2"
        assert resolve("[A.DIV=[B]]") == "0.5"
        assert resolve("[A.MOD=[B]]") == "1"


# Test setting and reading environment variables
def test_env():
    import os
    os.environ["FOO"] = "BAR"
    assert resolve("[SYS.ENV.FOO]") == "BAR"


# Test executing a block of python code
def test_execute_python_code():
    code = """
def func():
    print("Hello [USERPARAM]")
    return "Hello World"
func()
    """
    import io
    import contextlib
    # Capture stdout
    stdout = io.StringIO()
    with contextlib.redirect_stdout(stdout):
        with local_context(USERPARAM="World"):
            execute(code)
    assert stdout.getvalue() == "Hello World\n"


