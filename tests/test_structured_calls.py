from __future__ import annotations

from sigils import SafeNamespace, Sigil


class ApprovedCall:
    __sigils_safe_callable__ = True

    def __init__(self, function):
        self.function = function

    def __call__(self, *args, **kwargs):
        return self.function(*args, **kwargs)


def test_colon_separates_positional_arguments() -> None:
    context = {"join": lambda left, right: f"{left}:{right}", "a": "A", "b": "B"}
    assert Sigil("[join : a : b]").solve(context) == "A:B"


def test_keyword_arguments_use_equals() -> None:
    def describe(interface: str, metric: str = "state") -> str:
        return f"{interface}:{metric}"

    context = {"describe": describe, "wlan": "wlan0", "count": "count"}
    assert Sigil("[describe : interface=wlan : metric=count]").solve(context) == "wlan0:count"


def test_explicit_positional_marker_colon_equals() -> None:
    context = {"echo": lambda value: value, "name": "Alice"}
    assert Sigil("[echo := name]").solve(context) == "Alice"
    assert Sigil("[echo := left=right]").solve(context) == "left=right"


def test_commas_create_one_tuple_argument() -> None:
    context = {"shape": lambda value: repr(value), "a": "A", "b": "B"}
    assert Sigil("[shape : a, b]").solve(context) == "('A', 'B')"


def test_keyword_argument_can_hold_tuple() -> None:
    def shape(*, values):
        return repr(values)

    context = {"shape": shape, "a": "A", "b": "B"}
    assert Sigil("[shape : values=a, b]").solve(context) == "('A', 'B')"


def test_whitespace_around_colon_comma_and_equals_is_ignored() -> None:
    def shape(left, *, values):
        return f"{left}:{values!r}"

    context = {"shape": shape, "a": "A", "b": "B", "c": "C"}
    assert Sigil("[ shape : a : values = b , c ]").solve(context) == "A:('B', 'C')"


def test_provider_approved_callable_can_be_invoked() -> None:
    command = ApprovedCall(lambda interface: f"ip:{interface}")
    context = {"network": SafeNamespace({"ip": command}), "wlan0": "wlan0"}
    assert Sigil("[network ip : wlan0]").solve(context) == "ip:wlan0"


def test_unmarked_callable_from_safe_namespace_remains_blocked() -> None:
    context = {"safe": SafeNamespace({"call": lambda: "unsafe"})}
    assert Sigil("[safe call]").solve(context) == "[safe call]"
