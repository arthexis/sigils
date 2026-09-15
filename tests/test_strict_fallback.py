from sigils import Sigil


def _context(value):
    return {"value": value, "fallback": "fallback"}


def test_double_pipe_keeps_false_boolean() -> None:
    assert Sigil("[value||fallback]") % _context(False) == "False"


def test_double_pipe_keeps_zero() -> None:
    assert Sigil("[value||fallback]") % _context(0) == "0"


def test_double_pipe_keeps_empty_string() -> None:
    assert Sigil("[value||fallback]") % _context("") == ""


def test_double_pipe_keeps_empty_list_and_dict() -> None:
    assert Sigil("[value||fallback]") % _context([]) == "[]"
    assert Sigil("[value||fallback]") % _context({}) == ""


def test_double_pipe_falls_back_on_none() -> None:
    assert Sigil("[value||fallback]") % _context(None) == "fallback"


def test_double_pipe_falls_back_on_empty_sets() -> None:
    assert Sigil("[value||fallback]") % _context(set()) == "fallback"
    assert Sigil("[value||fallback]") % _context(frozenset()) == "fallback"


def test_double_pipe_falls_back_on_unresolved_value() -> None:
    assert Sigil("[missing||fallback]") % {"fallback": "fallback"} == "fallback"


def test_single_pipe_remains_falsey_fallback() -> None:
    assert Sigil("[value|fallback]") % _context(False) == "fallback"
    assert Sigil("[value|fallback]") % _context(0) == "fallback"
    assert Sigil("[value|fallback]") % _context("") == "fallback"


def test_mixed_fallback_operators_apply_left_to_right() -> None:
    context = {"first": False, "second": 0, "third": "ready"}
    assert Sigil("[first||second|third]") % context == "False"
    assert Sigil("[first|second||third]") % context == "0"
