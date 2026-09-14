from __future__ import annotations

from sigils import Sigil
from sigils.secret import Secret
from sigils.sigil.placement import (
    IncomingIndex,
    SPREAD,
    parse_placement_marker,
    route_incoming,
)


def _collect(*values):
    return tuple(values)


def test_route_incoming_defaults_to_front_insertion() -> None:
    assert route_incoming(["tail"], ["A", "B"]) == ["A", "B", "tail"]


def test_route_incoming_reorders_with_one_based_selectors() -> None:
    assert route_incoming(
        [IncomingIndex(2), IncomingIndex(1)],
        ["A", "B", "C", "D"],
    ) == ["B", "A"]


def test_route_incoming_spreads_only_unselected_values() -> None:
    assert route_incoming(
        [IncomingIndex(3), SPREAD, IncomingIndex(1)],
        ["A", "B", "C", "D"],
    ) == ["C", "B", "D", "A"]


def test_route_incoming_allows_duplicate_numeric_selectors() -> None:
    assert route_incoming(
        [IncomingIndex(2), IncomingIndex(2)],
        ["A", "B"],
    ) == ["B", "B"]


def test_zero_selector_is_invalid_for_call_placement() -> None:
    try:
        parse_placement_marker("[0]")
    except ValueError as exc:
        assert "one-based" in str(exc)
    else:
        raise AssertionError("[0] must not be a call-placement selector")


def test_explicit_pass_uses_default_front_insertion() -> None:
    context = {
        "values": ("A", "B"),
        "collect": _collect,
        "tail": "tail",
    }
    result = Sigil("[values - collect : tail]").results(context)
    assert result["values - collect : tail"] == ("A", "B", "tail")


def test_explicit_pass_numeric_selectors_reorder_incoming_values() -> None:
    context = {"values": ("A", "B", "C", "D"), "collect": _collect}
    expression = "values - collect : [2] : [1]"
    result = Sigil(f"[{expression}]").results(context)
    assert result[expression] == ("B", "A")


def test_explicit_pass_wildcard_uses_unselected_remainder() -> None:
    context = {"values": ("A", "B", "C", "D"), "collect": _collect}
    expression = "values - collect : [3] : [*] : [1]"
    result = Sigil(f"[{expression}]").results(context)
    assert result[expression] == ("C", "B", "D", "A")


def test_explicit_selector_disables_implicit_insertion() -> None:
    context = {
        "values": ("A", "B", "C", "D"),
        "collect": _collect,
        "tail": "tail",
    }
    expression = "values - collect : [2] : tail"
    result = Sigil(f"[{expression}]").results(context)
    assert result[expression] == ("B", "tail")


def test_out_of_range_selector_keeps_call_unresolved() -> None:
    context = {"values": ("A", "B"), "collect": _collect}
    expression = "values - collect : [3]"
    assert expression not in Sigil(f"[{expression}]").results(context)


def test_multiple_wildcards_keep_call_unresolved() -> None:
    context = {"values": ("A", "B"), "collect": _collect}
    expression = "values - collect : [*] : [*]"
    assert expression not in Sigil(f"[{expression}]").results(context)


def test_selected_secret_protects_call_result() -> None:
    context = {
        "values": ("public", Secret("secret")),
        "collect": _collect,
    }
    expression = "values - collect : [2]"
    result = Sigil(f"[{expression}]").results(context)
    assert result[expression] == Secret.REDACTED
