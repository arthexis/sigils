import os
import datetime
import pytest

from ..tools import *  # Module under test
from ..errors import SigilError
from ..sigils import Sigil
from ..contexts import local_context, global_context


def test_sigil_with_simple_context():
    with local_context(USER="arthexis"):
        assert splice("[[USER]]") == "arthexis"


def test_sigil_with_mapping_context():
    with local_context(ENV={"PROD": "localhost"}):
        assert splice("[[ENV='PROD']]") == "localhost"


def test_callable_no_param():
    with local_context(FUNC=lambda: "Test"):
        assert splice("[[FUNC]]") == "Test"


def test_class_static_attribute():
    class Entity:
        code = "Hello"

    with local_context(ENT=Entity()):
        assert splice("[[ENT.CODE]]") == "Hello"


def test_sigil_with_natural_index():
    with local_context(ENV=["hello", "world"]):
        assert splice("[[ENV=1]]") == "world"


def test_replace_missing_sigils_with_default():
    with local_context(USER="arthexis"):
        assert splice("[[NOT_USER]]", default="ERROR") == "ERROR"


def test_remove_missing_sigils():
    with local_context(USER="arthexis"):
        assert not splice("[[NOT_USER]]", on_error=OnError.REMOVE)


def test_attributes_casefold():
    class Env:
        def __init__(self, host):
            self.ssh_hostname = host

    hostname = "localhost"
    with local_context(ENV=Env(hostname)):
        assert splice("[[ENV.SSH_HOSTNAME]]") == hostname


def test_no_sigils_in_text():
    assert splice("No sigils") == "No sigils"


def test_call_lambda_same():
    with local_context(SAME=lambda arg: arg):
        assert splice("[[SAME='Test']]") == "Test"


def test_call_lambda_same_alt_quotes():
    with local_context(SAME=lambda arg: arg):
        assert splice('[[SAME="Test"]]') == "Test"


def test_call_lambda_reverse():
    with local_context(REVERSE=lambda arg: arg[::-1]):
        assert splice("[[REVERSE='Test']]") == "tseT"


def test_call_lambda_error():
    with local_context(DIVIDE_BY_ZERO=lambda arg: arg / 0):
        with pytest.raises(SigilError):
            splice("[[DIVIDE_BY_ZERO=1]]", on_error=OnError.RAISE)


def test_subitem_subscript():
    with local_context(A={"B": "C"}):
        assert splice("[[A.B]]") == "C"


def test_item_subscript_key_not_found():
    with local_context(A={"B": "C"}):
        with pytest.raises(SigilError):
            splice("[[A.C]]", on_error=OnError.RAISE)


def test_required_key_not_in_context():
    with local_context(USER="arthexis"):
        with pytest.raises(SigilError):
            splice("[[ENVXXX]]", on_error=OnError.RAISE)


def test_replace_duplicated():
    # TODO: Fix this test
    text = "User: [[U]], Manager: [[U]], Company: [[ORG]]"
    text, sigils = vanish(text, "X")
    assert sigils == ("[[U]]", "[[U]]", "[[ORG]]")
    assert text == "User: X, Manager: X, Company: X"

def test_resolve_simple_whitespace():
    with local_context({"ENV": "local"}):
        assert splice("[[ ENV ]]") == "local"


def test_resolve_dotted_whitespace():
    with local_context({"ENV": {"USER": "admin"}}):
        assert splice("[[ ENV  .  USER ]]") == "admin"


def test_resolve_recursive_one_level():
    with local_context(Y="[[X]]", X=10):
        assert splice("[[Y]]", max_recursion=1) == "10"


def test_sigil_helper_class():
    sigil = Sigil("Hello [[PLACE]]")
    assert sigil(PLACE="World") == "Hello World"


# Test converstion to json works with the standard library
# using the Sigil class
def test_json_conversion():
    import json
    with local_context(USER="arthexis"):
        sigil = Sigil("Hello [[USER]]")
        assert json.dumps(sigil) == '"Hello [[USER]]"'


# RJGO New functionatlity: using lists in the context
def test_item_subscript():
    with local_context(A=[1,2,3]):
        assert splice("[[A.ITEM=2]]") == "3"




# Test global_context
def test_global_context():
    global_context()["USER"] = "arthex1s"
    assert splice("[[USER]]") == "arthex1s"


# Test global_context
def test_global_context_set_key():
    global_context("USERA", "arthexe4s")
    assert splice("[[USERA]]") == "arthexe4s"

