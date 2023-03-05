
from ..tools import *  # Module under test
from ..contexts import local_context


def test_join_list():
    with local_context(LIST=["Hello", "World"]):
        assert splice("[[LIST.JOIN=', ']]") == "Hello, World"

# Test that a string has no sigils with spool
def test_no_sigils_in_big_string():
    with local_context(HELLO="Hello", WORLD="World"):
        assert not any(spool("Hello World"))

# Test adding a custom function to context
def test_custom_function():
    def custom_func():
        return "Hello World"

    with local_context(CUSTOM=custom_func):
        assert splice("[[CUSTOM]]") == "Hello World"

# Test chaining two functions
def test_chained_functions():
    def custom_func():
        return "Hello World"

    with local_context(CUSTOM=custom_func):
        assert splice("[[CUSTOM.UPPER]]") == "HELLO WORLD"


# Test a custom two parameter function
def test_two_parameter_function():
    def func_add_to_self(self, other):
        return self + other

    with local_context(APPEND=func_add_to_self, HELLO="Hello "):
        assert splice("[[HELLO.APPEND='World']]") == "Hello World"


# Test a custom filter that does nothing
def test_noop_filter():
    def custom_func(self):
        return self
    
    with local_context(NOOP=custom_func, HELLO="Hello World"):
        assert splice("[[HELLO.NOOP]]") == "Hello World"


# Test a custom function with a default parameter
def test_default_parameter_function():
    def concat_func(self, other="World"):
        return f"{self}{other}"

    with local_context(CONCAT=concat_func, HELLO="Hello "):
        assert splice("[[HELLO.CONCAT]]") == "Hello World"


# Test splitting a string
def test_split_string():
    # TODO: Fix this test
    with local_context(HELLO="Hello World"):
        assert splice("[[HELLO.SPLIT.ITEM=0]]") == "Hello"


# Test ADD function
def test_add_function():
    with local_context(HELLO="Hello ", WORLD="World"):
        assert splice("[[HELLO.ADD=WORLD]]") == "Hello WORLD"


# Test RSPLIT function
def test_rsplit_function():
    with local_context(HELLO="Hello World"):
        assert splice("[[HELLO.SPLIT.ITEM=1]]") == "World"


# Test extracting the second word from a string
def test_second_word():
    with local_context(HELLO="Hello Foo Bar"):
        assert splice("[[HELLO.WORD=1]]") == "Foo"


# Test EQ and NEQ
def test_eq():
    with local_context(A=1, B=2):
        assert splice("[[A.EQ=1]]") == "True"
        assert splice("[[A.EQ=2]]") == "False"
        assert splice("[[A.NE=1]]") == "False"
        assert splice("[[A.NE=2]]") == "True"


# Test LT and GT
def test_lt_gt():
    with local_context(A=1, B=2):
        assert splice("[[A.LT=2]]") == "True"
        assert splice("[[A.LT=1]]") == "False"
        assert splice("[[A.GT=2]]") == "False"
        assert splice("[[A.GT=0]]") == "True"


# Test LTE and GTE
def test_lte_gte():
    with local_context(A=1, B=2):
        assert splice("[[A.LE=2]]") == "True"
        assert splice("[[A.LE=1]]") == "True"
        assert splice("[[A.LE=0]]") == "False"
        assert splice("[[A.GE=2]]") == "False"
        assert splice("[[A.GE=1]]") == "True"
        assert splice("[[A.GE=0]]") == "True"


# Test arithmetic
def test_arithmetic():
    with local_context(A=1):
        assert splice("[[A.ADD=2]]") == "3"
        assert splice("[[A.SUB=2]]") == "-1"
        assert splice("[[A.MUL=2]]") == "2"
        assert splice("[[A.DIV=2]]") == "0.5"
        assert splice("[[A.MOD=2]]") == "1"


# Test executing a block of python code
def test_execute_python_code():
    code = """
def func():
    print("Hello [[USERPARAM]]")
func()
    """
    with local_context(USERPARAM="World"):
        assert execute(code) == "Hello World\n"


# Test executing a block of python code with a return value
# and using it as a condition
def test_execute_python_code_with_return():
    condition = "if '[[USERPARAM]]' == 'World': print('Yes')"
    with local_context(USERPARAM="World"):
        assert execute(condition) == "Yes\n"

