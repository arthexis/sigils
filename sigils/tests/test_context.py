import pytest

from ..context import *   # Module under test
from ..resolve import resolve


def test_set_context():
    set_context("USER", "arthexis")
    result = resolve("[USER]")
    assert result == "arthexis"


def test_join():
    context = {"A": [1, 2, 3]}
    result = resolve("[A.JOIN='-']", context, required=True)
    assert result == "1-2-3"


def test_mask():
    context = {"A": "password"}
    result = resolve("[A.MASK]", context, required=True)
    assert result == "********"


def test_if():
    context = {"A": "hello"}
    result = resolve("[A.IF='hello']", context)
    assert result == "hello"


def test_not_if():
    context = {"A": "hello"}
    result = resolve("[A.IF='world']", context)
    assert result == ""


def test_unary_if():
    context = {"A": "world"}
    result = resolve("[IF='hello']", context)
    assert result == "hello"


def test_null():
    result = resolve("[NULL]")
    assert result == ""


def test_add_binary():
    context = {"A": 2, "B": 3}
    result = resolve("[A.ADD=[B]]", context, required=True)
    assert result == 5


def test_add_unary():
    context = {"A": [1, 2, 3]}
    result = resolve("[A.ADD]", context, required=True)
    assert result == 6
