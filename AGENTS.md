# Repository Guidelines

## Project Structure & Module Organization
This repository is a Python `uv` workspace.

- Root package: `src/skrynia/` (thin top-level package entrypoint).
- Workspace packages: `packages/*` (currently `packages/skry-sqla`).
- SQLAlchemy extension code: `packages/skry-sqla/src/skry_sqla/`.
- Tests: `packages/skry-sqla/tests/` with shared fixtures in `conftest.py`.
- Build outputs: `dist/` directories (do not edit generated artifacts directly).

## Build, Test, and Development Commands
Run commands from the repository root unless noted.

- `uv sync --all-packages --all-groups`: install workspace and dev dependencies.
- `uv run pytest`: run the full test suite.
- `uv run pytest packages/skry-sqla/tests/test_entity_manager.py -q`: run a focused test file.
- `cd packages/skry-sqla; uv build`: build package artifacts (`.whl`, `.tar.gz`) for `skry-sqla`.

## Coding Style & Naming Conventions
- Target runtime: Python `>=3.13`.
- Use 4-space indentation and PEP 8-compatible formatting.
- Prefer explicit type hints for public functions and class methods.
- Naming:
  - modules/files: `snake_case.py`
  - functions/variables: `snake_case`
  - classes: `PascalCase`
  - constants: `UPPER_SNAKE_CASE`
- Keep imports grouped: standard library, third-party, local.

## Testing Guidelines
- Frameworks: `pytest` and `pytest-asyncio`.
- Name tests as `test_*.py` and test functions as `test_*`.
- Async tests should use `pytest.mark.asyncio` (module-level mark is preferred, as in existing tests).
- Cover success, failure, and not-found paths for data-access code.

## Commit & Pull Request Guidelines
Git history currently has a single `Initial commit`, so no strict convention is established yet.

- Use concise, imperative commit subjects (example: `Add async save rollback test`).
- Keep commits scoped to one logical change.
- PRs should include:
  - what changed and why
  - linked issue/task (if available)
  - test evidence (for example, output summary from `uv run pytest`)
