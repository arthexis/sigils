"""Regression tests for stabilized Sigils built-in tools."""

import os
import unittest

from sigils import Sigil
from sigils import tools as tools_module


class TestStableTools(unittest.TestCase):
    """Verify corrected helpers directly and through Sigil expressions."""

    def test_numeric_aggregates_do_not_shadow_python_builtins(self):
        """Use Python builtins instead of recursively shadowing tool names."""
        self.assertEqual(tools_module.min("3,1,2"), 1.0)
        self.assertEqual(tools_module.max("3,1,2"), 3.0)
        self.assertEqual(tools_module.sum("3,1,2"), 6.0)
        self.assertEqual(tools_module.average("3,1,2"), 2.0)

    def test_hex_does_not_recurse_into_itself(self):
        """Convert integers to hexadecimal without recursive self-calls."""
        self.assertEqual(tools_module.hex("255"), "ff")
        self.assertEqual(Sigil("[n.hex]") % {"n": "255"}, "ff")

    def test_json_returns_full_value_without_index(self):
        """Parse complete JSON values when no selection index is supplied."""
        self.assertEqual(tools_module.json('{"name": "Alice"}'), {"name": "Alice"})
        self.assertEqual(tools_module.json('{"name": "Alice"}', "name"), "Alice")

    def test_toml_returns_full_value_without_index(self):
        """Parse complete TOML values when no selection index is supplied."""
        self.assertEqual(tools_module.toml('name = "Alice"'), {"name": "Alice"})
        self.assertEqual(tools_module.toml('name = "Alice"', "name"), "Alice")

    def test_yaml_returns_full_value_without_index(self):
        """Parse complete YAML values when no selection index is supplied."""
        self.assertEqual(tools_module.yaml("name: Alice"), {"name": "Alice"})
        self.assertEqual(tools_module.yaml("name: Alice", "name"), "Alice")

    def test_indexed_parsers_receive_all_sigil_arguments(self):
        """Forward both the encoded value and selection key through `_run_func`."""
        context = {
            "json_value": '{"name": "Alice"}',
            "toml_value": 'name = "Alice"',
            "yaml_value": "name: Alice",
            "field": "name",
        }
        self.assertEqual(Sigil("[json json_value field]") % context, "Alice")
        self.assertEqual(Sigil("[toml toml_value field]") % context, "Alice")
        self.assertEqual(Sigil("[yaml yaml_value field]") % context, "Alice")

    def test_markdown_extra_is_wired(self):
        """Load the Markdown optional dependency through the registered tool."""
        self.assertIn("<strong>bold</strong>", tools_module.markdown("**bold**"))

    def test_env_uses_explicit_allowlist(self):
        """Expose only default or caller-approved environment variable names."""
        old_allowlist = os.environ.get("SIGILS_ENV_ALLOWLIST")
        old_safe = os.environ.get("SIGILS_TEST_SAFE")
        old_token = os.environ.get("API_TOKEN")
        os.environ["SIGILS_ENV_ALLOWLIST"] = "SIGILS_TEST_SAFE"
        os.environ["SIGILS_TEST_SAFE"] = "visible"
        os.environ["API_TOKEN"] = "hidden"
        try:
            self.assertEqual(tools_module.env("SIGILS_TEST_SAFE"), "visible")
            self.assertEqual(tools_module.env("API_TOKEN"), "")
            environment = tools_module.env(None)
            self.assertEqual(environment["SIGILS_TEST_SAFE"], "visible")
            self.assertNotIn("API_TOKEN", environment)
        finally:
            if old_allowlist is None:
                os.environ.pop("SIGILS_ENV_ALLOWLIST", None)
            else:
                os.environ["SIGILS_ENV_ALLOWLIST"] = old_allowlist
            if old_safe is None:
                os.environ.pop("SIGILS_TEST_SAFE", None)
            else:
                os.environ["SIGILS_TEST_SAFE"] = old_safe
            if old_token is None:
                os.environ.pop("API_TOKEN", None)
            else:
                os.environ["API_TOKEN"] = old_token

    def test_default_public_environment_values_remain_available(self):
        """Keep documented non-secret process metadata available by default."""
        old_path = os.environ.get("PATH")
        os.environ["PATH"] = "/example/bin"
        try:
            self.assertEqual(tools_module.env("PATH"), "/example/bin")
        finally:
            if old_path is None:
                os.environ.pop("PATH", None)
            else:
                os.environ["PATH"] = old_path

    def test_sigil_tool_uses_lazy_canonical_syntax(self):
        """Wrap generated placeholders with canonical lazy delimiters."""
        self.assertEqual(tools_module.sigil("name"), "[name]")


if __name__ == "__main__":
    unittest.main()
