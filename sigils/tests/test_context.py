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


def test_hide():
    context = {"A": "password"}
    result = resolve("[A.HIDE]", context, required=True)
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

