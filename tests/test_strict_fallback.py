from sigils import Sigil


def test_double_pipe_keeps_false_boolean() -> None:
    assert Sigil("[value||:fallback]") % {"value": False} == "False"


def test_double_pipe_keeps_zero() -> None:
    assert Sigil("[value||:fallback]") % {"value": 0} == "0"


def test_double_pipe_keeps_empty_string() -> None:
    assert Sigil("[value||:fallback]") % {"value": ""} == ""


def test_double_pipe_keeps_empty_list_and_dict() -> None:
    assert Sigil("[value||:fallback]") % {"value": []} == "[]"
    assert Sigil("[value||:fallback]") % {"value": {}} == ""


def test_double_pipe_falls_back_on_none() -> None:
    assert Sigil("[value||:fallback]") % {"value": None} == "fallback"


def test_double_pipe_falls_back_on_empty_sets() -> None:
    assert Sigil("[value||:fallback]") % {"value": set()} == "fallback"
    assert Sigil("[value||:fallback]") % {"value": frozenset()} == "fallback"


def test_double_pipe_falls_back_on_unresolved_value() -> None:
    assert Sigil("[missing||:fallback]") % {} == "fallback"


def test_single_pipe_remains_falsey_fallback() -> None:
    assert Sigil("[value|:fallback]") % {"value": False} == "fallback"
    assert Sigil("[value|:fallback]") % {"value": 0} == "fallback"
    assert Sigil("[value|:fallback]") % {"value": ""} == "fallback"


def test_mixed_fallback_operators_apply_left_to_right() -> None:
    context = {"first": False, "second": 0, "third": "ready"}
    assert Sigil("[first||second|third]") % context == "False"
    assert Sigil("[first|second||third]") % context == "0"
