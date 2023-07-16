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
            "callable": lambda: "Hello, World!",
            "callable_with_args": lambda x: f"Hello, {x}!",
            "recursive": recursive,
        }


    def test_interpolation(self):
        s = Sigil("Hello, %[name]!")
        self.assertEqual(s % self.context, "Hello, Alice!")

    def test_nested_interpolation(self):
        s = Sigil("Hello, %[nested.key]!")
        self.assertEqual(s % self.context, "Hello, value!")

    def test_list_interpolation(self):
        s = Sigil("Number: %[list.1]")
        self.assertEqual(s % self.context, "Number: 2")

    def test_callable_interpolation(self):
        s = Sigil("%[callable]")
        self.assertEqual(s % self.context, "Hello, World!")

    def test_callable_with_args_interpolation(self):
        s = Sigil("%[callable_with_args:name]")
        self.assertEqual(s % self.context, "Hello, Alice!")

    def test_callable_with_literal_args(self):
        s = Sigil("%[callable_with_args:%name]")
        self.assertEqual(s % self.context, "Hello, name!")

    def test_sigils(self):
        s = Sigil("Hello, %[name]!")
        self.assertEqual(s.sigils(self.context), {"name": "Alice"})

    def test_recursive_interpolation(self):
        self.context["a"] = "%[b]"
        self.context["b"] = "%[c]"
        self.context["c"] = "Hello, World!"
        s = Sigil("%[a]")
        self.assertEqual(s % self.context, "Hello, World!")

    def test_list_of_dictionaries_interpolation(self):
        self.context["users"] = [
            {"name": "Alice", "email": "alice@example.com"},
            {"name": "Bob", "email": "bob@example.com"}
        ]
        s = Sigil("User: %[users.0.name], Email: %[users.0.email]")
        self.assertEqual(s % self.context, "User: Alice, Email: alice@example.com")

    def test_nested_callable_with_args_interpolation(self):
        self.context['nested']['callable_with_args'] = lambda x: f"Hello, {x}!"
        s = Sigil("Message: %[nested.callable_with_args:name]")
        self.assertEqual(s % self.context, "Message: Hello, Alice!")

    def test_recursive_callable(self):
        s = Sigil("Message: %[recursive:name]")
        self.assertEqual(s % self.context, "Message: Hello, Alice!")



if __name__ == "__main__":
    unittest.main()
