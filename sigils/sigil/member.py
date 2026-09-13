from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable

from ..namespace import SafeNamespace
from ..secret import Secret
from .constants import _UNRESOLVED


@dataclass(frozen=True, slots=True)
class MemberResolution:
    """Result of one structural member lookup."""

    value: object
    protected: bool
    alias: str | None = None
    bound_method: bool = False

    @property
    def resolved(self) -> bool:
        return self.value is not _UNRESOLVED


def resolve_member(
    owner: object,
    key: str,
    *,
    aliases: Callable[[str], Iterable[str]],
    protected_path: bool = False,
    allow_attributes: bool = True,
) -> MemberResolution:
    """Resolve one member consistently without root lookup or continuation."""
    parent_protected = isinstance(owner, Secret)
    lookup_value = owner.reveal() if parent_protected else owner
    candidates = (key, *tuple(aliases(key)))

    value = _UNRESOLVED
    selected_alias = None
    bound_method = False
    next_protected = protected_path

    if isinstance(lookup_value, SafeNamespace):
        for candidate in candidates:
            try:
                value = lookup_value.resolve(candidate)
                selected_alias = None if candidate == key else candidate
                break
            except KeyError:
                continue
        if value is _UNRESOLVED:
            return MemberResolution(_UNRESOLVED, protected_path)
        next_protected = True
    elif isinstance(lookup_value, dict):
        for candidate in candidates:
            if candidate in lookup_value:
                value = lookup_value[candidate]
                selected_alias = None if candidate == key else candidate
                break
    elif isinstance(lookup_value, list) and key.lstrip("+-").isdigit():
        try:
            value = lookup_value[int(key)]
        except (IndexError, ValueError):
            value = _UNRESOLVED
    elif allow_attributes and not protected_path and lookup_value is not None:
        for candidate in candidates:
            try:
                value = getattr(lookup_value, candidate)
            except AttributeError:
                continue
            selected_alias = None if candidate == key else candidate
            bound_method = callable(value)
            break

    if value is _UNRESOLVED:
        return MemberResolution(_UNRESOLVED, protected_path)
    if parent_protected and not isinstance(value, Secret):
        value = Secret(value)
    return MemberResolution(
        value,
        next_protected,
        alias=selected_alias,
        bound_method=bound_method,
    )
