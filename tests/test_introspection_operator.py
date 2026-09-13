from __future__ import annotations

from sigils import Sigil
from sigils.secret import Secret


def explain(template: str, context: dict) -> dict:
    return Sigil(template).explain(context)


def test_explain_projects_successful_resolution() -> None:
    metadata = explain(
        "[service.client.status]",
        {"service": {"client": {"status": "ready"}}},
    )

    assert metadata["resolved"] is True
    assert metadata["expression"] == "service.client.status"
    assert metadata["value_type"] == "str"
    assert metadata["protected"] is False
    assert metadata["failure_reason"] is None
    assert metadata["resolution_mode"] == "call"
    assert metadata["trace"][-1]["kind"] == "traversal_complete"


def test_explain_reports_unresolved_expression() -> None:
    metadata = explain("[missing]", {})

    assert metadata["resolved"] is False
    assert metadata["value_type"] is None
    assert metadata["failure_reason"] in {"missing_member", "no_interpretation"}
    assert any(event["outcome"] == "missing" for event in metadata["trace"])


def test_explain_reuses_candidate_trace() -> None:
    metadata = explain(
        "[service.slugify]",
        {
            "service": {"slugify": "member"},
            "slugify": lambda value: str(value).upper(),
        },
    )

    assert metadata["resolved"] is True
    assert metadata["selected_interpretation"] == "member"
    kinds = [event["kind"] for event in metadata["candidates"]]
    assert "candidate_created" in kinds
    assert "candidate_selected" in kinds


def test_explain_never_reveals_secret_payload() -> None:
    metadata = explain("[token]", {"token": Secret("swordfish")})

    assert metadata["resolved"] is True
    assert metadata["protected"] is True
    assert metadata["value_type"] == "Secret"
    assert "swordfish" not in repr(metadata)


def test_explain_does_not_replay_descriptor_lookup() -> None:
    class Service:
        def __init__(self) -> None:
            self.reads = 0

        @property
        def status(self) -> str:
            self.reads += 1
            return "ready"

    service = Service()
    metadata = explain("[service.status]", {"service": service})

    assert metadata["resolved"] is True
    assert service.reads == 1
    assert metadata["memo"]["misses"] >= 1


def test_explain_output_is_plain_serializable_metadata() -> None:
    metadata = explain("[value]", {"value": 42})

    assert metadata["resolved"] is True
    assert metadata["value_type"] == "int"
    assert isinstance(metadata["trace"], list)
    assert isinstance(metadata["memo"], dict)


def test_explain_rejects_multi_expression_templates() -> None:
    sigil = Sigil("[left] [right]")

    try:
        sigil.explain({"left": 1, "right": 2})
    except ValueError as error:
        assert "exactly one Sigil" in str(error)
    else:
        raise AssertionError("expected explain() to reject multiple expressions")
