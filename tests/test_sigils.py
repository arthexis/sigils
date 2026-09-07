import os
import unittest

from sigils import Context, Sigil


AMBIENT_GLOBAL = "Hello from globals"
AMBIENT_PRECEDENCE = "global"


class TestSigil(unittest.TestCase):
    def setUp(self):
        def recursive(x):
            return f"Hello, {x}!"

        self.context = {
            "name": "Alice",
            "age": 30,
            "email": "alice@example.com",
            "nested": {
                "key": "value"
            },
            "list": [1, 2, 3],
            "callable": lambda x: "Hello, World!",
            "callable_with_args": lambda x: f"Hello, {x}!",
            "recursive": recursive,
            "Name": "Bob",
            "AGE": 40,
        }

    def test_custom_debug_true_flag_gets_set(self):
        s = Sigil("Hello, [name]!", debug=True)
        self.assertTrue(s.debug)

    def test_custom_debug_false_flag_gets_unset(self):
        s = Sigil("Hello, [name]!", debug=False)
        self.assertFalse(s.debug)

    def test_basic_solve(self):
        s = Sigil("Hello, [name]!")
        self.assertEqual(s % self.context, "Hello, Alice!")

    def test_lazy_sigil_does_not_resolve_on_construction(self):
        name = "Ambient Alice"
        s = Sigil("[name]")
        self.assertEqual(s.template, "[name]")
        self.assertEqual(s.solve({"name": "Explicit Bob"}), "Explicit Bob")

    def test_eager_sigil_resolves_local_on_construction(self):
        name = "Ambient Alice"
        s = Sigil("%[name]")
        self.assertEqual(s.template, "Ambient Alice")
        self.assertEqual(s.solve({"name": "Explicit Bob"}), "Ambient Alice")

    def test_eager_sigil_resolves_global_on_construction(self):
        s = Sigil("%[AMBIENT_GLOBAL]")
        self.assertEqual(s.template, "Hello from globals")

    def test_eager_sigil_uses_active_context(self):
        with Context({"ambient_name": "Context Alice"}):
            s = Sigil("%[ambient_name]")
        self.assertEqual(s.template, "Context Alice")

    def test_eager_context_precedence_prefers_local_over_global_and_context(self):
        AMBIENT_PRECEDENCE = "local"
        with Context({"AMBIENT_PRECEDENCE": "context"}):
            s = Sigil("%[AMBIENT_PRECEDENCE]")
        self.assertEqual(s.template, "local")

    def test_missing_eager_sigil_is_preserved_for_later_resolution(self):
        s = Sigil("%[available_later]")
        self.assertEqual(s.template, "%[available_later]")
        self.assertEqual(
            s.solve({"available_later": "resolved later"}),
            "resolved later",
        )

    def test_eager_and_lazy_sigils_can_coexist(self):
        early = "captured now"
        s = Sigil("%[early] [late]")
        self.assertEqual(s.template, "captured now [late]")
        self.assertEqual(s.solve({"late": "resolved later"}), "captured now resolved later")

    def test_eager_recursive_resolution_preserves_lazy_tokens(self):
        early = "[late]"
        s = Sigil("%[early]")
        self.assertEqual(s.template, "[late]")
        self.assertEqual(s.solve({"late": "resolved later"}), "resolved later")

    def test_eager_recursive_resolution_continues_through_eager_tokens(self):
        first = "%[second]"
        second = "resolved now"
        s = Sigil("%[first]")
        self.assertEqual(s.template, "resolved now")

    def test_nested_solve(self):
        s = Sigil("Hello, [nested.key]!")
        self.assertEqual(s % self.context, "Hello, value!")

    def test_list_solve(self):
        s = Sigil("Number: [list.1]")
        self.assertEqual(s % self.context, "Number: 2")

    def test_callable_solve(self):
        s = Sigil("[callable]")
        self.assertEqual(s % self.context, "Hello, World!")

    def test_callable_with_args_solve(self):
        s = Sigil("[callable_with_args name]")
        self.assertEqual(s % self.context, "Hello, Alice!")

    def test_callable_with_literal_args(self):
        s = Sigil("[callable_with_args %name]")
        self.assertEqual(s % self.context, "Hello, name!")

    def test_percent_suffix_is_literal_text(self):
        self.assertEqual(Sigil("[name]%") % self.context, "Alice%")
        self.assertEqual(Sigil("%[missing]%") % {"missing": "Alice"}, "Alice%")

    def test_unsolved_sigil_is_preserved(self):
        s = Sigil("[notfound]")
        self.assertEqual(s % self.context, "[notfound]")

    def test_sigil_results_method(self):
        s = Sigil("Hello, [name]!")
        self.assertEqual(s.results(self.context), {"name": "Alice"})

    def test_recursive_solve(self):
        self.context["a"] = "[b]"
        self.context["b"] = "[c]"
        self.context["c"] = "Hello, World!"
        s = Sigil("[a]")
        self.assertEqual(s % self.context, "Hello, World!")

    def test_list_of_dictionaries_solve(self):
        self.context["users"] = [
            {"name": "Alice", "email": "alice@example.com"},
            {"name": "Bob", "email": "bob@example.com"}
        ]
        s = Sigil("User: [users.0.name], Email: [users.0.email]")
        self.assertEqual(s % self.context, "User: Alice, Email: alice@example.com")

    def test_nested_callable_with_args_solve(self):
        self.context["nested"]["callable_with_args"] = lambda x: f"Hello, {x}!"
        s = Sigil("Message: [nested.callable_with_args name]")
        self.assertEqual(s % self.context, "Message: Hello, Alice!")

    def test_recursive_callable(self):
        s = Sigil("Message: [recursive name]")
        self.assertEqual(s % self.context, "Message: Hello, Alice!")

    def test_upper(self):
        self.context["name"] = "alice"
        s = Sigil("[name.upper]")
        self.assertEqual(s % self.context, "ALICE")

    def test_lower(self):
        self.context["name"] = "ALICE"
        s = Sigil("[name.lower]")
        self.assertEqual(s % self.context, "alice")

    def test_reverse(self):
        self.context["name"] = "Alice"
        s = Sigil("[name.reverse]")
        self.assertEqual(s % self.context, "ecilA")

    def test_exact_case_keys_can_coexist(self):
        s = Sigil("[name]|[Name]|[age]|[AGE]")
        self.assertEqual(s % self.context, "Alice|Bob|30|40")

    def test_tarot(self):
        s = Sigil("[n.tarot]")
        self.assertEqual(s % {"n": "12"}, "The Hanged Man")

    def test_env_solve(self):
        os.environ["TEST_ENV_VAR"] = "Hello, Environment!"
        try:
            s = Sigil("[env TEST_ENV_VAR]")
            self.assertEqual(s % self.context, "Hello, Environment!")
        finally:
            del os.environ["TEST_ENV_VAR"]

    def test_interpolation_with_mod_operator(self):
        s = Sigil("Hello, [name]!")
        self.assertEqual(s % self.context, "Hello, Alice!")

    def test_interpolate_none(self):
        s = Sigil("Hello!")
        self.assertEqual(s % None, "Hello!")


if __name__ == "__main__":
    unittest.main()
