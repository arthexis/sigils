import os
import unittest

from sigils import Sigil
from sigils import tools as tools_module


class TestStableTools(unittest.TestCase):
    def test_numeric_aggregates_do_not_shadow_python_builtins(self):
        self.assertEqual(tools_module.min("3,1,2"), 1.0)
        self.assertEqual(tools_module.max("3,1,2"), 3.0)
        self.assertEqual(tools_module.sum("3,1,2"), 6.0)
        self.assertEqual(tools_module.average("3,1,2"), 2.0)

    def test_hex_does_not_recurse_into_itself(self):
        self.assertEqual(tools_module.hex("255"), "ff")
        self.assertEqual(Sigil("[n.hex]") % {"n": "255"}, "ff")

    def test_json_returns_full_value_without_index(self):
        self.assertEqual(tools_module.json('{"name": "Alice"}'), {"name": "Alice"})
        self.assertEqual(tools_module.json('{"name": "Alice"}', "name"), "Alice")

    def test_toml_returns_full_value_without_index(self):
        self.assertEqual(tools_module.toml('name = "Alice"'), {"name": "Alice"})
        self.assertEqual(tools_module.toml('name = "Alice"', "name"), "Alice")

    def test_yaml_returns_full_value_without_index(self):
        self.assertEqual(tools_module.yaml("name: Alice"), {"name": "Alice"})
        self.assertEqual(tools_module.yaml("name: Alice", "name"), "Alice")

    def test_markdown_extra_is_wired(self):
        self.assertIn("<strong>bold</strong>", tools_module.markdown("**bold**"))

    def test_env_filters_sensitive_names(self):
        old_safe = os.environ.get("SIGILS_TEST_SAFE")
        old_secret = os.environ.get("SIGILS_TEST_SECRET")
        os.environ["SIGILS_TEST_SAFE"] = "visible"
        os.environ["SIGILS_TEST_SECRET"] = "hidden"
        try:
            self.assertEqual(tools_module.env("SIGILS_TEST_SAFE"), "visible")
            self.assertEqual(tools_module.env("SIGILS_TEST_SECRET"), "")
            environment = tools_module.env(None)
            self.assertEqual(environment["SIGILS_TEST_SAFE"], "visible")
            self.assertNotIn("SIGILS_TEST_SECRET", environment)
        finally:
            if old_safe is None:
                os.environ.pop("SIGILS_TEST_SAFE", None)
            else:
                os.environ["SIGILS_TEST_SAFE"] = old_safe
            if old_secret is None:
                os.environ.pop("SIGILS_TEST_SECRET", None)
            else:
                os.environ["SIGILS_TEST_SECRET"] = old_secret

    def test_sigil_tool_uses_lazy_canonical_syntax(self):
        self.assertEqual(tools_module.sigil("name"), "[name]")


if __name__ == "__main__":
    unittest.main()
