from __future__ import annotations

from sigils import SafeNamespace, Sigil


class ApprovedCall:
    __sigils_safe_callable__ = True

    def __init__(self, function):
        self.function = function

    def __call__(self, *args, **kwargs):
        return self.function(*args, **kwargs)


class Service:
    def __init__(self, prefix: str):
        self.prefix = prefix

    def send(self, value: str) -> str:
        return f"{self.prefix}:{value}"


def test_double_colon_invokes_member_from_left_value() -> None:
    context = {
        "service": {"send": lambda value: f"local:{value}"},
        "payload": "data",
    }

    assert Sigil("[service :: send : payload]").solve(context) == "local:data"


def test_double_colon_does_not_fall_back_to_root_callable() -> None:
    context = {
        "service": {},
        "send": lambda value: f"external:{value}",
        "payload": "data",
    }

    assert Sigil("[service :: send : payload]").solve(context) == (
        "[service :: send : payload]"
    )


def test_double_colon_owner_path_does_not_use_root_continuation() -> None:
    calls = []

    def make(value):
        calls.append(value)
        return {"send": lambda payload: f"external-owner:{payload}"}

    context = {
        "service": {},
        "make": make,
        "payload": "data",
    }

    assert Sigil("[service.make :: send : payload]").solve(context) == (
        "[service.make :: send : payload]"
    )
    assert calls == []


def test_double_colon_local_member_wins_over_same_root_name() -> None:
    context = {
        "service": {"send": lambda value: f"local:{value}"},
        "send": lambda value: f"external:{value}",
        "payload": "data",
    }

    assert Sigil("[service :: send : payload]").solve(context) == "local:data"


def test_double_colon_supports_object_attributes() -> None:
    context = {"service": Service("object"), "payload": "data"}

    assert Sigil("[service :: send : payload]").solve(context) == "object:data"


def test_double_colon_supports_zero_argument_local_calls() -> None:
    context = {"service": {"status": lambda: "ready"}}

    assert Sigil("[service :: status]").solve(context) == "ready"


def test_double_colon_reuses_structured_keyword_arguments() -> None:
    def describe(*, interface: str, metric: str) -> str:
        return f"{interface}:{metric}"

    context = {
        "service": {"describe": describe},
        "wlan": "wlan0",
        "count": "count",
    }

    assert (
        Sigil("[service :: describe : interface=wlan : metric=count]").solve(context)
        == "wlan0:count"
    )


def test_double_colon_can_follow_a_nested_local_member_path() -> None:
    context = {
        "service": {"client": {"send": lambda value: f"nested:{value}"}},
        "payload": "data",
    }

    assert (
        Sigil("[service :: client.send : payload]").solve(context)
        == "nested:data"
    )


def test_double_colon_safe_namespace_requires_approved_callable() -> None:
    context = {
        "safe": SafeNamespace({"send": lambda value: f"unsafe:{value}"}),
        "payload": "data",
    }

    assert Sigil("[safe :: send : payload]").solve(context) == (
        "[safe :: send : payload]"
    )


def test_double_colon_safe_namespace_allows_approved_callable() -> None:
    context = {
        "safe": SafeNamespace(
            {"send": ApprovedCall(lambda value: f"approved:{value}")}
        ),
        "payload": "data",
    }

    assert Sigil("[safe :: send : payload]").solve(context) == "approved:data"


def test_double_colon_safe_namespace_nested_dict_honors_aliases() -> None:
    context = {
        "safe": SafeNamespace(
            {
                "client": {
                    "send_value": ApprovedCall(
                        lambda value: f"approved-alias:{value}"
                    )
                }
            }
        ),
        "payload": "data",
    }

    assert (
        Sigil("[safe :: client.send-value : payload]").solve(context)
        == "approved-alias:data"
    )
