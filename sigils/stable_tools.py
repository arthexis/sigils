"""Corrected implementations for core Sigils built-in tools.

The historical ``tools.py`` module exposes a large compatibility surface. This
module replaces the small set of known-broken helpers in that registry without
requiring unrelated legacy tools to be rewritten as part of the stabilization
pass.
"""

import builtins as _builtins
import importlib
import json as _json
import os

try:
    import tomllib as _tomllib
except ModuleNotFoundError:  # Python 3.9 and 3.10
    import tomli as _tomllib


FORBIDDEN_ENV = (
    "DATABASE",
    "KEY",
    "SECRET",
    "ACCESS_TOKEN",
    "AWS",
    "SSH",
    "OAUTH",
    "SMTP",
    "CREDENTIALS",
    "ENV_FILE",
    "SESSION",
)


def _numbers(value):
    return [float(number) for number in str(value).split(",")]


def _select(value, index):
    return value if index is None else value[index]


def minimum(value):
    """Return the minimum number in a comma-separated list."""
    return _builtins.min(_numbers(value))


def maximum(value):
    """Return the maximum number in a comma-separated list."""
    return _builtins.max(_numbers(value))


def total(value):
    """Return the sum of a comma-separated list of numbers."""
    return _builtins.sum(_numbers(value))


def average(value):
    """Return the arithmetic mean of a comma-separated list of numbers."""
    numbers = _numbers(value)
    return _builtins.sum(numbers) / len(numbers)


def hexadecimal(value):
    """Convert an integer to a hexadecimal string without the 0x prefix."""
    return format(int(value), "x")


def json(value, index=None):
    """Parse JSON and optionally return one indexed value."""
    return _select(_json.loads(value), index)


def toml(value, index=None):
    """Parse TOML and optionally return one indexed value."""
    return _select(_tomllib.loads(value), index)


def yaml(value, index=None):
    """Parse YAML and optionally return one indexed value."""
    try:
        import yaml as _yaml
    except ImportError as exc:  # pragma: no cover - exercised without the extra
        raise RuntimeError("YAML support requires pip install sigils[yaml]") from exc
    return _select(_yaml.safe_load(value), index)


def markdown(value):
    """Convert Markdown text to HTML."""
    try:
        import markdown as _markdown
    except ImportError as exc:  # pragma: no cover - exercised without the extra
        raise RuntimeError(
            "Markdown support requires pip install sigils[markdown]"
        ) from exc
    return _markdown.markdown(value)


def _forbidden_env(name):
    upper_name = name.upper()
    return any(marker in upper_name for marker in FORBIDDEN_ENV)


def env(value):
    """Return a non-sensitive environment value or filtered environment map."""
    if not value:
        return {
            key: item
            for key, item in os.environ.items()
            if not _forbidden_env(key)
        }

    name = str(value).upper()
    if _forbidden_env(name):
        return ""
    return os.environ.get(name)


def sigil(value, start="[", end="]"):
    """Wrap text in the canonical lazy sigil delimiters."""
    return f"{start}{value}{end}"


_OVERRIDES = {
    "min": minimum,
    "max": maximum,
    "sum": total,
    "average": average,
    "hex": hexadecimal,
    "json": json,
    "toml": toml,
    "yaml": yaml,
    "markdown": markdown,
    "env": env,
    "sigil": sigil,
}


def install_tool_overrides():
    """Install corrected helpers into the legacy module and tool registry."""
    tools_module = importlib.import_module("sigils.tools")
    for name, function in _OVERRIDES.items():
        setattr(tools_module, name, function)
        tools_module.tools[name] = function
