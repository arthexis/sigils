"""Regression tests for Sigil key aliases."""

from sigils import SafeNamespace, Sigil


def test_hyphenated_sigil_resolves_underscore_mapping_key():
    context = {"local_node": "ready"}

    assert Sigil("[local-node]").solve(context) == "ready"
    assert Sigil("[local_node]").solve(context) == "ready"


class _Status:
    local_node = "ready"
    start_server = "started"


def test_hyphenated_sigil_resolves_underscore_attribute():
    context = {"status": _Status()}

    assert Sigil("[status.local-node]").solve(context) == "ready"
    assert Sigil("[status.local_node]").solve(context) == "ready"


def test_two_word_mapping_key_resolves_in_either_order():
    context = {"start_server": "started"}

    assert Sigil("[start_server]").solve(context) == "started"
    assert Sigil("[start-server]").solve(context) == "started"
    assert Sigil("[server_start]").solve(context) == "started"
    assert Sigil("[server-start]").solve(context) == "started"


def test_two_word_callable_resolves_in_either_order():
    context = {"start_server": lambda: "started"}

    assert Sigil("[server-start]").solve(context) == "started"
    assert Sigil("[server_start]").solve(context) == "started"


def test_two_word_attribute_resolves_in_either_order():
    context = {"status": _Status()}

    assert Sigil("[status.server-start]").solve(context) == "started"
    assert Sigil("[status.server_start]").solve(context) == "started"


def test_two_word_safe_namespace_key_resolves_in_either_order():
    context = {"node": SafeNamespace({"start_server": "started"})}

    assert Sigil("[node.server-start]").solve(context) == "started"
    assert Sigil("[node.server_start]").solve(context) == "started"


def test_exact_two_word_key_takes_precedence_over_reversed_alias():
    context = {
        "alpha_beta": "alpha-beta",
        "beta_alpha": "beta-alpha",
    }

    assert Sigil("[alpha-beta]").solve(context) == "alpha-beta"
    assert Sigil("[beta-alpha]").solve(context) == "beta-alpha"


def test_space_separated_two_word_mapping_key_is_alias_fallback():
    context = {"start_server": "started"}

    assert Sigil("[start server]").solve(context) == "started"
    assert Sigil("[server start]").solve(context) == "started"


def test_space_separated_two_word_attribute_is_alias_fallback():
    context = {"status": _Status()}

    assert Sigil("[status.start server]").solve(context) == "started"
    assert Sigil("[status.server start]").solve(context) == "started"


def test_space_separated_safe_namespace_key_is_alias_fallback():
    context = {"node": SafeNamespace({"start_server": "started"})}

    assert Sigil("[node.start server]").solve(context) == "started"
    assert Sigil("[node.server start]").solve(context) == "started"


def test_normal_space_traversal_wins_over_key_alias():
    context = {
        "health": {"errors": "nested"},
        "health_errors": "alias",
    }

    assert Sigil("[health errors]").solve(context) == "nested"


def test_space_alias_does_not_cross_explicit_dot_boundary():
    context = {
        "node_server": {"start": "wrong"},
        "node": {"server_start": "right"},
    }

    assert Sigil("[node.server start]").solve(context) == "right"


def test_ambiguous_space_alias_stays_unresolved():
    context = {
        "root": {
            "alpha_beta": {"gamma": "left"},
            "alpha": {"beta_gamma": "right"},
        }
    }

    template = Sigil("[root.alpha beta gamma]")
    assert template.solve(context) == "[root.alpha beta gamma]"


def test_literal_marker_disables_space_alias_for_that_pair():
    context = {"root": {"server_start": "started"}}

    template = Sigil("[root.%server start]")
    assert template.solve(context) == "[root.%server start]"
