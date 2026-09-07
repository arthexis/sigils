"""Behavior tests for the Sigil resolver and eager/lazy syntax."""

import os
import unittest

from sigils import Context, Sigil


AMBIENT_GLOBAL = "Hello from globals"
AMBIENT_PRECEDENCE = "global"


class TestSigil(unittest.TestCase):
    """Exercise core resolution, recursion, tools, and ambient-context behavior."""

    def setUp(self):
        """Create a reusable context containing values, nesting, and callables."""
        def recursive(x):
            """Return a greeting used by recursive-callable tests."""
            return f"Hello, {x}!"

        self.context = {
            "name": "Alice",
            "age": 30,
            "email": "alice@example.com",
            "nested": {"key": "value"},
            "list": [1, 2, 3],
            "callable": lambda x: "Hello, World!",
            "callable_with_args": lambda x: f"Hello, {x}!",
            "recursive": recursive,
            "Name": "Bob",
            "AGE": 40,
        }

    def test_custom_debug_true_flag_gets_set(self):
        """Allow debug mode to be enabled per Sigil instance."""
        s = Sigil("Hello, [name]!", debug=True)
        self.assertTrue(s.debug)

    def test_custom_debug_false_flag_gets_unset(self):
        """Allow debug mode to be disabled per Sigil instance."""
        s = Sigil("Hello, [name]!", debug=False)
        self.assertFalse(s.debug)

    def test_basic_solve(self):
        """Resolve a basic lazy sigil from explicit context."""
        s = Sigil("Hello, [name]!")
        self.assertEqual(s % self.context, "Hello, Alice!")

    def test_lazy_sigil_does_not_resolve_on_construction(self):
        """Keep lazy sigils intact until explicitly solved."""
        name = "Ambient Alice"  # noqa: F841 - intentionally visible to inspect()
        s = Sigil("[name]")
        self.assertEqual(s.template, "[name]")
        self.assertEqual(s.solve({"name": "Explicit Bob"}), "Explicit Bob")

    def test_eager_sigil_resolves_local_on_construction(self):
        """Resolve eager sigils from caller locals during construction."""
        name = "Ambient Alice"  # noqa: F841 - intentionally visible to inspect()
        s = Sigil("%[name]")
        self.assertEqual(s.template, "Ambient Alice")
        self.assertEqual(s.solve({"name": "Explicit Bob"}), "Ambient Alice")

    def test_eager_sigil_resolves_global_on_construction(self):
        """Resolve eager sigils from caller globals when no local shadows them."""
        s = Sigil("%[AMBIENT_GLOBAL]")
        self.assertEqual(s.template, "Hello from globals")

    def test_eager_sigil_uses_active_context(self):
        """Use active Context values as an eager-resolution fallback."""
        with Context({"ambient_name": "Context Alice"}):
            s = Sigil("%[ambient_name]")
        self.assertEqual(s.template, "Context Alice")

    def test_eager_context_precedence_prefers_local_over_global_and_context(self):
        """Prefer caller locals over globals and active Context values."""
        AMBIENT_PRECEDENCE = "local"  # noqa: F841 - ambient resolver fixture
        with Context({"AMBIENT_PRECEDENCE": "context"}):
            s = Sigil("%[AMBIENT_PRECEDENCE]")
        self.assertEqual(s.template, "local")

    def test_missing_eager_sigil_is_preserved_for_later_resolution(self):
        """Preserve unresolved eager sigils for a later explicit solve."""
        s = Sigil("%[available_later]")
        self.assertEqual(s.template, "%[available_later]")
        self.assertEqual(
            s.solve({"available_later": "resolved later"}),
            "resolved later",
        )

    def test_eager_and_lazy_sigils_can_coexist(self):
        """Support early-bound and late-bound placeholders in one template."""
        early = "captured now"  # noqa: F841 - ambient resolver fixture
        s = Sigil("%[early] [late]")
        self.assertEqual(s.template, "captured now [late]")
        self.assertEqual(
            s.solve({"late": "resolved later"}), "captured now resolved later"
        )

    def test_eager_recursive_resolution_preserves_lazy_tokens(self):
        """Keep lazy tokens produced during the eager phase unresolved."""
        early = "[late]"  # noqa: F841 - ambient resolver fixture
        s = Sigil("%[early]")
        self.assertEqual(s.template, "[late]")
        self.assertEqual(s.solve({"late": "resolved later"}), "resolved later")

    def test_eager_recursive_resolution_continues_through_eager_tokens(self):
        """Continue recursive eager resolution through eager token values."""
        first = "%[second]"  # noqa: F841 - ambient resolver fixture
        second = "resolved now"  # noqa: F841 - ambient resolver fixture
        s = Sigil("%[first]")
        self.assertEqual(s.template, "resolved now")

    def test_nested_solve(self):
        """Traverse nested dictionary values with dotted expressions."""
        s = Sigil("Hello, [nested.key]!")
        self.assertEqual(s % self.context, "Hello, value!")

    def test_list_solve(self):
        """Resolve numeric list indexes from dotted expressions."""
        s = Sigil("Number: [list.1]")
        self.assertEqual(s % self.context, "Number: 2")

    def test_callable_solve(self):
        """Invoke callable context values during resolution."""
        s = Sigil("[callable]")
        self.assertEqual(s % self.context, "Hello, World!")

    def test_callable_with_args_solve(self):
        """Resolve and pass explicit arguments to context callables."""
        s = Sigil("[callable_with_args name]")
        self.assertEqual(s % self.context, "Hello, Alice!")

    def test_callable_with_literal_args(self):
        """Pass percent-prefixed function arguments as literals."""
        s = Sigil("[callable_with_args %name]")
        self.assertEqual(s % self.context, "Hello, name!")

    def test_percent_suffix_is_literal_text(self):
        """Treat a percent sign after a closing bracket as ordinary text."""
        self.assertEqual(Sigil("[name]%") % self.context, "Alice%")
        self.assertEqual(Sigil("%[missing]%") % {"missing": "Alice"}, "Alice%")

    def test_unsolved_sigil_is_preserved(self):
        """Preserve delimiters around unresolved lazy sigils."""
        s = Sigil("[notfound]")
        self.assertEqual(s % self.context, "[notfound]")

    def test_sigil_results_method(self):
        """Expose resolved expression values through ``results``."""
        s = Sigil("Hello, [name]!")
        self.assertEqual(s.results(self.context), {"name": "Alice"})

    def test_recursive_solve(self):
        """Resolve recursively nested sigil values up to the configured depth."""
        self.context["a"] = "[b]"
        self.context["b"] = "[c]"
        self.context["c"] = "Hello, World!"
        s = Sigil("[a]")
        self.assertEqual(s % self.context, "Hello, World!")

    def test_list_of_dictionaries_solve(self):
        """Traverse list indexes followed by nested dictionary keys."""
        self.context["users"] = [
            {"name": "Alice", "email": "alice@example.com"},
            {"name": "Bob", "email": "bob@example.com"},
        ]
        s = Sigil("User: [users.0.name], Email: [users.0.email]")
        self.assertEqual(s % self.context, "User: Alice, Email: alice@example.com")

    def test_nested_callable_with_args_solve(self):
        """Invoke callables stored within nested mappings."""
        self.context["nested"]["callable_with_args"] = lambda x: f"Hello, {x}!"
        s = Sigil("Message: [nested.callable_with_args name]")
        self.assertEqual(s % self.context, "Message: Hello, Alice!")

    def test_recursive_callable(self):
        """Resolve callable output inside surrounding template text."""
        s = Sigil("Message: [recursive name]")
        self.assertEqual(s % self.context, "Message: Hello, Alice!")

    def test_upper(self):
        """Apply the built-in uppercase transformation."""
        self.context["name"] = "alice"
        s = Sigil("[name.upper]")
        self.assertEqual(s % self.context, "ALICE")

    def test_lower(self):
        """Apply the built-in lowercase transformation."""
        self.context["name"] = "ALICE"
        s = Sigil("[name.lower]")
        self.assertEqual(s % self.context, "alice")

    def test_reverse(self):
        """Apply the built-in reverse transformation."""
        self.context["name"] = "Alice"
        s = Sigil("[name.reverse]")
        self.assertEqual(s % self.context, "ecilA")

    def test_exact_case_keys_can_coexist(self):
        """Keep dictionary lookup case-sensitive and exact."""
        s = Sigil("[name]|[Name]|[age]|[AGE]")
        self.assertEqual(s % self.context, "Alice|Bob|30|40")

    def test_tarot(self):
        """Resolve a historical built-in tool through the compatibility registry."""
        s = Sigil("[n.tarot]")
        self.assertEqual(s % {"n": "12"}, "The Hanged Man")

    def test_env_solve(self):
        """Resolve caller-approved environment variables through the env tool."""
        old_allowlist = os.environ.get("SIGILS_ENV_ALLOWLIST")
        os.environ["SIGILS_ENV_ALLOWLIST"] = "TEST_ENV_VAR"
        os.environ["TEST_ENV_VAR"] = "Hello, Environment!"
        try:
            s = Sigil("[env TEST_ENV_VAR]")
            self.assertEqual(s % self.context, "Hello, Environment!")
        finally:
            del os.environ["TEST_ENV_VAR"]
            if old_allowlist is None:
                os.environ.pop("SIGILS_ENV_ALLOWLIST", None)
            else:
                os.environ["SIGILS_ENV_ALLOWLIST"] = old_allowlist

    def test_interpolation_with_mod_operator(self):
        """Use the modulus operator as shorthand for explicit solve."""
        s = Sigil("Hello, [name]!")
        self.assertEqual(s % self.context, "Hello, Alice!")

    def test_interpolate_none(self):
        """Allow ``None`` as an empty explicit context."""
        s = Sigil("Hello!")
        self.assertEqual(s % None, "Hello!")


if __name__ == "__main__":
    unittest.main()
