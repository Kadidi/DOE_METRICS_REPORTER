# Repository Guidelines

## Project Structure & Module Organization
Core Python entry points live at the repository root (for example, `doe_metrics_client.py`, `multi_ask.py`, `slack_bot.py`). Reusable logic is organized under:
- `servers/`: MCP server integrations (Google Docs, Slack, templates for new sources)
- `models/`: Pydantic data models (`incident.py`, `job.py`, `message.py`)
- `cache/`: SQLite-backed cache manager and helpers
- `tests/`: pytest unit tests (currently focused on cache behavior)
- `docs/`: setup, API configuration, architecture, and usage references

Prefer adding new source integrations in `servers/` and corresponding model changes in `models/`.

## Build, Test, and Development Commands
- `pip install -e .` installs the package in editable mode.
- `pip install -e ".[dev]"` installs developer tooling (`pytest`, `black`, `ruff`).
- `./setup_user.sh` creates/populates local `.env` configuration.
- `./start_reporter.sh` launches the CLI reporter.
- `pytest tests/` runs the primary test suite.
- `pytest tests/test_cache.py -v` runs cache tests with verbose output.
- `black .` formats code (line length 100).
- `ruff check .` runs static lint checks.

## Coding Style & Naming Conventions
Target runtime is Python 3.11+. Use 4-space indentation, type hints where practical, and keep lines within 100 characters (Black/Ruff config in `pyproject.toml`).  
Naming patterns:
- files/modules: `snake_case.py`
- functions/variables: `snake_case`
- classes/models: `PascalCase`
- constants/env keys: `UPPER_SNAKE_CASE`

## Testing Guidelines
Use `pytest` (with `pytest-asyncio` configured as `asyncio_mode = auto`).  
Place unit tests in `tests/` and name files/functions as `test_*.py` and `test_*`.  
Keep fast, deterministic tests for core logic; place external API checks in clearly marked integration scripts (for example, root-level `test_slack.py`, `test_sfapi.py`).

## Commit & Pull Request Guidelines
Git history is not available in this workspace snapshot, so follow a clear imperative style:
- Commit format: `type: short description` (for example, `feat: add sfapi outage formatter`).
- Keep commits focused and logically scoped.
- PRs should include: summary, affected modules, test evidence (`pytest ...` output), config/env changes, and linked issue/ticket when applicable.

## Security & Configuration Tips
Never commit secrets (`.env`, tokens, OAuth JSON credentials). Use `.env.template` as the source of required keys and keep local credentials outside version control.
