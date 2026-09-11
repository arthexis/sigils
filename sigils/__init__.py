"""Public Sigils API and runtime compatibility bootstrap."""

try:
    import tomllib as _tomllib
except ModuleNotFoundError:  # Python 3.10
    import sys as _sys

    import tomli as _tomllib

    # Package modules historically import ``tomllib`` directly. Register the
    # maintained backport under the stdlib name before importing those modules.
    _sys.modules.setdefault("tomllib", _tomllib)

from .context import Context
from .namespace import NamespaceProvider, SafeNamespace
from .secret import Secret
from .sigil import Sigil

__all__ = ["Context", "NamespaceProvider", "SafeNamespace", "Secret", "Sigil"]
