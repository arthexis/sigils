from __future__ import annotations

from sigils import Sigil


def test_nested_selector_brackets_stay_inside_outer_expression() -> None:
    expression = "values - collect : [2] : [*] : [1]"
    sigil = Sigil(f"[{expression}]")

    matches = list(sigil.pattern.finditer(sigil.template))
    assert len(matches) == 1
    assert matches[0].group("expression") == expression
