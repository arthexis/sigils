# Repository Guidelines

## Python Style

`pyproject.toml` is the canonical Ruff configuration for this repository. Do not duplicate or override Ruff rule selection in workflows, scripts, or agent instructions.

Current expectations are:

- Python target: 3.11.
- Maximum line length: 88.
- Ruff lint rules: `E4`, `E7`, `E9`, and `F`.
- Keep imports, syntax, whitespace, and names compatible with those configured rules; do not assume Gway or Arthexis Ruff rules also apply here.
- New or edited Python must pass both Ruff lint and Ruff format before the change is considered complete.

Use the repository configuration explicitly when checking code:

```bash
python -m ruff check --config pyproject.toml sigils tests .ci
python -m ruff format --check --config pyproject.toml sigils tests .ci
```

When fixing style locally, prefer Ruff itself rather than manually approximating its output:

```bash
python -m ruff check --fix --config pyproject.toml sigils tests .ci
python -m ruff format --config pyproject.toml sigils tests .ci
```

## CI Order

Code quality is the first gate. Package, Python compatibility, and clean-install work should remain skipped when the Ruff gate fails. Fix style before investigating downstream CI failures.

## Testing

Install the relevant optional dependencies and run the test suite with:

```bash
python -m pytest tests
```

Tests should describe supported current behavior rather than preserve removed implementation details.
