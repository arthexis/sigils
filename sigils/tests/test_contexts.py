import os
import datetime
import pytest

from ..transforms import *  # Module under test
from ..errors import SigilError
from ..sigils import Sigil
from ..contexts import local_context


def test_sigil_with_simple_context():
    with local_context(USER="arthexis"):
        assert resolve("[USER]") == "arthexis"


def test_sigil_with_mapping_context():
    with local_context(ENV={"PROD": "localhost"}):
        assert resolve("[ENV='PROD']") == "localhost"


def test_callable_no_param():
    with local_context(FUNC=lambda: "Test"):
        assert resolve("[FUNC]") == "Test"


def test_class_static_attribute():
    class Entity:
        code = "Hello"

    with local_context(ENT=Entity()):
        assert resolve("[ENT.CODE]") == "Hello"


def test_sigil_with_natural_index():
    with local_context(ENV=["hello", "world"]):
        assert resolve("[ENV=1]") == "world"


def test_replace_missing_sigils_with_default():
    with local_context(USER="arthexis"):
        assert resolve("[NOT_USER]", default="ERROR") == "ERROR"


def test_remove_missing_sigils():
    with local_context(USER="arthexis"):
        assert not resolve("[NOT_USER]", on_error=OnError.REMOVE)


def test_attributes_casefold():
    class Env:
        def __init__(self, host):
            self.ssh_hostname = host

    hostname = "localhost"
    with local_context(ENV=Env(hostname)):
        assert resolve("[ENV.SSH_HOSTNAME]") == hostname


def test_no_sigils_in_text():
    assert resolve("No sigils") == "No sigils"


def test_call_lambda_same():
    with local_context(SAME=lambda arg: arg):
        assert resolve("[SAME='Test']") == "Test"


def test_call_lambda_same_alt_quotes():
    with local_context(SAME=lambda arg: arg):
        assert resolve('[SAME="Test"]') == "Test"


def test_call_lambda_reverse():
    with local_context(REVERSE=lambda arg: arg[::-1]):
        assert resolve("[REVERSE='Test']") == "tseT"


def test_call_lambda_error():
    with local_context(DIVIDE_BY_ZERO=lambda arg: arg / 0):
        with pytest.raises(SigilError):
            resolve("[DIVIDE_BY_ZERO=1]", on_error=OnError.RAISE)


def test_item_subscript():
    with local_context(A={"B": "C"}):
        assert resolve("[A.B]") == "C"


def test_item_subscript_key_not_found():
    with local_context(A={"B": "C"}):
        with pytest.raises(SigilError):
            resolve("[A.C]", on_error=OnError.RAISE)


def test_required_key_not_in_context():
    with local_context(USER="arthexis"):
        with pytest.raises(SigilError):
            resolve("[ENVXXX]", on_error=OnError.RAISE)


def test_replace_duplicated():
    text = "User: [USER], Manager: [USER], Company: [ORG]"
    text, sigils = replace(text, "%s")
    assert text == "User: %s, Manager: %s, Company: %s"
    assert sigils == ("[USER]", "[USER]", "[ORG]")


def test_cache_value_is_used():
    with local_context(USER="arthexis"):
        resolve("[USER]")
        with local_context(USER="joe"):
            assert resolve("[USER]") == "arthexis"


def test_cache_value_is_not_used():
    with local_context(USER="arthexis"):
        resolve("[USER]")
        with local_context(USER="joe"):
            assert resolve("[USER]", cache=False) == "joe"


def test_cache_value_is_not_saved():
    with local_context(USER="arthexis"):
        resolve("[USER]", cache=False)
        with local_context(USER="joe"):
            assert resolve("[USER]") == "joe"


def test_resolve_simple_whitespace():
    with local_context({"ENV": "local"}):
        assert resolve("[ ENV ]") == "local"


def test_resolve_dotted_whitespace():
    with local_context({"ENV": {"USER": "admin"}}):
        assert resolve("[ ENV  .  USER ]") == "admin"


def test_resolve_recursive_one_level():
    with local_context(Y="[X]", X=10):
        assert resolve("[Y]", recursion_limit=1) == "10"


def test_sigil_helper_class():
    sigil = Sigil("Hello [PLACE]")
    assert sigil(PLACE="World") == "Hello World"


# Test converstion to json works with the standard library
# using the Sigil class
def test_json_conversion():
    import json
    with local_context(USER="arthexis"):
        sigil = Sigil("Hello [USER]")
        assert json.dumps(sigil) == '"Hello [USER]"'


# RJGO New functionatlity: using lists in the context
def test_item_subscript():
    with local_context(A=[1,2,3]):
        assert resolve("[A.ITEM=2]") == "3"


# Check that SYS.ENV is a dictionary with PATH
def test_get_env():
    assert resolve("[SYS.ENV.PATH]") == os.environ["PATH"]


# Test SYS.NOW produces correct year
def test_get_now():
    assert resolve("[SYS.NOW.YEAR]") == str(datetime.datetime.now().year)


# Test SYS.PID produces correct pid
def test_get_pid():
    assert resolve("[SYS.PID]") == str(os.getpid())


# Text getting the correct python executable
def test_get_python():
    import sys
    assert resolve("[SYS.PYTHON]") == sys.executable

