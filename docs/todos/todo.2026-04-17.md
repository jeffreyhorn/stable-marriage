# Remediation Plan: `stable_marriage`

Date: 2026-04-17

This plan is ordered by risk reduction. The first steps protect correctness and the public contract before any refactor or feature work.

## Step-by-step plan

1. Freeze the public API surface and decide the status of couple support.
   - Choose one of two directions:
   - Keep only classical one-to-one stable marriage as the supported public API.
   - Or keep couple support, but move it behind an explicit experimental namespace and document it as a heuristic.
   - Exit criteria: the package API, docstrings, and docs all describe the same supported feature set.

2. Fix the Python version contract everywhere.
   - Update `pyproject.toml` `requires-python` and classifiers to match the real minimum version.
   - Align `AGENTS.md`, future `README.md`, CI, and local tooling with that same minimum.
   - Exit criteria: there is exactly one supported Python version policy across the project.

3. Replace the current packaged readme and onboarding path.
   - Create a real `README.md` for end users.
   - Change `project.readme` from `AGENTS.md` to `README.md`.
   - Remove the nonexistent `requirements.txt` instruction and replace it with `pip install -e .[dev]`.
   - Exit criteria: a fresh contributor can follow the docs without hitting a missing file or an ambiguous step.

4. Make the CLI runnable through an installed package instead of relying on path hacks.
   - Add a console entry point in `pyproject.toml`, for example `stable-marriage = "stable_marriage.cli:main"`.
   - Stop depending on `tests/conftest.py` path injection as the primary test setup.
   - Add one smoke test that exercises the CLI from an installed environment.
   - Exit criteria: documented CLI commands work after the documented install step.

5. Clarify the product boundary between library features and CLI features.
   - If couple support remains public, define a JSON schema for couples input and add CLI support.
   - If couple support is not public, remove it from the primary API and docs for now.
   - Exit criteria: there is no mismatch between what the library exposes and what the CLI/docs promise.

6. Correct the immediate couple-mode bugs before any deeper refactor.
   - Fix `_receiver_base()` so it matches its documented behavior, or replace it with explicit structured slot metadata.
   - Replace string-based internal entity IDs with opaque keys that cannot collide with user data.
   - Add regression tests for hyphenated receiver IDs and identifier collisions.
   - Exit criteria: couple-mode helpers behave deterministically for the cases they claim to support.

7. Quarantine or redesign the couples algorithm.
   - If the feature stays experimental, move it into `stable_marriage.experimental.couples` or a similarly explicit module.
   - Add a precise definition of what the algorithm guarantees, what it does not guarantee, and known failure modes.
   - If the project wants full correctness, redesign around a formal algorithmic approach and build a dedicated test corpus before re-exposing it publicly.
   - Exit criteria: the couples code no longer over-claims stability or completeness.

8. Refactor the package into clearer modules.
   - Split `solver.py` into focused modules such as `core.py`, `validation.py`, and `experimental/couples.py`.
   - Keep `__init__.py` small and intentional, exporting only supported APIs.
   - Move reusable types into a dedicated module if they remain part of the public API.
   - Exit criteria: the classical solver can be understood without reading the experimental code path.

9. Harden CLI error handling and file handling.
   - Catch read-side `OSError` the same way write-side failures are caught.
   - Set explicit UTF-8 encoding for file reads and writes.
   - Add tests for unreadable input, malformed output paths, and installed CLI execution.
   - Exit criteria: the CLI consistently returns exit code `1` with readable errors for expected operational failures.

10. Improve external documentation for actual users.
    - Add a short project overview, installation instructions, Python and CLI examples, and the input JSON schema to `README.md`.
    - If couple support exists, document the exact model and limitations in a dedicated page.
    - Add `data/README.md` if larger or additional datasets are introduced.
    - Exit criteria: a new user can install, run, and understand the supported library behavior from repository docs alone.

11. Expand tests around the highest-risk behavior.
    - Add regression tests for the fixed `_receiver_base()` behavior.
    - Add direct tests for coupled-mode entity-key collision cases.
    - Add installation or subprocess smoke tests for the packaged CLI.
    - Add more negative tests for validation and I/O failures.
    - Exit criteria: the test suite covers the project’s actual risk areas, not only the happy path.

12. Clean the repository layout and artifact hygiene.
    - Remove generated packaging artifacts from `src/` and keep environment/build outputs out of the main project tree where practical.
    - Add or tighten ignore rules for caches, coverage files, and local environment directories.
    - Keep docs under `docs/`, code under `src/`, tests under `tests/`, and sample data under `data/`.
    - Exit criteria: the repository is easy to navigate and clearly separated into source, tests, docs, and generated files.

## Suggested implementation order for PRs

1. PR 1: API decision for couples + Python version fix + README/onboarding fix.
2. PR 2: Installed CLI path + console script + CLI smoke tests.
3. PR 3: Couple-mode bug fixes for base parsing and internal IDs.
4. PR 4: Module split and cleanup refactor.
5. PR 5: Documentation expansion and repository hygiene cleanup.
