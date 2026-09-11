"""Regression tests for continuation resolution across Sigil path segments."""

from sigils import Sigil


class _Formatter:
    def normalize(self):
        return "method"


def test_scalar_continues_into_root_callable():
    context = {
        "name": "Alice Smith",
        "slugify": lambda value: value.lower().replace(" ", "-"),
    }

    assert Sigil("[name.slugify]").solve(context) == "alice-smith"


def test_sequence_continues_into_root_callable():
    context = {
        "items": [2, 3, 5],
        "total": sum,
    }

    assert Sigil("[items.total]").solve(context) == "10"


def test_object_method_takes_precedence_over_root_callable():
    context = {
        "formatter": _Formatter(),
        "normalize": lambda value: "root",
    }

    assert Sigil("[formatter.normalize]").solve(context) == "method"


def test_bound_method_can_continue_into_root_callable():
    context = {
        "name": " Alice Smith ",
        "slugify": lambda value: value.lower().replace(" ", "-"),
    }

    assert Sigil("[name.strip.slugify]").solve(context) == "alice-smith"


def test_continuation_can_chain_multiple_root_callables():
    context = {
        "number": 4,
        "double": lambda value: value * 2,
        "label": lambda value: f"value={value}",
    }

    assert Sigil("[number.double.label]").solve(context) == "value=8"


def test_normal_mapping_traversal_wins_over_root_callable():
    context = {
        "record": {"normalize": "mapping"},
        "normalize": lambda value: "root",
    }

    assert Sigil("[record.normalize]").solve(context) == "mapping"


def test_unresolved_segment_remains_unresolved_without_callable():
    context = {
        "name": "Alice",
        "missing": "not callable",
    }

    assert Sigil("[name.missing]").solve(context) == "[name.missing]"
