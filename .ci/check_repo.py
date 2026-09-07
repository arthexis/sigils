from __future__ import annotations

import argparse
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CheckResult:
    name: str
    ok: bool
    detail: str


def _check_pyproject(root: Path) -> CheckResult:
    path = root / "pyproject.toml"
    if not path.is_file():
        return CheckResult("pyproject", False, "missing pyproject.toml")

    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as exc:
        return CheckResult("pyproject", False, f"invalid pyproject.toml: {exc}")

    project = data.get("project")
    if not isinstance(project, dict):
        return CheckResult("pyproject", False, "missing [project] table")

    missing = [key for key in ("name", "version") if not project.get(key)]
    if missing:
        return CheckResult(
            "pyproject",
            False,
            "missing project field(s): " + ", ".join(missing),
        )

    return CheckResult("pyproject", True, f"project={project['name']} version={project['version']}")


def _check_tests(root: Path) -> CheckResult:
    tests = root / "tests"
    if not tests.is_dir():
        return CheckResult("tests", False, "missing tests/ directory")
    if not any(tests.rglob("test_*.py")):
        return CheckResult("tests", False, "no test_*.py files found")
    return CheckResult("tests", True, "tests/ contains test modules")


def _check_workflow(root: Path) -> CheckResult:
    workflow = root / ".github" / "workflows" / "ci.yml"
    if not workflow.is_file():
        return CheckResult("workflow", False, "missing .github/workflows/ci.yml")
    return CheckResult("workflow", True, "CI workflow present")


def _check_readme(root: Path) -> CheckResult:
    for name in ("README.md", "README.rst", "README.txt"):
        if (root / name).is_file():
            return CheckResult("readme", True, name)
    return CheckResult("readme", False, "missing README")


def check_repo(root: Path, *, require_python_project: bool = True) -> list[CheckResult]:
    checks = [_check_readme(root), _check_workflow(root)]
    if require_python_project:
        checks.extend((_check_pyproject(root), _check_tests(root)))
    return checks


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate baseline repository structure.")
    parser.add_argument("path", nargs="?", default=".", help="repository root")
    parser.add_argument(
        "--template",
        action="store_true",
        help="validate only template-level files; do not require a Python package or tests",
    )
    args = parser.parse_args(argv)

    root = Path(args.path).resolve()
    results = check_repo(root, require_python_project=not args.template)

    for result in results:
        status = "PASS" if result.ok else "FAIL"
        print(f"{status:4} {result.name:10} {result.detail}")

    return 0 if all(result.ok for result in results) else 1


if __name__ == "__main__":
    sys.exit(main())
