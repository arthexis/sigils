import json
import os
import subprocess
import sys
import tempfile
import unittest


class TestSigilCLI(unittest.TestCase):
    def run_cli(self, args):
        process = subprocess.run(
            [sys.executable, "-m", "sigils", *args],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        return process.stdout.strip(), process.stderr.strip(), process.returncode

    def test_solve_from_text(self):
        stdout, stderr, code = self.run_cli(["Hello, [name]!", "-v", "name=Alice"])
        self.assertEqual(stdout, "Hello, Alice!")
        self.assertEqual(stderr, "")
        self.assertEqual(code, 0)

    def test_solve_from_file(self):
        with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8") as temp_file:
            temp_file.write("Hello, [name]!")
            input_path = temp_file.name

        try:
            stdout, stderr, code = self.run_cli(["-f", input_path, "-v", "name=Alice"])
            self.assertEqual(stdout, "Hello, Alice!")
            self.assertEqual(stderr, "")
            self.assertEqual(code, 0)
        finally:
            os.remove(input_path)

    def test_write_output_to_file(self):
        with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8") as input_file:
            input_file.write("Hello, [name]!")
            input_path = input_file.name
        with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8") as output_file:
            output_path = output_file.name

        try:
            stdout, stderr, code = self.run_cli(
                ["-f", input_path, "-w", output_path, "-v", "name=Alice"]
            )
            self.assertEqual(stdout, "")
            self.assertEqual(stderr, "")
            self.assertEqual(code, 0)
            with open(output_path, "r", encoding="utf-8") as file:
                self.assertEqual(file.read(), "Hello, Alice!")
        finally:
            os.remove(input_path)
            os.remove(output_path)

    def test_overwrite_file(self):
        with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8") as temp_file:
            temp_file.write("Hello, [name]!")
            input_path = temp_file.name

        try:
            stdout, stderr, code = self.run_cli(
                ["-f", input_path, "-r", "-v", "name=Alice"]
            )
            self.assertEqual(stdout, "")
            self.assertEqual(stderr, "")
            self.assertEqual(code, 0)
            with open(input_path, "r", encoding="utf-8") as file:
                self.assertEqual(file.read(), "Hello, Alice!")
        finally:
            os.remove(input_path)

    def test_solve_with_json_context(self):
        with tempfile.NamedTemporaryFile(
            "w", delete=False, suffix=".json", encoding="utf-8"
        ) as context_file:
            json.dump({"name": "Alice"}, context_file)
            context_path = context_file.name

        try:
            stdout, stderr, code = self.run_cli(["Hello, [name]!", "-c", context_path])
            self.assertEqual(stdout, "Hello, Alice!")
            self.assertEqual(stderr, "")
            self.assertEqual(code, 0)
        finally:
            os.remove(context_path)

    def test_solve_with_toml_context(self):
        with tempfile.NamedTemporaryFile(
            "w", delete=False, suffix=".toml", encoding="utf-8"
        ) as context_file:
            context_file.write('name = "Alice"\n')
            context_path = context_file.name

        try:
            stdout, stderr, code = self.run_cli(["Hello, [name]!", "-c", context_path])
            self.assertEqual(stdout, "Hello, Alice!")
            self.assertEqual(stderr, "")
            self.assertEqual(code, 0)
        finally:
            os.remove(context_path)

    def test_solve_directory_resolves_filename_and_contents(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = os.path.join(temp_dir, "[name].txt")
            with open(input_path, "w", encoding="utf-8") as file:
                file.write("Hello, [name]!")

            stdout, stderr, code = self.run_cli(["-f", temp_dir, "-v", "name=Alice"])
            self.assertEqual(stdout, "")
            self.assertEqual(stderr, "")
            self.assertEqual(code, 0)

            resolved_path = os.path.join(temp_dir, "Alice.txt")
            with open(resolved_path, "r", encoding="utf-8") as file:
                self.assertEqual(file.read(), "Hello, Alice!")

    def test_expression_evaluation(self):
        stdout, stderr, code = self.run_cli(["-e", "name.upper", "-v", "name=alice"])
        self.assertEqual(stdout, "ALICE")
        self.assertEqual(stderr, "")
        self.assertEqual(code, 0)

    def test_missing_context_key_is_preserved(self):
        stdout, stderr, code = self.run_cli(["Hello, [missing]!"])
        self.assertEqual(stdout, "Hello, [missing]!")
        self.assertEqual(stderr, "")
        self.assertEqual(code, 0)

    def test_max_depth_controls_recursive_resolution(self):
        stdout, stderr, code = self.run_cli(
            ["[a]", "-d", "0", "-v", "a=[b]", "-v", "b=resolved"]
        )
        self.assertEqual(stdout, "[b]")
        self.assertEqual(stderr, "")
        self.assertEqual(code, 0)

    def test_list_separator_is_applied(self):
        with tempfile.NamedTemporaryFile(
            "w", delete=False, suffix=".json", encoding="utf-8"
        ) as context_file:
            json.dump({"mapping": {"a": 1, "b": 2}}, context_file)
            context_path = context_file.name

        try:
            stdout, stderr, code = self.run_cli(
                ["[mapping]", "-c", context_path, "--list-sep", ","]
            )
            self.assertEqual(stdout, "a,b")
            self.assertEqual(stderr, "")
            self.assertEqual(code, 0)
        finally:
            os.remove(context_path)

    def test_seed_makes_random_tool_deterministic(self):
        stdout, stderr, code = self.run_cli(
            ["[n.randint]", "-v", "n=10", "--seed", "7"]
        )
        self.assertEqual(stdout, "5")
        self.assertEqual(stderr, "")
        self.assertEqual(code, 0)

    def test_unsupported_context_format_is_an_error(self):
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt") as context_file:
            context_path = context_file.name

        try:
            _, stderr, code = self.run_cli(["[name]", "-c", context_path])
            self.assertEqual(code, 2)
            self.assertIn("expected .json or .toml", stderr)
        finally:
            os.remove(context_path)

    def test_malformed_value_is_an_error(self):
        _, stderr, code = self.run_cli(["[name]", "-v", "name"])
        self.assertEqual(code, 2)
        self.assertIn("expected KEY=VALUE", stderr)


if __name__ == "__main__":
    unittest.main()
