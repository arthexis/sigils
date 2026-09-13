from __future__ import annotations

import json

from sigils import Sigil
from sigils.secret import Secret


def explain(template: str, context: dict) -> dict:
    return json.loads(Sigil(template).solve(context))


def test_question_operator_projects_successful_resolution() -> None:
    metadata = explain(
        "[service.client.status ?]",
        {"service": {"client": {"status": "ready"}}},
    )

    assert metadata["resolved"] is True
    assert metadata["expression"] == "service.client.status"
    assert metadata["value_type"] == "str"
    assert metadata["protected"] is False
    assert metadata["failure_reason"] is None
    assert metadata["resolution_mode"] == "call"
    assert metadata["trace"][-1]["kind"] == "traversal_complete"


def test_question_operator_explains_unresolved_expression() -> None:
    metadata = explain("[missing ?]", {})

    assert metadata["resolved"] is False
    assert metadata["value_type"] is None
    assert metadata["failure_reason"] in {"missing_member", "no_interpretation"}
    assert any(event["outcome"] == "missing" for event in metadata["trace"])


def test_question_operator_reuses_candidate_trace() -> None:
    metadata = explain(
        "[service.slugify ?]",
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


def test_question_operator_never_reveals_secret_payload() -> None:
    metadata_text = Sigil("[token ?]").solve({"token": Secret("swordfish")})
    metadata = json.loads(metadata_text)

    assert metadata["resolved"] is True
    assert metadata["protected"] is True
    assert metadata["value_type"] == "Secret"
    assert "swordfish" not in metadata_text


def test_question_operator_does_not_replay_descriptor_lookup() -> None:
    class Service:
        def __init__(self) -> None:
            self.reads = 0

        @property
        def status(self) -> str:
            self.reads += 1
            return "ready"

    service = Service()
    metadata = explain("[service.status ?]", {"service": service})

    assert metadata["resolved"] is True
    assert service.reads == 1
    assert metadata["memo"]["misses"] >= 1


def test_question_operator_output_is_stable_json() -> None:
    rendered = Sigil("[value ?]").solve({"value": 42})
    metadata = json.loads(rendered)

    assert rendered == json.dumps(metadata, sort_keys=True, separators=(",", ":"))
