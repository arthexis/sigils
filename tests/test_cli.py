import subprocess
import os
import tempfile
import json
import unittest


class TestSigilCLI(unittest.TestCase):
    def run_cli(self, args, input_text=None):
        """Helper to run the CLI and return stdout, stderr, and exit code."""
        process = subprocess.Popen(
            ["python", "main.py"] + args,
            stdin=subprocess.PIPE if input_text else None,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = process.communicate(input_text)
        return stdout.strip(), stderr.strip(), process.returncode

    def test_solve_from_text(self):
        stdout, stderr, code = self.run_cli(["Hello, %[name]!", "-v", "name=Alice"])
        self.assertEqual(stdout, "Hello, Alice!")
        self.assertEqual(stderr, "")
        self.assertEqual(code, 0)

    def test_solve_from_file(self):
        with tempfile.NamedTemporaryFile("w+", delete=False) as temp_file:
            temp_file.write("Hello, %[name]!")
            temp_file.close()

            stdout, stderr, code = self.run_cli(["-f", temp_file.name, "-v", "name=Alice"])
            self.assertEqual(stdout, "Hello, Alice!")

            os.remove(temp_file.name)

    def test_write_output_to_file(self):
        with tempfile.NamedTemporaryFile("w+", delete=False) as input_file:
            input_file.write("Hello, %[name]!")
            input_file.close()  # ✅ Ensure file is closed before reading

        with tempfile.NamedTemporaryFile("w+", delete=False) as output_file:
            output_path = output_file.name  # ✅ Store path before closing
            output_file.close()

        try:
            self.run_cli(["-f", input_file.name, "-w", output_path, "-v", "name=Alice"])

            with open(output_path, "r") as f:
                self.assertEqual(f.read().strip(), "Hello, Alice!")

        finally:
            os.remove(input_file.name)
            os.remove(output_path)  # ✅ Clean up

    def test_overwrite_file(self):
        with tempfile.NamedTemporaryFile("w+", delete=False) as temp_file:
            temp_file.write("Hello, %[name]!")
            temp_file.close()

            self.run_cli(["-f", temp_file.name, "-o", "-v", "name=Alice"])

            with open(temp_file.name, "r") as f:
                self.assertEqual(f.read().strip(), "Hello, Alice!")

            os.remove(temp_file.name)

    def test_solve_with_json_context(self):
        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".json") as json_file:
            json.dump({"name": "Alice"}, json_file)
            json_file.close()

            stdout, stderr, code = self.run_cli(["Hello, %[name]!", "-c", json_file.name])
            self.assertEqual(stdout, "Hello, Alice!")

            os.remove(json_file.name)

    def test_solve_with_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            file1 = os.path.join(temp_dir, "%[name].txt")
            with open(file1, "w") as f:
                f.write("Hello, %[name]!")

            self.run_cli(["-f", temp_dir, "-v", "name=Alice"])

            resolved_file = os.path.join(temp_dir, "Alice.txt")
            with open(resolved_file, "r") as f:
                self.assertEqual(f.read().strip(), "Hello, Alice!")

    def test_expression_evaluation(self):
        stdout, _, _ = self.run_cli(["-e", "name.upper()", "-v", "name=alice"])
        self.assertEqual(stdout, "ALICE")

    def test_missing_context_key(self):
        stdout, stderr, code = self.run_cli(["Hello, %[missing]!"])
        self.assertEqual(stdout, "missing")
        self.assertEqual(stderr, "")
        self.assertEqual(code, 0)

    def test_debug_mode_output(self):
        stdout, stderr, _ = self.run_cli(["Hello, %[name]!", "-v", "name=Alice", "-b"])
        self.assertIn("Hello, Alice!", stdout)

if __name__ == "__main__":
    unittest.main()
