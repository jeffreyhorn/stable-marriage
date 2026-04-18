# Code Review: `stable_marriage`

Date: 2026-04-18  
Reviewer: Codex

## Scope

Reviewed the current working tree on branch `review.claude.2026-04-18`, including:

- `src/stable_marriage/`
- `tests/`
- `README.md`, `AGENTS.md`, `CHANGELOG.md`
- `.github/workflows/ci.yml`
- `pyproject.toml`, `Makefile`

## Validation performed

- Read all production modules and test modules.
- Ran `.venv/bin/python -m pytest --cov=stable_marriage --cov-report=term-missing`
  -> `62 passed`, `96%` total coverage.
- Ran a downstream mypy probe against the current public API:
  `reveal_type(stable_marriage(...))` currently resolves to
  `dict[typing.Hashable, typing.Hashable]`.

## Findings

### 1. Medium-High: the exported `Matching` alias has degraded downstream type precision

**Evidence**

- [src/stable_marriage/types.py](/Users/jeff/experiments/stable_marriage/src/stable_marriage/types.py:8) defines `Person` as a `TypeVar`, but [types.py](/Users/jeff/experiments/stable_marriage/src/stable_marriage/types.py:11) now exports `Matching: TypeAlias = dict[Hashable, Hashable]`.
- Public solver signatures still look generic, but they return `Matching`:
  [core.py](/Users/jeff/experiments/stable_marriage/src/stable_marriage/core.py:12),
  [experimental/couples.py](/Users/jeff/experiments/stable_marriage/src/stable_marriage/experimental/couples.py:18).
- A downstream mypy probe on the installed package now reveals
  `dict[typing.Hashable, typing.Hashable]` for `stable_marriage(...)`, rather
  than `dict[str, str]` or `dict[Person, Person]`.

**Why this matters**

- The package now advertises itself as typed, but the primary return type has
  become much less useful to typed consumers.
- Call sites lose the same-type relationship between proposer IDs and receiver
  IDs even when both sides are statically known.
- This is a regression in API ergonomics and type-driven maintainability.

**Recommendation**

- Restore generic precision at the public function boundary.
- Either return `dict[Person, Person]` directly from the public solvers, or
  redefine the shared typing surface so the exported alias preserves the same
  type parameter relationship instead of collapsing to `Hashable`.

### 2. Medium: `experimental/couples.py` is becoming a maintenance hotspot with too many responsibilities

**Evidence**

- [src/stable_marriage/experimental/couples.py](/Users/jeff/experiments/stable_marriage/src/stable_marriage/experimental/couples.py:1)
  now contains:
  the public API, heuristic queue scheduler, validation logic, naming/base
  parsing, target selection, iteration-bound logic, and debug logging.
- The main heuristic body alone spans
  [couples.py:77](/Users/jeff/experiments/stable_marriage/src/stable_marriage/experimental/couples.py:77)
  through [couples.py:314](/Users/jeff/experiments/stable_marriage/src/stable_marriage/experimental/couples.py:314),
  while validation and parsing live in the same file below it.

**Why this matters**

- Every new change to the experimental couples path now lands in one large,
  high-churn module.
- Mixed concerns make the heuristic harder to reason about, harder to test in
  smaller units, and more expensive to refactor safely.
- The recent additions (`base_fn`, iteration bounds, logging, validation
  tightening) all compounded this concentration.

**Recommendation**

- Split the module by concern.
- A pragmatic cut would separate:
  validation/preprocessing,
  receiver-base parsing helpers,
  and the heuristic scheduler itself.

### 3. Medium: packaging-entrypoint behavior is still hard to test directly, and important fallback paths remain uncovered

**Evidence**

- [src/stable_marriage/__main__.py](/Users/jeff/experiments/stable_marriage/src/stable_marriage/__main__.py:7)
  raises `SystemExit(main())` at import time.
- Current coverage shows:
  - `src/stable_marriage/__main__.py` -> `0%`
  - `src/stable_marriage/__init__.py` fallback path -> uncovered
- The existing subprocess coverage is useful, but it does not make the module
  import-safe for direct tests or tooling.

**Why this matters**

- Importing `stable_marriage.__main__` from a unit test or helper immediately
  exits the process, which makes direct verification awkward.
- The version fallback path and the package entrypoint behavior can regress
  without local coverage making that obvious.
- This is mostly a testability and maintainability problem, not a runtime bug.

**Recommendation**

- Refactor `__main__.py` to expose a small callable wrapper and only raise
  `SystemExit` under an `if __name__ == "__main__"` guard.
- Add direct tests for the `__version__` fallback path and the package
  entrypoint wrapper so those packaging behaviors are covered without relying
  only on subprocess smoke tests.

### 4. Medium: the documented coverage standard is not enforced by CI

**Evidence**

- [AGENTS.md](/Users/jeff/experiments/stable_marriage/AGENTS.md:39) says the
  project should maintain `>=90%` branch coverage.
- CI only runs `make typecheck`, `make lint`, and `make test` in
  [.github/workflows/ci.yml](/Users/jeff/experiments/stable_marriage/.github/workflows/ci.yml:31).
- Local coverage currently exposes blind spots:
  `__main__.py` at `0%` and `__init__.py` at `75%`.

**Why this matters**

- The repository documents a coverage contract but does not automate it.
- That leaves packaging and entrypoint regressions easier to miss even though
  the project already relies on a fairly small codebase and a manageable test
  surface.
- This is a workflow reliability problem more than a code bug.

**Recommendation**

- Make coverage part of CI and fail below the documented threshold.
- Consider also automating the downstream typing smoke check that justified the
  `py.typed` marker, because that contract is currently only verified manually.

### 5. Low: contributor documentation is already lagging current CLI behavior

**Evidence**

- [README.md](/Users/jeff/experiments/stable_marriage/README.md:105) documents
  stdin support for the CLI.
- [AGENTS.md](/Users/jeff/experiments/stable_marriage/AGENTS.md:21) still
  describes the CLI as file-path oriented and does not mention stdin input.
- [AGENTS.md](/Users/jeff/experiments/stable_marriage/AGENTS.md:12) still
  uses only the file-input verification command in its fresh-checkout guidance.

**Why this matters**

- `AGENTS.md` is contributor-facing process documentation, so drift there tends
  to recreate confusion during onboarding and future code review.
- This is a small issue, but it is exactly the kind of documentation skew that
  accumulates after fast-moving cleanup work.

**Recommendation**

- Sync `AGENTS.md` with the current CLI contract:
  stdin support, optional `--input`, and the currently supported invocation
  paths.

## Residual risks

- The one-to-one solver implementation is compact and well covered, so most of
  the current risk is concentrated in packaging/type contracts and the
  experimental couples path rather than the Gale-Shapley core itself.
- The experimental couples heuristic is now more configurable and observable,
  but that flexibility has increased the amount of logic concentrated in one
  module.
