"""Tests for protected Secret values and redacted resolver introspection."""

import unittest

from sigils import Secret, Sigil


class TestSecret(unittest.TestCase):
    """Exercise value-level protection across the public resolver API."""

    def test_secret_representations_are_redacted(self):
        """Keep ordinary string and repr output free of the wrapped value."""
        secret = Secret("swordfish")
        self.assertEqual(str(secret), "[REDACTED]")
        self.assertEqual(repr(secret), "Secret('[REDACTED]')")
        self.assertNotIn("swordfish", str(secret))
        self.assertNotIn("swordfish", repr(secret))

    def test_secret_reveal_is_explicit(self):
        """Allow trusted callers to opt into retrieving the wrapped value."""
        self.assertEqual(Secret("swordfish").reveal(), "swordfish")

    def test_lazy_rendering_reveals_secret_intentionally(self):
        """Render the real value when template output is explicitly requested."""
        template = Sigil("password=[password]")
        self.assertEqual(
            template.solve({"password": Secret("swordfish")}),
            "password=swordfish",
        )

    def test_results_redact_secret_values(self):
        """Redact protected values returned by resolver introspection."""
        template = Sigil("[password]")
        self.assertEqual(
            template.results({"password": Secret("swordfish")}),
            {"password": "[REDACTED]"},
        )

    def test_results_redact_secrets_inside_containers(self):
        """Recursively redact protected values nested in mappings and lists."""
        context = {
            "payload": {
                "public": "visible",
                "tokens": [Secret("alpha"), Secret("beta")],
            }
        }
        template = Sigil("[payload]")
        self.assertEqual(
            template.results(context),
            {
                "payload": {
                    "public": "visible",
                    "tokens": ["[REDACTED]", "[REDACTED]"],
                }
            },
        )

    def test_dotted_traversal_preserves_secret_taint(self):
        """Keep children selected from a protected container protected."""
        context = {"account": Secret({"token": "swordfish"})}
        template = Sigil("[account.token]")
        self.assertEqual(template.solve(context), "swordfish")
        self.assertEqual(template.results(context), {"account.token": "[REDACTED]"})

    def test_tool_transform_preserves_secret_taint(self):
        """Keep built-in transformation results protected."""
        context = {"password": Secret("swordfish")}
        template = Sigil("[password.upper]")
        self.assertEqual(template.solve(context), "SWORDFISH")
        self.assertEqual(template.results(context), {"password.upper": "[REDACTED]"})

    def test_callable_argument_preserves_secret_taint(self):
        """Protect callable output when a resolved argument is protected."""
        context = {
            "password": Secret("swordfish"),
            "decorate": lambda value: f"<{value}>",
        }
        template = Sigil("[decorate password]")
        self.assertEqual(template.solve(context), "<swordfish>")
        self.assertEqual(
            template.results(context),
            {"decorate password": "[REDACTED]"},
        )

    def test_recursive_secret_remains_protected(self):
        """Resolve nested sigils inside a secret without losing protection."""
        context = {
            "outer": Secret("[inner]"),
            "inner": "swordfish",
        }
        template = Sigil("[outer]")
        self.assertEqual(template.solve(context), "swordfish")
        self.assertEqual(template.results(context), {"outer": "[REDACTED]"})

    def test_eager_secret_is_captured_without_plaintext_template_storage(self):
        """Capture eager secrets out of band while keeping template inspection redacted."""
        password = Secret("swordfish")  # noqa: F841 - read through ambient locals
        template = Sigil("password=%[password]")

        self.assertEqual(template.template, "password=[REDACTED]")
        self.assertNotIn("swordfish", repr(template.__dict__))
        self.assertEqual(template.solve(), "password=swordfish")

    def test_eager_secret_resolves_nested_lazy_with_explicit_context(self):
        """Resolve lazy sigils inside an eager captured secret during solve()."""
        early = Secret("[later]")  # noqa: F841 - read through ambient locals
        template = Sigil("%[early]")

        self.assertEqual(template.template, "[REDACTED]")
        self.assertEqual(template.solve({"later": "swordfish"}), "swordfish")

    def test_eager_secret_nested_lazy_respects_max_depth(self):
        """Do not bypass the recursion bound when revealing captured secrets."""
        early = Secret("[later]")  # noqa: F841 - read through ambient locals
        template = Sigil("%[early]", max_depth=0)

        self.assertEqual(template.solve({"later": "swordfish"}), "[later]")

    def test_nested_eager_secrets_replace_inner_markers(self):
        """Reveal nested eager Secret captures without leaking opaque markers."""
        inner = Secret("swordfish")  # noqa: F841 - read through ambient locals
        outer = Secret("%[inner]")  # noqa: F841 - read through ambient locals
        template = Sigil("%[outer]")

        self.assertEqual(template.template, "[REDACTED]")
        self.assertEqual(template.solve(), "swordfish")


if __name__ == "__main__":
    unittest.main()
