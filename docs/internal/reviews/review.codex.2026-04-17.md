# Code Review: `stable_marriage`

Date: 2026-04-17

Scope reviewed:
- `src/stable_marriage/`
- `tests/`
- `data/`
- `pyproject.toml`
- `AGENTS.md`

Validation performed:
- `pytest` -> 22 passed
- `pytest --cov=stable_marriage --cov-report=term-missing` -> 92% total coverage
- `ruff check src tests` -> passed
- `python -m stable_marriage.cli --input data/sample_preferences.json --indent 0` from a fresh checkout context -> failed with `ModuleNotFoundError`

## Findings

### 1. High: couple support is presented as a stable-matching capability without a defensible correctness contract

Evidence:
- The public API advertises couple handling directly on `stable_marriage(...)` and describes the result as a stable matching in `src/stable_marriage/solver.py:25-59`.
- The implementation in `src/stable_marriage/solver.py:107-272` is a greedy heuristic layered on top of Gale-Shapley, not a proved algorithm for the stable matching with couples problem.
- The test fixtures already acknowledge the limitation in `tests/fixtures/couples.py:37-43`.
- The regression in `tests/test_solver.py:245-249` treats a failure on a conflicting couple instance as expected behavior rather than as a clearly documented limitation of an experimental API.

Why this matters:
- Stable matching with couples is materially harder than one-to-one stable marriage. The current API and docstrings imply a guarantee the implementation does not justify.
- Consumers can reasonably assume that a returned result is stable under the same meaning as the classic algorithm, or that `ValueError` means no valid solution exists. Neither claim is currently defendable.

Impact:
- Primary risk is correctness and trust. This is the most important issue in the library.

Recommendation:
- Either remove couples from the main `stable_marriage(...)` API until there is a well-specified solver, or move it to an explicitly experimental module with a precise contract that states what is and is not guaranteed.

### 2. High: published Python compatibility metadata is incorrect

Evidence:
- `pyproject.toml:10` declares `requires-python = ">=3.8"`.
- The code uses PEP 604 union syntax such as `Sequence[str] | None` in `src/stable_marriage/cli.py:15`, `src/stable_marriage/cli.py:43`, `src/stable_marriage/cli.py:111`, and `src/stable_marriage/cli.py:126`, which requires Python 3.10+.
- `AGENTS.md:23-27` separately says the project targets Python 3.11+.

Why this matters:
- Users on Python 3.8 or 3.9 can be told by package metadata that the project supports their interpreter, then hit syntax errors immediately.
- The project currently advertises three different compatibility stories: `>=3.8`, `3.11+`, and actual syntax usage of `3.10+`.

Impact:
- Installation and support expectations are incorrect.

Recommendation:
- Pick one minimum supported Python version and make `pyproject.toml`, docs, CI, and code all match it. Given the current style guide, `>=3.11` is the cleanest choice.

### 3. High: external onboarding and packaging documentation do not work from a clean checkout

Evidence:
- `AGENTS.md:10-15` tells contributors to run `pip install -r requirements.txt`, but no `requirements.txt` exists.
- `AGENTS.md:15` and `AGENTS.md:19-20` tell users to run `python -m stable_marriage.cli ...`, but that fails from the repository root before installation because the project uses a `src/` layout.
- `tests/conftest.py:1-8` injects `src/` into `sys.path`, which makes tests pass while masking the real packaging/onboarding gap.
- `pyproject.toml:9` uses `AGENTS.md` as the package readme, so internal contributor instructions are being published as end-user package documentation.

Why this matters:
- The documented quick-start path is broken.
- Test success currently overstates the health of the packaging and installation experience.
- The published package metadata points users to repository instructions instead of product documentation.

Impact:
- Usability is substantially worse than the passing test suite suggests.

Recommendation:
- Add a real `README.md`, switch `project.readme` to it, document `pip install -e .[dev]`, and add an installed-package smoke test instead of relying on `tests/conftest.py`.

### 4. Medium: `solver.py` is carrying too many responsibilities for a library expected to grow

Evidence:
- `src/stable_marriage/solver.py` contains the public API, the classical solver, the couples heuristic, identifier parsing, and all validation logic in one file.

Why this matters:
- The one-to-one algorithm is compact and maintainable today, but the file is already doing several distinct jobs.
- The couples code path and helper routines make the core algorithm harder to reason about than necessary.

Impact:
- Maintainability and reviewability will degrade quickly as the library expands.

Recommendation:
- Split responsibilities into at least `core.py`, `couples.py` or `experimental/couples.py`, and `validation.py`, with `__init__.py` re-exporting the intended public API.

### 5. Medium: `_receiver_base()` contradicts its own documented behavior for hyphenated receiver IDs

Evidence:
- The docstring in `src/stable_marriage/solver.py:400-407` says `Hospital-1-SlotA -> Hospital-1`.
- The implementation in `src/stable_marriage/solver.py:409-414` splits on the first `-`, which returns `Hospital`.
- A direct evaluation on 2026-04-17 confirmed `_receiver_base("Hospital-1-SlotA") == "Hospital"`.

Why this matters:
- Couple placement depends on base extraction.
- The code does not do what the documentation says for one of the documented examples.

Impact:
- Hyphenated receiver IDs are parsed incorrectly in couple mode.

Recommendation:
- Replace the heuristic with an explicit slot/base representation, or at minimum implement a deterministic parsing rule that matches the documented examples and test it.

### 6. Medium: coupled-mode internal entity keys can collide with user identifiers

Evidence:
- Singles are keyed internally with `str(proposer)` in `src/stable_marriage/solver.py:158-168`.
- Couples are keyed with `f"couple:{couple_id}"` in `src/stable_marriage/solver.py:146-156`.

Why this matters:
- The public API is generic over any hashable participant type, but the implementation collapses identifiers into strings.
- Distinct values such as `1` and `"1"` become the same internal key. User IDs that already look like `"couple:..."` can also collide with synthetic names.

Impact:
- This is a latent correctness bug in coupled mode.

Recommendation:
- Use opaque internal keys such as tuples or dedicated dataclasses instead of stringifying user data.

### 7. Medium: the CLI exposes only a subset of the library surface and leaves major behavior undocumented

Evidence:
- The library API accepts `couples`, but the CLI in `src/stable_marriage/cli.py:15-139` has no way to load or pass couples.
- `AGENTS.md:17-21` documents only the one-to-one JSON shape.

Why this matters:
- Users cannot tell whether couples are intentionally unsupported in the CLI or simply undocumented.
- There is also no console-script entry point, so even the supported CLI path is less ergonomic than it should be.

Impact:
- The product boundary is unclear.

Recommendation:
- Decide whether couples are public. If yes, define and document a CLI schema. If no, remove them from the advertised public API until the feature is ready.

### 8. Medium: CLI file-I/O handling is narrower than the documented error contract

Evidence:
- `src/stable_marriage/cli.py:46-51` catches `FileNotFoundError` and `JSONDecodeError` when reading input, but not other `OSError` cases such as permission failures.
- `src/stable_marriage/cli.py:120-123` catches output write failures, but the input side is not symmetric.
- `AGENTS.md:21` says exit code `1` signals invalid input or write errors, but unreadable input files can still escape as uncaught exceptions.

Why this matters:
- CLI behavior should be predictable for automation.
- Input and output error handling should follow the same contract.

Impact:
- A subset of operational failures still bypass the user-friendly `Error: ...` path.

Recommendation:
- Catch read-side `OSError`, set explicit UTF-8 encoding on reads and writes, and add regression tests for unreadable or permission-denied input.

### 9. Low: repository structure is clean for source code, but the working tree is noisy

Evidence:
- The current tree includes `install/`, `src/stable_marriage.egg-info/`, `.coverage`, `.pytest_cache/`, and `.ruff_cache/`.

Why this matters:
- Even if some of these are local artifacts, they make the project harder to navigate and blur the boundary between source, build outputs, and environment state.

Impact:
- Structure and developer ergonomics are weaker than the small codebase deserves.

Recommendation:
- Keep generated artifacts out of the project tree where possible, add or tighten ignore rules, and avoid storing packaging byproducts under `src/`.

### 10. Low: test coverage is good, but it is not yet aligned with the highest-risk areas

Evidence:
- Coverage is 92%, which is good.
- Missing lines in the coverage report are concentrated in validation and uncommon branches of `solver.py`.
- There are no direct regression tests for the documented hyphenated receiver example, identifier-collision risks in couples mode, or installed-package CLI smoke tests.

Why this matters:
- The current suite is strong for the classical solver, but not for the most fragile edges.

Impact:
- The test suite currently protects confidence unevenly.

Recommendation:
- Add regression tests that target the specific risks above before making feature or refactor changes.

## Scorecard

| Area | Assessment |
| --- | --- |
| Correctness | Good for one-to-one Gale-Shapley; not reliable enough for couple support as currently advertised. |
| Efficiency | One-to-one path is appropriately `O(n^2)` and implemented efficiently; couple mode has no clear complexity or guarantee story. |
| Maintainability | Decent in the small, but `solver.py` is already over-concentrated and mixes stable core logic with experimental behavior. |
| Usability | Weaker than it should be because the documented install/run path is broken from a clean checkout. |
| Internal documentation | Generally good docstrings in source and fixtures. |
| External documentation | Weak; there is no proper README or packaged user-facing guide. |
| Structure | Reasonable `src/` and `tests/` layout, but module boundaries and artifact hygiene need work. |

## Strengths

- The classical one-to-one solver is small, readable, and uses the right data structures for Gale-Shapley.
- Validation logic is strict about complete preference lists, which keeps the main algorithm simple.
- The test suite is better than average for a small library: randomized checks, worst-case proposal counting, CLI tests, and 92% coverage.
- Error messages are mostly understandable, and the JSON CLI interface is simple for the supported one-to-one case.

## Overall assessment

The project has a solid core in the classical stable-marriage implementation, and that core is already tested at a useful level. The biggest risk is that the library currently presents a broader and more mature product than it actually implements. If the project narrows its public contract around the one-to-one solver, fixes the packaging/documentation path, and either removes or quarantines the couples heuristic, it can become a clean, dependable small library quickly.
