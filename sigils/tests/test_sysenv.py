import datetime
import os
from ..tools import *  # Module under test


def test_sys_context_env_path():
    import os
    assert splice("[[SYS.ENV.PATH]]") == os.getenv("PATH")


def test_sys_uuid_length():
    assert len(splice("[[SYS.UUID]]")) == 32

# Test setting and reading environment variables
def test_env():
    import os
    os.environ["FOO"] = "BAR"
    assert splice("[[SYS.ENV.FOO]]") == "BAR"


# Check that SYS.ENV is a dictionary with PATH
def test_get_env():
    assert splice("[[SYS.ENV.PATH]]") == os.environ["PATH"]


# Test SYS.NOW produces correct year
def test_get_now():
    assert splice("[[SYS.NOW.YEAR]]") == str(datetime.datetime.now().year)


# Test SYS.PID produces correct pid
def test_get_pid():
    assert splice("[[SYS.PID]]") == str(os.getpid())


# Text getting the correct python executable
def test_get_python():
    import sys
    assert splice("[[SYS.PYTHON]]") == sys.executable