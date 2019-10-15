import pytest

from ..context import set_context
from ..resolve import resolve
from ..exceptions import SigilError


def test_set_context():
    set_context("USER", "arthexis")
    result = resolve("[USER]")
    assert result == "arthexis"


def test_using_item_subscript():
    set_context("A", {"B": "C"})
    result = resolve("[A.B]")
    assert result == "C"


def test_item_subscript_key_not_found():
    set_context("A", {"B": "C"})
    with pytest.raises(SigilError):
        resolve("[A.C]", required=True)


def test_call_lambda():
    set_context("A", lambda x: x)
    result = resolve("[A='Test']", required=True)
    assert result == "Test"


def test_call_lambda_error():
    set_context("A", lambda x: x / 0)
    with pytest.raises(SigilError):
        resolve("[A='Test']", required=True)


def test_call_lambda_missing_required_arg():
    set_context("A", lambda x: x)
    result = resolve("[A]", required=True)
    assert result

