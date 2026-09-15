from __future__ import annotations

import re
from dataclasses import replace

from .constants import _UNRESOLVED
from .modes import ResolutionMode
from .pending import PendingCall
from .semantic import BoundedResolutionBeam


class BoundedInterpretationMixin:
    """Route ambiguous whitespace interpretations through the semantic beam."""

    _WHITESPACE_INTERPRETATIONS = (
        ("whitespace_traverse", ResolutionMode.TRAVERSE, 30),
        ("whitespace_call", ResolutionMode.CALL, 20),
        ("legacy_whitespace", None, 10),
    )

    @classmethod
    def _whitespace_score(cls, label):
        for candidate_label, _mode, score in cls._WHITESPACE_INTERPRETATIONS:
            if candidate_label == label:
                return score
        raise ValueError(f"unknown whitespace interpretation: {label}")

    def _rank_whitespace_interpretations(self, session):
        """Return bounded interpretation labels in semantic-precedence order.

        Ranking is side-effect free. Candidate routes are represented by distinct
        temporary semantic states only long enough for the existing bounded beam
        to rank/cap them. Actual resolution happens one route at a time afterward.
        """
        routes = self._WHITESPACE_INTERPRETATIONS
        if not session.budget.consume_expansions(len(routes)):
            session._record_budget_exhaustion(segment=0)
            return ()

        base = session.state
        states = []
        labels = {}
        for label, _mode, score in routes:
            session.record(
                "candidate_created",
                segment=0,
                outcome="available",
                detail=label,
            )
            if session.exhausted:
                return ()
            candidate = replace(
                base,
                score=base.score + score,
                bindings_key=("interpretation", label, base.bindings_key),
            )
            states.append(candidate)
            labels[id(candidate)] = label

        beam = BoundedResolutionBeam(())
        kept, dominated, dropped = beam.classify(states)
        for candidate in dominated:
            session.record(
                "candidate_pruned",
                segment=0,
                outcome="dominated",
                detail=labels[id(candidate)],
            )
        for candidate in dropped:
            session.record(
                "candidate_pruned",
                segment=0,
                outcome="beam_dropped",
                detail=labels[id(candidate)],
            )
        return tuple(labels[id(state)] for state in kept)

    def _run_whitespace_interpretation(self, label, expression, context):
        """Execute exactly one ranked interpretation route."""
        if label == "whitespace_traverse":
            return self._resolve_traversal(
                expression,
                context,
                mode=ResolutionMode.TRAVERSE,
            )
        if label == "whitespace_call":
            return self._resolve_traversal(
                expression,
                context,
                mode=ResolutionMode.CALL,
            )
        if label == "legacy_whitespace":
            return self._resolve_legacy_expression(expression, context)
        raise ValueError(f"unknown whitespace interpretation: {label}")

    def _resolve_single_expression(self, expression, context):
        """Resolve whitespace syntax through ranked, bounded semantic routes."""
        expression = expression.strip()
        if (
            not expression
            or self._split_explicit_pass(expression)
            or not re.search(r"\s", expression)
        ):
            return super()._resolve_single_expression(expression, context)

        session = getattr(self, "_resolution_session", None)
        if session is None:
            return super()._resolve_single_expression(expression, context)

        routes = self._rank_whitespace_interpretations(session)
        for route_index, label in enumerate(routes):
            if session.exhausted:
                return _UNRESOLVED
            session.record(
                "interpretation_attempt",
                segment=0,
                outcome="attempted",
                detail=label,
            )
            value = self._run_whitespace_interpretation(label, expression, context)
            if value is _UNRESOLVED or isinstance(value, PendingCall):
                session.record(
                    "candidate_pruned",
                    segment=0,
                    outcome="failed",
                    detail=label,
                )
                continue

            session.state = replace(
                session.state,
                score=session.state.score + self._whitespace_score(label),
            )
            session.record(
                "candidate_selected",
                segment=0,
                outcome="selected",
                detail=label,
                value=value,
            )
            for untried in routes[route_index + 1 :]:
                session.record(
                    "candidate_pruned",
                    segment=0,
                    outcome="not_selected",
                    detail=untried,
                )
            return value

        return _UNRESOLVED
