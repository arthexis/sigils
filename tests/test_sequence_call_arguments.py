from __future__ import annotations

from sigils import Secret, Sigil


def test_call_argument_tuple_split_ignores_nested_commas() -> None:
    sigil = Sigil("[value]")
    context = {"a": 1, "b": 2}

    assert sigil._resolve_call_argument("a, (b, a)", context) == (
        1,
        "(b, a)",
    )


def test_structured_call_protects_nested_secret_tuple_items() -> None:
    sigil = Sigil("[value]")
    context = {"token": Secret("swordfish"), "public": "visible"}

    result = sigil._run_structured_call(
        lambda values: values[0],
        ["token, public"],
        context,
    )

    assert isinstance(result, Secret)
    assert result.reveal() == "swordfish"
