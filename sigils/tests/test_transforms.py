import pytest

from ..transforms import *  # Module under test
from ..exceptions import SigilError


def test_sigil_with_simple_context():
    with context(USER="arthexis"):
        assert resolve("[USER]", raise_errors=True) == "arthexis"


def test_sigil_with_mapping_context():
    with context(ENV={"PROD": "localhost"}):
        assert resolve("[ENV='PROD']") == "localhost"


def test_callable_no_param():
    with context(FUNC=lambda: "Test"):
        assert resolve("[FUNC]") == "Test"


def test_class_static_attribute():

    class Entity:
        code = "Hello"

    with context(ENT=Entity()):
        assert resolve("[ENT.CODE]") == "Hello"


def test_sigil_with_index():
    with context(ENV=["hello", "world"]):
        assert resolve("[ENV=1]") == "world"


def test_suppress_errors_by_default():
    with context(USER="arthexis"):
        assert resolve("[NOT_USER]") == "[NOT_USER]"


def test_attributes_casefold():

    class Env:
        def __init__(self, host):
            self.ssh_hostname = host

    hostname = "localhost"
    with context(ENV=Env(hostname)):
        assert resolve("[ENV.SSH_HOSTNAME]") == hostname


def test_no_sigils_in_text():
    assert resolve("No sigils") == "No sigils"


def test_call_lambda_same():
    with context(SAME=lambda arg: arg):
        assert resolve("[SAME='Test']", raise_errors=True) == "Test"


def test_call_lambda_same_alt_quotes():
    with context(SAME=lambda arg: arg):
        assert resolve('[SAME="Test"]', raise_errors=True) == "Test"


def test_call_lambda_reverse():
    with context(REVERSE=lambda arg: arg[::-1]):
        assert resolve("[REVERSE='Test']", raise_errors=True) == "tseT"


def test_call_lambda_error():
    with context(DIVIDE_BY_ZERO=lambda arg: arg / 0):
        with pytest.raises(SigilError):
            resolve("[DIVIDE_BY_ZERO=1]", raise_errors=True)


def test_item_subscript():
    with context(A={"B": "C"}):
        assert resolve("[A.B]", raise_errors=True) == "C"


def test_item_subscript_key_not_found():
    with context(A={"B": "C"}):
        with pytest.raises(SigilError):
            resolve("[A.C]", raise_errors=True)


def test_required_key_not_in_context():
    with context(USER="arthexis"):
        with pytest.raises(SigilError):
            resolve("[ENV]", raise_errors=True)


def test_replace_duplicated():
    text = "User: [USER], Manager: [USER], Company: [ORG]"
    text, sigils = replace(text, "%s")
    assert text == "User: %s, Manager: %s, Company: %s"
    assert sigils == ("[USER]", "[USER]", "[ORG]")
