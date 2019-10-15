import pytest
import unittest.mock

from ..resolve import *
from ..exceptions import *


def test_resolve_attributes():
    """Attributes are resolved by case-folding."""

    class Env:
        def __init__(self, host):
            self.ssh_hostname = host

    hostname = "localhost"
    context = {"ENV": Env(hostname)}
    text = "[ENV.SSH_HOSTNAME]"

    result = resolve(text, context)
    assert result == hostname


def test_context_is_required():
    with pytest.raises(ValueError):
        result = resolve("[ENV]", required=True, default=None)


def test_required_key_not_in_context():
    context = {"USER": "arthexis"}
    with pytest.raises(SigilError):
        result = resolve("[ENV]", context, required=True)


def test_suppress_errors_default():
    context = {"USER": "arthexis"}
    sigil = "[ENV]"
    result = resolve(sigil, context)
    assert result == sigil


def test_resolve_without_extract():
    context = {"USER": "arthexis"}
    sigil = "[USER]"
    result = resolve(sigil, context)
    assert result == "arthexis"


def test_no_sigils_found():
    context = {"USER": "arthexis"}
    text = "This contains no sigils"
    result = resolve(text, context)
    assert result == text

