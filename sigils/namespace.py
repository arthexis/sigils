from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol, runtime_checkable


@runtime_checkable
class NamespaceProvider(Protocol):
    """Provide explicitly approved values for a protected sigil namespace.

    Providers should return render-safe data for approved keys and raise
    ``KeyError`` for keys that are not exposed. Returned mappings and lists may
    be traversed further by Sigils, but protected resolution never falls back
    to arbitrary object attributes, built-in tools, or callable execution.
    """

    def resolve_sigil(self, key: str) -> object:
        """Return the approved value for *key* or raise ``KeyError``."""
        ...


class SafeNamespace:
    """Wrap an explicit mapping or provider as a protected sigil namespace."""

    __slots__ = ("_source",)

    def __init__(self, source: Mapping[str, object] | NamespaceProvider) -> None:
        if not isinstance(source, Mapping) and not isinstance(
            source, NamespaceProvider
        ):
            raise TypeError(
                "SafeNamespace source must be a mapping or NamespaceProvider"
            )
        self._source = source

    def resolve(self, key: str) -> object:
        """Resolve one explicitly exposed key without attribute fallthrough."""
        if isinstance(self._source, Mapping):
            if key not in self._source:
                raise KeyError(key)
            return self._source[key]
        return self._source.resolve_sigil(key)


__all__ = ["NamespaceProvider", "SafeNamespace"]
