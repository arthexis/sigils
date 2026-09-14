from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass

_SELECTOR = re.compile(r"\[(?P<index>\d+)\]\Z")
_WILDCARD = "[*]"


@dataclass(frozen=True, slots=True)
class IncomingIndex:
    """One-based selector for an incoming positional value."""

    index: int


@dataclass(frozen=True, slots=True)
class IncomingSpread:
    """Marker that inserts unselected incoming positional values."""


SPREAD = IncomingSpread()


def parse_placement_marker(text: str):
    """Return a call-boundary placement marker for exact selector syntax."""
    text = text.strip()
    if text == _WILDCARD:
        return SPREAD
    match = _SELECTOR.fullmatch(text)
    if match is None:
        return None
    index = int(match.group("index"))
    if index < 1:
        raise ValueError("call placement selectors are one-based")
    return IncomingIndex(index)


def incoming_values(value) -> list[object]:
    """Normalize one explicit-pass value into positional transfer values."""
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return list(value)
    return [value]


def route_incoming(arguments: Sequence[object], incoming: Sequence[object]) -> list[object]:
    """Route incoming values through GWAY-compatible one-based selectors."""
    markers = [
        item
        for item in arguments
        if isinstance(item, (IncomingIndex, IncomingSpread))
    ]
    if not markers:
        return [*incoming, *arguments]

    spreads = sum(isinstance(item, IncomingSpread) for item in markers)
    if spreads > 1:
        raise ValueError("call placement may contain at most one [*] selector")

    selected = {item.index for item in markers if isinstance(item, IncomingIndex)}
    if selected and max(selected) > len(incoming):
        raise IndexError(
            f"call placement selector [{max(selected)}] is out of range for "
            f"{len(incoming)} value(s)"
        )

    remainder = [
        value
        for index, value in enumerate(incoming, start=1)
        if index not in selected
    ]
    routed: list[object] = []
    for item in arguments:
        if isinstance(item, IncomingIndex):
            routed.append(incoming[item.index - 1])
        elif isinstance(item, IncomingSpread):
            routed.extend(remainder)
        else:
            routed.append(item)
    return routed
