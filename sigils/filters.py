from typing import Sequence


def join(obj: Sequence, arg=None) -> str:
    """Join left (a sequence) using sep."""
    return (arg or "").join(str(x) for x in obj)
