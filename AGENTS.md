# Repository Guidelines

## Project Structure & Module Organization
Core packages live in `analysis/`, `trading/`, `database/`, and `data_collection/`. Configuration stays in `config/`, while `scripts/` collects utilities such as `init_database.py` and data refresh jobs. The Flask UI sits in `web/` with templates in `web/templates`. Generated data, logs, and reports reside in their directories and should remain untracked unless explicitly needed.

## Build, Test, and Development Commands
Create a virtual environment via `python -m venv venv`, activate it (`venv\Scripts\activate` or `source venv/bin/activate`), then run `pip install -r requirements.txt`. Prime the schema with `python scripts/init_database.py`. Start the stack through `python run.py`; use `python run_web_only.py` when an engine already runs elsewhere. Utility jobs such as `python scripts/fetch_stock_list.py --market HK` seed reference data. Execute `pytest` or `python -m pytest` before pushing.

## Coding Style & Naming Conventions
Use four space indentation, `snake_case` for modules and functions, and `PascalCase` for classes. Keep existing Chinese docstrings when extending localized modules, add type hints on new paths, and send logs through `loguru`. Run `black .` and `flake8` prior to review.

## Testing Guidelines
Place pytest suites under `tests/` mirroring the source layout (example `tests/analysis/test_trading_signals.py`). Name files and functions `test_*` for discovery. Cover trading flows, database IO, and API clients with fixture driven mocks to avoid live LongPort calls. Quick pre push sweep: `pytest --maxfail=1 --disable-warnings`.

## Commit & Pull Request Guidelines
Snapshot lacks `.git`, but internal notes follow Conventional Commits such as `feat: add money flow monitor`. Keep subjects under 72 characters and explain motivation plus impact in the body. PRs should link a guide or ticket, list manual checks, attach dashboard screenshots when UI changes, and highlight config or schema updates so reviewers refresh `config/*.yaml` or migrations.

## Configuration & Security Tips
Store secrets in environment variables or the ignored `config/api_config.yaml`; never check them in. Review `config/config.yaml` before runs, especially `trading.mode` and `web.port`, and mention overrides in the PR. When sharing logs, strip account identifiers and tokens; send trimmed excerpts from `logs/longport_quant.log`.
