from __future__ import annotations

from sigils import Sigil
from sigils.secret import Secret


def test_right_arrow_binds_for_later_expression() -> None:
    context = {"value": "ready"}

    assert Sigil("[value -> saved] [saved]").solve(context) == "ready ready"
    assert context == {"value": "ready"}


def test_left_arrow_has_identical_binding_semantics() -> None:
    context = {"value": "ready"}

    assert Sigil("[saved <- value] [saved]").solve(context) == "ready ready"


def test_binding_shadows_root_only_inside_current_evaluation() -> None:
    context = {"value": "new", "saved": "old"}
    sigil = Sigil("[value -> saved] [saved]")

    assert sigil.solve(context) == "new new"
    assert context["saved"] == "old"
    assert sigil._binding_scope is None


def test_binding_preserves_secret_protection_in_results() -> None:
    context = {"token": Secret("swordfish")}

    result = Sigil("[token -> saved] [saved]").results(context)

    assert result["token -> saved"] == Secret.REDACTED
    assert result["saved"] == Secret.REDACTED
    assert "swordfish" not in repr(result)


def test_unresolved_source_does_not_create_binding() -> None:
    sigil = Sigil("[missing -> saved] [saved]")

    assert sigil.solve({}) == "[missing -> saved] [saved]"


def test_invalid_binding_target_remains_unresolved() -> None:
    sigil = Sigil("[value -> bad.name]")

    assert sigil.solve({"value": 1}) == "[value -> bad.name]"


def test_right_arrow_can_continue_through_explicit_pass() -> None:
    context = {
        "value": "hello",
        "persist": lambda value: value.upper(),
    }

    assert (
        Sigil("[value -> normalized - persist] [normalized]").solve(context)
        == "HELLO hello"
    )
