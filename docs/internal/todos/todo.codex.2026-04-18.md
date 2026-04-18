# Remediation Plan: `stable_marriage`

Date: 2026-04-18  
Source: [review.codex.2026-04-18](../reviews/review.codex.2026-04-18.md)

This plan addresses the current shortcomings still present on branch
`review.claude.2026-04-18`, ordered by user impact first, then maintenance
cost.

---

## Priority 1: Restore public typing quality

### 1.1 Recover precise solver return types

- Rework the public typing surface so `stable_marriage(...)` and
  `stable_marriage_with_couples(...)` preserve the proposer/receiver ID type
  relationship instead of collapsing to `dict[Hashable, Hashable]`.
- Prefer one of these directions:
  - return `dict[Person, Person]` directly from the public solver signatures
  - or introduce a generic alias pattern that preserves `Person`
- Recheck all imports of `Matching` in:
  - `src/stable_marriage/core.py`
  - `src/stable_marriage/experimental/couples.py`
  - `src/stable_marriage/cli.py`
  - `src/stable_marriage/__init__.py`
- Add a downstream mypy regression that asserts the revealed type of
  `stable_marriage({...}, {...})` is concrete for a simple `str`-ID example.
- Exit criteria:
  downstream type checking no longer reveals
  `dict[typing.Hashable, typing.Hashable]` for the root solver.

---

## Priority 2: Reduce experimental-couples maintenance risk

### 2.1 Split `experimental/couples.py` by concern

- Extract validation/preprocessing helpers out of
  `src/stable_marriage/experimental/couples.py`.
- Extract receiver-base parsing helpers into a small naming-focused module or
  section with a narrower public/internal API.
- Keep the heuristic scheduler loop in one focused module that only orchestrates
  queue state, displacements, and assignments.
- Preserve the current external import path:
  `stable_marriage.experimental.stable_marriage_with_couples(...)`.
- Keep existing behavior unchanged while refactoring; this is primarily an
  architecture cleanup.
- Exit criteria:
  no single experimental module owns API surface, validation, parsing,
  scheduling, and logging all at once.

### 2.2 Add narrower unit tests around the extracted helpers

- After the split, add targeted tests for the extracted validation and
  receiver-base logic rather than only exercising them through the top-level
  heuristic.
- Keep the current end-to-end couples tests, but reduce reliance on large
  integrated fixtures for every behavior check.
- Exit criteria:
  helper behavior can be tested without stepping through the full heuristic.

---

## Priority 3: Improve packaging and entrypoint testability

### 3.1 Make `__main__.py` import-safe

- Replace the top-level `raise SystemExit(main())` in
  `src/stable_marriage/__main__.py` with a small wrapper function, for example:
  - `def run() -> int: return main()`
  - `if __name__ == "__main__": raise SystemExit(run())`
- Preserve `python -m stable_marriage` behavior.
- Exit criteria:
  importing `stable_marriage.__main__` in a unit test does not immediately
  terminate the process.

### 3.2 Cover packaging fallback paths directly

- Add a direct test for the `PackageNotFoundError` fallback path in
  `src/stable_marriage/__init__.py`, likely by reloading the module under a
  patched metadata lookup.
- Add a direct test for the `__main__.py` wrapper function.
- Keep the existing subprocess smoke tests, but stop relying on them as the
  only verification of package-entry behavior.
- Exit criteria:
  coverage for `src/stable_marriage/__main__.py` and the `__version__` fallback
  path is no longer effectively blind.

---

## Priority 4: Enforce the documented quality bar in automation

### 4.1 Add coverage enforcement to CI

- Update `.github/workflows/ci.yml` to run the coverage target, not only
  `make test`.
- Fail the workflow if coverage drops below the documented threshold.
- If branch coverage is the intended contract, configure that explicitly rather
  than relying on a prose-only statement in `AGENTS.md`.
- Exit criteria:
  the CI workflow enforces the same coverage standard the repo documents.

### 4.2 Automate packaging and typing smoke checks

- Add one CI validation for downstream typed-consumer behavior:
  install the package, run a temp mypy check without
  `--ignore-missing-imports`, and ensure the installed package is treated as
  typed.
- Keep the existing `python -m stable_marriage` subprocess test, but consider
  running a dedicated packaging-smoke target in CI so entrypoint regressions are
  clearly separated from normal unit tests.
- Exit criteria:
  packaging/type-distribution contracts are continuously verified, not just
  manually spot-checked.

---

## Priority 5: Resync contributor documentation

### 5.1 Update `AGENTS.md` for current CLI behavior

- Add the stdin input path to the CLI Usage section.
- Make it explicit that `--input` is optional.
- Refresh the fresh-checkout verification example so it reflects one of the
  currently supported invocation styles.
- Verify all CLI guidance in `AGENTS.md` matches `README.md`.
- Exit criteria:
  contributor docs no longer lag the actual CLI contract.

---

## Suggested execution order

1. Fix typing precision first, because it affects downstream consumers
   immediately and is already observable in mypy output.
2. Make package entrypoints import-safe and directly testable.
3. Enforce coverage and packaging checks in CI so the previous two fixes stay
   fixed.
4. Refactor the experimental couples module once the public and packaging
   contracts are stabilized.
5. Finish by resyncing contributor docs.
