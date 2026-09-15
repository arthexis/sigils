from __future__ import annotations

from sigils import SafeNamespace, Sigil


class ApprovedCall:
    __sigils_safe_callable__ = True

    def __init__(self, function, *, requires_args: bool = False):
        self.function = function
        self.__sigils_requires_args__ = requires_args

    def __call__(self, *args, **kwargs):
        return self.function(*args, **kwargs)


def test_whitespace_calls_root_function_with_positional_arguments() -> None:
    context = {"join": lambda left, right: f"{left}:{right}", "a": "A", "b": "B"}

    assert Sigil("[join a b]").solve(context) == "A:B"


def test_colon_structured_call_syntax_is_not_interpreted() -> None:
    context = {"join": lambda left, right: f"{left}:{right}", "a": "A", "b": "B"}

    assert Sigil("[join:a:b]").solve(context) == "[join:a:b]"


def test_colon_keyword_call_syntax_is_not_interpreted() -> None:
    def describe(interface: str, metric: str = "state") -> str:
        return f"{interface}:{metric}"

    context = {"describe": describe, "wlan": "wlan0", "count": "count"}

    assert (
        Sigil("[describe:interface=wlan:metric=count]").solve(context)
        == "[describe:interface=wlan:metric=count]"
    )


def test_structured_call_helper_still_supports_keyword_arguments() -> None:
    def describe(*, interface: str, metric: str) -> str:
        return f"{interface}:{metric}"

    sigil = Sigil("[value]")
    context = {"wlan": "wlan0", "count": "count"}

    assert (
        sigil._run_structured_call(
            describe,
            ["interface=wlan", "metric=count"],
            context,
        )
        == "wlan0:count"
    )


def test_provider_callable_requiring_args_stays_unresolved_without_arguments() -> None:
    command = ApprovedCall(lambda interface: f"ip:{interface}", requires_args=True)
    context = {"network": SafeNamespace({"ip": command})}

    assert Sigil("[network.ip]").solve(context) == "[network.ip]"
    assert Sigil("[network.ip||:offline]").solve(context) == "offline"


def test_unmarked_callable_from_safe_namespace_remains_blocked() -> None:
    context = {"safe": SafeNamespace({"call": lambda: "unsafe"})}
    assert Sigil("[safe call]").solve(context) == "[safe call]"
