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
