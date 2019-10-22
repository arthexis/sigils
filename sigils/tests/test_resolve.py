import pytest

from ..resolve import *  # Module under test
from ..exceptions import SigilError


def test_resolve_attributes():
    """Attributes are resolved by case-folding."""

    class Env:
        def __init__(self, host):
            self.ssh_hostname = host

    hostname = "localhost"
    context = {"ENV": Env(hostname)}
    text = "[ENV.SSH_HOSTNAME]"

    result = resolve(text, context)
    assert result == hostname


def test_suppress_errors_default():
    context = {"USER": "arthexis"}
    sigil = "[ENV]"
    result = resolve(sigil, context)
    assert result == sigil


def test_resolve_without_extract():
    context = {"USER": "arthexis"}
    sigil = "[USER]"
    result = resolve(sigil, context)
    assert result == "arthexis"


def test_no_sigils_found():
    context = {"USER": "arthexis"}
    text = "This contains no sigils"
    result = resolve(text, context)
    assert result == text


def test_call_lambda_missing_required_arg():
    context = {"A": lambda p, x: x}
    result = resolve("[A]", context, required=True)
    assert result is None


def test_call_lambda_error():
    context = {"A": lambda p, x: x / 0}
    with pytest.raises(SigilError):
        resolve("[A='Test']", context, required=True)


def test_call_lambda():
    context = {"A": lambda p, x: x}
    result = resolve("[A='Test']", context, required=True)
    assert result == "Test"


def test_using_item_subscript():
    context = {"A": {"B": "C"}}
    result = resolve("[A.B]", context)
    assert result == "C"


def test_item_subscript_key_not_found():
    context = {"A": {"B": "C"}}
    with pytest.raises(SigilError):
        resolve("[A.C]", context, required=True)


def test_required_key_not_in_context():
    context = {"USER": "arthexis"}
    with pytest.raises(SigilError):
        result = resolve("[ENV]", context, required=True)


def test_null_arg():
    result = resolve("[IF=NULL]", required=True)
    assert result == ""


def test_embedded_resolve():
    result = resolve("[A] World!", {"A": "Hello"})
    assert result == "Hello World!"
