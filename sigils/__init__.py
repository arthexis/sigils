import os
import logging

from .transforms import resolve, replace
from .sigils import Sigil
from .errors import SigilError
from .contexts import context


DEBUG = os.environ.get("DEBUG", False)
logging.basicConfig(level=logging.DEBUG if DEBUG else logging.INFO)


__all__ = [
    "resolve",
    "context",
    "replace",
    "Sigil",
    "SigilError",
]
