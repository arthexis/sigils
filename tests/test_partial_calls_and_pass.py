"""Tests for partial callable resolution and explicit pass chaining."""

from sigils import SafeNamespace, Sigil


def test_partial_callable_stays_unrendered_until_value_is_passed():
    def between(value, minimum, maximum):
        return minimum <= value <= maximum

    context = {
        "between": between,
        "minimum": 1,
        "maximum": 10,
    }

    assert Sigil("[between.minimum.maximum]").solve(context) == (
        "[between.minimum.maximum]"
    )


def test_explicit_pass_completes_partial_callable():
    def between(value, minimum, maximum):
        return minimum <= value <= maximum

    context = {
        "value": 5,
        "between": between,
        "minimum": 1,
        "maximum": 10,
    }

    assert Sigil("[value - between.minimum.maximum]").solve(context) == "True"


def test_spaces_can_replace_dots_inside_explicit_pass_target():
    def between(value, minimum, maximum):
        return minimum <= value <= maximum

    context = {
        "value": 5,
        "between": between,
        "minimum": 1,
        "maximum": 10,
    }

    assert Sigil("[value - between minimum maximum]").solve(context) == "True"


def test_explicit_pass_chains_left_to_right():
    context = {
        "value": "  Alice Smith  ",
        "strip": lambda value: value.strip(),
        "slug": lambda value: value.lower().replace(" ", "-"),
    }

    assert Sigil("[value - strip - slug]").solve(context) == "alice-smith"


class _Record:
    def normalize(self):
        return "member"


def test_explicit_pass_disambiguates_root_callable_from_member():
    record = _Record()
    context = {
        "record": record,
        "normalize": lambda value: "root" if value is record else "wrong",
    }

    assert Sigil("[record.normalize]").solve(context) == "member"
    assert Sigil("[record - normalize]").solve(context) == "root"


def test_hyphenated_identifier_is_not_an_explicit_pass():
    context = {"start_server": "started"}

    assert Sigil("[start-server]").solve(context) == "started"


def test_space_never_stands_in_for_explicit_pass():
    context = {
        "value": "alice",
        "upper": lambda value: value.upper(),
    }

    assert Sigil("[value upper]").solve(context) == "ALICE"
    assert Sigil("[value - upper]").solve(context) == "ALICE"


def test_explicit_pass_does_not_invoke_unapproved_safe_namespace_callable():
    calls = []

    def dangerous(value):
        calls.append(value)
        return "should-not-run"

    context = {
        "value": "secret",
        "node": SafeNamespace({"dangerous": dangerous}),
    }

    assert Sigil("[value - node.dangerous]").solve(context) == (
        "[value - node.dangerous]"
    )
    assert calls == []
