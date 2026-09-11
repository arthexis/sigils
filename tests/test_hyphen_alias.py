"""Regression tests for hyphen/underscore Sigil lookup equivalence."""

from sigils import Sigil


def test_hyphenated_sigil_resolves_underscore_mapping_key():
    context = {"local_node": "ready"}

    assert Sigil("[local-node]").solve(context) == "ready"
    assert Sigil("[local_node]").solve(context) == "ready"


class _Status:
    local_node = "ready"


def test_hyphenated_sigil_resolves_underscore_attribute():
    context = {"status": _Status()}

    assert Sigil("[status.local-node]").solve(context) == "ready"
    assert Sigil("[status.local_node]").solve(context) == "ready"
