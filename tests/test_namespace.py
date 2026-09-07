from __future__ import annotations

from sigils import NamespaceProvider, SafeNamespace, Secret, Sigil


class DemoProvider:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def resolve_sigil(self, key: str) -> object:
        self.calls.append(key)
        values = {
            "hostname": "gway-001",
            "network": {"address": "10.42.0.10"},
            "secret": Secret("hidden"),
        }
        if key not in values:
            raise KeyError(key)
        return values[key]


class DangerousObject:
    public = "should-not-be-reachable"

    def method(self) -> str:
        return "should-not-run"

    def __str__(self) -> str:
        return "opaque"


class DangerousProvider:
    def resolve_sigil(self, key: str) -> object:
        if key == "object":
            return DangerousObject()
        if key == "callable":
            return lambda: "should-not-run"
        raise KeyError(key)


def test_namespace_provider_protocol_is_structural() -> None:
    assert isinstance(DemoProvider(), NamespaceProvider)


def test_safe_namespace_resolves_provider_values_lazily() -> None:
    provider = DemoProvider()
    namespace = SafeNamespace(provider)
    template = Sigil("[node.hostname]")

    assert provider.calls == []
    assert template.solve({"node": namespace}) == "gway-001"
    assert provider.calls == ["hostname"]


def test_safe_namespace_allows_explicit_nested_mapping_data() -> None:
    namespace = SafeNamespace(DemoProvider())

    assert Sigil("[node.network.address]").solve({"node": namespace}) == "10.42.0.10"


def test_safe_namespace_preserves_secret_values() -> None:
    namespace = SafeNamespace(DemoProvider())
    template = Sigil("[node.secret]")

    assert template.solve({"node": namespace}) == "hidden"
    assert template.results({"node": namespace}) == {"node.secret": "[REDACTED]"}


def test_safe_namespace_keeps_unknown_keys_unresolved() -> None:
    namespace = SafeNamespace({"hostname": "gway-001"})

    assert Sigil("[node.password]").solve({"node": namespace}) == "[node.password]"


def test_safe_namespace_blocks_attribute_escape_from_provider_values() -> None:
    namespace = SafeNamespace(DangerousProvider())

    assert (
        Sigil("[node.object.public]").solve({"node": namespace})
        == "[node.object.public]"
    )
    assert (
        Sigil("[node.object.method]").solve({"node": namespace})
        == "[node.object.method]"
    )


def test_safe_namespace_does_not_execute_provider_callables() -> None:
    namespace = SafeNamespace(DangerousProvider())

    assert Sigil("[node.callable]").solve({"node": namespace}) == "[node.callable]"


def test_safe_namespace_does_not_invoke_tools_inside_protected_path() -> None:
    namespace = SafeNamespace({"name": "alice"})

    assert Sigil("[node.name.upper]").solve({"node": namespace}) == "[node.name.upper]"
