# Repository Guidelines

## Project Structure & Module Organization
- Place all runnable code under `src/stable_marriage/`, grouping algorithms, utilities, and CLI entry points by feature (e.g., `algorithms.py`, `matching.py`, `visualization/`).
- Keep reusable experiment notebooks or scripts in `notebooks/` or `scripts/`; convert production-ready logic into `src/` modules before shipping.
- Store unit tests in `tests/`, mirroring the `src/` layout (`tests/test_matching.py` exercises `src/stable_marriage/matching.py`), and add fixtures in `tests/fixtures/`.
- Check sample preference datasets into `data/` (small JSON/CSV) and document larger assets with download instructions in `data/README.md`.

## Build, Test, and Development Commands
- `python -m venv .venv && source .venv/bin/activate`: create and enter the local environment.
- `pip install -e .[dev]`: install the package and development dependencies in editable mode.
- After the editable install, run `pytest`, `ruff check src tests`, and `python -m stable_marriage.cli --input data/sample_preferences.json` from the repository root to verify a fresh checkout.
- `make test`: run the full test suite; use `pytest tests/test_solver.py -k stability` when you need to target specific cases directly.
- `make format`: format Python sources with the repository's canonical formatter setup.
- `make lint`: run the repository lint checks.
- `python -m stable_marriage.cli --input data/sample_preferences.json --output data/matching.json`: execute the reference CLI matcher and write the result after installing the package.
- CI currently validates the project on Python 3.11 and 3.12.

## CLI Usage
- Preference files are JSON objects with `proposers` and `receivers` keys whose values map participant IDs to ranked lists (arrays) of the opposite side.
- Because the project uses a `src/` layout, run `python -m stable_marriage.cli --input path/to/preferences.json` only after `pip install -e .[dev]` or `pip install .`.
- Provide `--output path/to/matches.json` to persist the matching, and `--indent 0` to disable pretty-printing when embedding in scripts.
- Exit code `1` signals invalid input or write errors (malformed JSON, incomplete keys, non-array preferences, or unwritable output paths); the CLI prints the error message to stderr for quick diagnosis.

## API Status
- The supported root API is the one-to-one `stable_marriage(...)` solver.
- Couples support is experimental and should be accessed only via `stable_marriage.experimental.stable_marriage_with_couples(...)`.

## Coding Style & Naming Conventions
- Target Python 3.11+, four-space indentation, and type-annotate public APIs (`def find_matches(...) -> MatchingResult`).
- Prefer snake_case for functions and variables, PascalCase for classes, and keep module names lowercase (`stable_marriage/rotation_elimination.py`).
- Run `make format` before pushing; the repository formatter path uses `black` plus Ruff import cleanup.
- Document non-trivial functions with Google-style docstrings and explain algorithmic complexity where it aids readers.

## Testing Guidelines
- Use `pytest` for unit and property-based tests; add `@pytest.mark.parametrize` for common preference permutations.
- Name test modules `test_<feature>.py` and prefix helper factories with `make_` to clarify intent.
- Maintain ≥90% branch coverage via `pytest --cov=stable_marriage --cov-report=term-missing`; justify exclusions in `pyproject.toml`.
- Include regression tests whenever fixing a bug or adjusting matching invariants (stability, optimality, fairness).

## Commit & Pull Request Guidelines
- Follow Conventional Commits (`feat: add rotation elimination helper`) and keep messages under 72 characters.
- Reference GitHub issues with `Fixes #12` in the body when applicable and link relevant datasets or benchmarks.
- PRs should summarize behavior changes, list test evidence (`pytest`, `ruff`), and attach screenshots or CLI transcripts for UX-affecting work.
- Request review once CI passes; assign a reviewer familiar with the affected subsystem (`matching`, `visualization`, or `data pipelines`).
