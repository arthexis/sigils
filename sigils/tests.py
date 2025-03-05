import os
import unittest
from sigils import Sigil


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
            "Name": "Bob",  # Upper case key
            "AGE": 40,      # Upper case key
        }

    def test_custom_debug_true_flag_gets_set(self):
        s = Sigil("Hello, %[name]!", debug=True)
        self.assertTrue(s.debug)  

    def test_custom_debug_false_flag_gets_unset(self):
        s = Sigil("Hello, %[name]!", debug=False)
        self.assertFalse(s.debug)  

    def test_basic_solve(self):
        s = Sigil("Hello, %[name]!")
        self.assertEqual(s % self.context, "Hello, Alice!")

    def test_nested_solve(self):
        s = Sigil("Hello, %[nested.key]!")
        self.assertEqual(s % self.context, "Hello, value!")

    def test_list_solve(self):
        s = Sigil("Number: %[list.1]")
        self.assertEqual(s % self.context, "Number: 2")

    def test_callable_solve(self):
        s = Sigil("%[callable]")
        self.assertEqual(s % self.context, "Hello, World!")

    def test_callable_with_args_solve(self):
        s = Sigil("%[callable_with_args name]")
        self.assertEqual(s % self.context, "Hello, Alice!")

    def test_callable_with_literal_args(self):
        s = Sigil("%[callable_with_args %name]")
        self.assertEqual(s % self.context, "Hello, name!")

    def test_literal_on_unsolved_just_removes_brackets(self):
        s = Sigil("%[notfound]")
        self.assertEqual(s % self.context, "notfound")

    def test_sigil_results(self):
        s = Sigil("Hello, %[name]!")
        self.assertEqual(s.results(self.context), {"name": "Alice"})

    def test_recursive_solve(self):
        self.context["a"] = "%[b]"
        self.context["b"] = "%[c]"
        self.context["c"] = "Hello, World!"
        s = Sigil("%[a]")
        self.assertEqual(s % self.context, "Hello, World!")

    def test_list_of_dictionaries_solve(self):
        self.context["users"] = [
            {"name": "Alice", "email": "alice@example.com"},
            {"name": "Bob", "email": "bob@example.com"}
        ]
        s = Sigil("User: %[users.0.name], Email: %[users.0.email]")
        self.assertEqual(s % self.context, "User: Alice, Email: alice@example.com")

    def test_nested_callable_with_args_solve(self):
        self.context['nested']['callable_with_args'] = lambda x: f"Hello, {x}!"
        s = Sigil("Message: %[nested.callable_with_args name]")
        self.assertEqual(s % self.context, "Message: Hello, Alice!")

    def test_recursive_callable(self):
        s = Sigil("Message: %[recursive name]")
        self.assertEqual(s % self.context, "Message: Hello, Alice!")

    def test_upper(self):
        self.context["name"] = "alice"
        s = Sigil("%[name.upper]")
        self.assertEqual(s % self.context, "ALICE")

    def test_lower(self):
        self.context["name"] = "ALICE"
        s = Sigil("%[name.lower]")
        self.assertEqual(s % self.context, "alice")

    def test_reverse(self):
        self.context["name"] = "Alice"
        s = Sigil("%[name.reverse]")
        self.assertEqual(s % self.context, "ecilA")

    def test_case_insensitive_solve(self):
        s = Sigil("Hello, %[Name]!")
        self.assertEqual(s % self.context, "Hello, Bob!")

    def test_case_insensitive_solve_lowercase(self):
        s = Sigil("Age: %[age]")
        self.assertEqual(s % self.context, "Age: 30")

    def test_case_insensitive_solve_uppercase(self):
        s = Sigil("Age: %[AGE]")
        self.assertEqual(s % self.context, "Age: 40")

    def test_tarot(self):
        s = Sigil("%[n.tarot]")
        self.assertEqual(s % {'n': '12'}, "The Hanged Man")

    def test_env_solve(self):
        os.environ["TEST_ENV_VAR"] = "Hello, Environment!"
        s = Sigil("%[env TEST_ENV_VAR]")
        self.assertEqual(s % self.context, "Hello, Environment!")
        del os.environ["TEST_ENV_VAR"]

    def test_iterpolation_with_mod_operator(self):
        # Keep at least one example, since this is the most common use case
        s = Sigil("Hello, %[name]!")
        self.assertEqual(s % self.context, "Hello, Alice!")

    def test_iterpolate_none(self):
        # Keep at least one example, since this is the most common use case
        s = Sigil("Hello!")
        self.assertEqual(s % None, "Hello!")

if __name__ == "__main__":
    unittest.main()
