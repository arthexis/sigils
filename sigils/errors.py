from enum import Enum


class SigilError(Exception):
    """Raised when a sigil cannot be resolved."""


# Rewrite the constants as an enum
class OnError(str, Enum):
    IGNORE = "ignore"
    RAISE = "raise"
    REMOVE = "remove"
    DEFAULT = "default"


__all__ = ["SigilError"]
