from sigils import Sigil


def test_interpretation_expansion_budget_aborts_ambiguous_traversal() -> None:
    sigil = Sigil("[service.slugify]")
    sigil.max_interpretation_expansions = 1
    context = {
        "service": {"slugify": "member"},
        "slugify": lambda value: str(value).upper(),
    }

    assert sigil.solve(context) == "[service.slugify]"

    metadata = sigil.explain(context)
    assert metadata["resolved"] is False
    assert metadata["failure_reason"] == "interpretation_expansions_budget_exceeded"
    assert metadata["budget"] == {
        "exhausted": True,
        "reason": "interpretation_expansions",
    }
    events = [event for event in metadata["trace"] if event["kind"] == "complexity_budget"]
    assert len(events) == 1
    assert events[0]["outcome"] == "exhausted"


def test_semantic_step_budget_aborts_before_unbounded_trace_growth() -> None:
    sigil = Sigil("[service.client.status]")
    sigil.max_semantic_steps = 1
    context = {"service": {"client": {"status": "ready"}}}

    assert sigil.solve(context) == "[service.client.status]"

    metadata = sigil.explain(context)
    assert metadata["resolved"] is False
    assert metadata["failure_reason"] == "semantic_steps_budget_exceeded"
    assert metadata["budget"]["reason"] == "semantic_steps"
    assert len(metadata["trace"]) <= 2
    assert metadata["trace"][-1]["kind"] == "complexity_budget"


def test_default_budgets_do_not_change_normal_resolution() -> None:
    sigil = Sigil("[service.client.status]")
    context = {"service": {"client": {"status": "ready"}}}

    assert sigil.solve(context) == "ready"

    metadata = sigil.explain(context)
    assert metadata["resolved"] is True
    assert metadata["budget"] == {"exhausted": False, "reason": None}
