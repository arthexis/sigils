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


def test_space_separated_segments_mean_traversal_not_hyphen_alias():
    context = {
        "start": {"server": "nested"},
        "start_server": "alias",
    }

    assert Sigil("[start server]").solve(context) == "nested"
    assert Sigil("[start.server]").solve(context) == "nested"


def test_space_does_not_manufacture_a_hyphenated_identifier():
    context = {"start_server": "started"}

    assert Sigil("[start server]").solve(context) == "[start server]"
    assert Sigil("[start-server]").solve(context) == "started"


def test_mixed_spaces_and_dots_follow_the_same_traversal():
    context = {"root": {"alpha": {"beta": "value"}}}

    assert Sigil("[root alpha.beta]").solve(context) == "value"
    assert Sigil("[root.alpha beta]").solve(context) == "value"


def test_normal_space_traversal_wins_over_key_alias():
    context = {
        "health": {"errors": "nested"},
        "health_errors": "alias",
    }

    assert Sigil("[health errors]").solve(context) == "nested"


def test_percent_inside_sigil_is_a_regular_key_character():
    context = {"root": {"%server": "percent"}}

    assert Sigil("[root.%server]").solve(context) == "percent"


def test_double_brackets_are_literal_constants():
    context = {"start_server": "started"}

    assert Sigil("[[start_server]]").solve(context) == "start_server"
    assert (
        Sigil("before [[server start]] after").solve(context)
        == "before server start after"
    )


def test_double_bracket_constant_and_sigil_can_share_template():
    context = {"start_server": "started"}

    assert (
        Sigil("[[start_server]] [start_server]").solve(context)
        == "start_server started"
    )
