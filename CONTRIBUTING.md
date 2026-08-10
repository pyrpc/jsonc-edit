# Contributing

## Development Setup

```bash
# Clone
git clone https://github.com/pyrpc/jsonc-edit
cd jsonc-edit

# Create virtualenv
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\Activate.ps1 on Windows

# Install dev dependencies
pip install -e .
pip install pytest pytest-asyncio anyio pytest-cov pre-commit

# Install pre-commit hooks
pre-commit install

# Install docs site dependencies
cd docs && npm install
```

## Running Tests

```bash
# All tests
pytest -v

# Coverage report
pytest --cov=jsonc_edit --cov-report=term-missing
```

## Code Style

- Ruff with line length 88
- Type hints on all public functions (3.8+ syntax for wide compatibility)
- Private/internal modules prefixed with `_`
- Docstrings on all public API functions
- No em-dashes (--) in prose; use standard punctuation
- No emoji in code, comments, or documentation

Run linting:
```bash
ruff check .
ruff format --check .
```

## Pull Request Process

1. Create a feature branch from `main`
2. Write tests for any new functionality
3. Ensure all tests pass
4. Run `ruff check .` — no warnings
5. Open a PR with a clear description

## Release Process

1. Update version in `pyproject.toml` and `__init__.py`
2. Create a Git tag: `git tag v<version>`
3. Push tag: `git push origin v<version>`
4. CI publishes to PyPI automatically

## Project Structure

```text
src/jsonc_edit/         # Source code
  __init__.py           # Public API exports
  _api.py               # modify(), apply_edits(), edit_session()
  _daemon.py            # Node process lifecycle & IPC via stdin/stdout
  _daemon.js            # Node JavaScript bridge for jsonc-parser
  _runtime.py           # Dependency caching & npm bootstrap logic
  _errors.py            # Exception classes
  _models.py            # Edit dataclass
  _typing.py            # JSON/Path type hints
tests/                  # Tests
  test_api.py
  test_daemon.py
  test_lifecycle.py
  test_preservation.py
  test_runtime.py
docs/                   # Next.js/Fumadocs documentation site
```
