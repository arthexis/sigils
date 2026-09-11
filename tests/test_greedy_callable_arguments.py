"""Regression tests for greedy root-callable argument resolution."""

from sigils import Sigil


def test_root_callable_consumes_one_required_argument():
    context = {
        "double": lambda value: value * 2,
        "number": 4,
    }

    assert Sigil("[double.number]").solve(context) == "8"


def test_root_callable_consumes_multiple_required_arguments():
    context = {
        "add": lambda left, right: left + right,
        "left": 2,
        "right": 3,
    }

    assert Sigil("[add.left.right]").solve(context) == "5"


def test_remaining_segments_traverse_the_call_result():
    def make_record(left, right):
        return {"total": left + right}

    context = {
        "make": make_record,
        "left": 2,
        "right": 3,
    }

    assert Sigil("[make.left.right.total]").solve(context) == "5"


def test_builtin_signature_can_drive_greedy_arguments():
    context = {
        "length": len,
        "items": [1, 2, 3],
    }

    assert Sigil("[length.items]").solve(context) == "3"


def test_optional_parameters_are_not_greedily_consumed():
    def make_record(value="default"):
        return {"value": value}

    context = {
        "make": make_record,
        "value": "context",
    }

    assert Sigil("[make.value]").solve(context) == "[make.value]"


def test_varargs_are_not_greedily_consumed():
    def collect(*values):
        return values

    context = {
        "collect": collect,
        "first": 1,
    }

    assert Sigil("[collect.first]").solve(context) == "[collect.first]"


def test_missing_required_segment_leaves_expression_unresolved():
    context = {
        "add": lambda left, right: left + right,
        "left": 2,
    }

    assert Sigil("[add.left]").solve(context) == "[add.left]"


def test_unresolvable_required_argument_leaves_expression_unresolved():
    context = {
        "add": lambda left, right: left + right,
        "left": 2,
    }

    assert Sigil("[add.left.missing]").solve(context) == "[add.left.missing]"
