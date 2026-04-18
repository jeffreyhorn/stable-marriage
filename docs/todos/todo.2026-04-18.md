# Remediation Plan: `stable_marriage`

Date: 2026-04-18
Source: [review.claude.2026-04-18](../reviews/review.claude.2026-04-18.md)

This plan is ordered by priority: packaging correctness and API consistency
first, then code quality, then polish.

---

## Priority 1: Packaging and Distribution (High)

These items affect anyone who installs or type-checks against the package.

### 1.1 Add `py.typed` marker file (Finding #4)

- Create an empty `src/stable_marriage/py.typed` file.
- Verify that `pip install -e .` makes mypy recognize the package as typed from
  a separate project.
- Exit criteria: `mypy` in a downstream project resolves `stable_marriage` types
  without `--ignore-missing-imports`.

### 1.2 Add `__main__.py` for `python -m stable_marriage` (Finding #5)

- Create `src/stable_marriage/__main__.py`:
  ```python
  """Allow execution via ``python -m stable_marriage``."""
  from stable_marriage.cli import main
  import sys
  raise SystemExit(main())
  ```
- Add a test that runs `python -m stable_marriage --input ...` via subprocess.
- Exit criteria: `python -m stable_marriage --input data/sample_preferences.json`
  works without the package being installed.

### 1.3 Expose `__version__` at runtime (Finding #6)

- Add to `src/stable_marriage/__init__.py`:
  ```python
  from importlib.metadata import version, PackageNotFoundError
  try:
      __version__ = version("stable-marriage")
  except PackageNotFoundError:
      __version__ = "0.0.0-dev"
  ```
- Add `__version__` to `__all__`.
- Add a test: `assert stable_marriage.__version__` is a non-empty string.
- Exit criteria: `python -c "import stable_marriage; print(stable_marriage.__version__)"` prints the version.

### 1.4 Add CI configuration or remove CI references (Finding #10)

- Option A (preferred): Add `.github/workflows/ci.yml` running lint, typecheck,
  and test on Python 3.11 and 3.12.
- Option B: Remove all CI references from `README.md:24` and `AGENTS.md:17`.
- Exit criteria: documentation accurately reflects CI state.

---

## Priority 2: Code Consistency (Medium)

These items improve internal consistency and modernize the codebase.

### 2.1 Replace deprecated `typing` imports with modern equivalents (Finding #1)

Files to update:
- `src/stable_marriage/experimental/couples.py`: Replace `Deque, Dict, List, Optional, Set, Tuple` with `deque` (from collections), `dict`, `list`, `set`, `tuple`, `X | None`.
- `tests/fixtures/preferences.py`: Replace `Dict, List, Sequence, Tuple`.
- `tests/fixtures/couples.py`: Replace `Dict, List, Tuple`.
- `tests/fixtures/residency.py`: Replace `Dict, List, Tuple`.
- `tests/fixtures/worst_case.py`: Replace `Dict, List, Tuple`.

Also update `EntityId = Tuple[str, Hashable]` to `EntityId = tuple[str, Hashable]`.

Exit criteria: no imports from `typing` except `TypeVar`, `cast`, and `TypeAlias`. All linting and type checking still pass.

### 2.2 Deduplicate `PreferenceProfile` type alias (Finding #7)

- Remove the duplicate definition in `tests/fixtures/residency.py`.
- Import `PreferenceProfile` from `tests/fixtures.preferences` in both
  `residency.py` and `worst_case.py`.
- Standardize on `tuple[dict[str, Sequence[str]], dict[str, Sequence[str]]]`.
- Exit criteria: `PreferenceProfile` is defined exactly once.

### 2.3 Fix `solver.py` shim `__all__` (Finding #8)

- Remove `_validate_inputs` from `__all__` in `src/stable_marriage/solver.py`.
- Keep the import for backward compatibility but do not advertise it as public.
- Exit criteria: `__all__` contains only intended public symbols.

### 2.4 Generalize `CoupleMapping` type or document the `str` restriction (Finding #3)

- Option A: Change `CoupleMapping = Mapping[str, Sequence[Person]]` to
  `Mapping[Hashable, Sequence[Person]]`.
- Option B: Add a docstring note explaining why couple IDs are `str` (e.g.,
  serialization constraints).
- Exit criteria: the type is either consistent with the rest of the API or
  explicitly documented.

---

## Priority 3: Couples Heuristic Improvements (Medium)

These items make the experimental couples API more robust and extensible.

### 3.1 Allow custom receiver-base parsing (Finding #2)

- Add an optional `base_fn: Callable[[Hashable], str] | None = None` parameter
  to `stable_marriage_with_couples()`.
- Default to `_receiver_base()` when `base_fn` is `None`.
- Document the default parsing rules in the docstring and in
  `docs/experimental-couples.md`.
- Add a test using a custom `base_fn`.
- Exit criteria: callers with non-standard receiver naming can use the couples
  heuristic without workarounds.

### 3.2 Add iteration bound to couples heuristic (Finding #11)

- Add an iteration counter to the `while queue:` loop in
  `_stable_marriage_with_couples()`.
- Set a conservative upper bound (e.g., `n * n * max(len(couples), 1)`).
- Raise `ValueError` with a clear message if the bound is exceeded.
- Document the expected complexity in the function docstring.
- Exit criteria: pathological inputs fail fast with a clear error instead of
  hanging.

### 3.3 Validate minimum couple size (Finding #18)

- Change the check in `_validate_couples()` from `if not members` to
  `if len(members) < 2`.
- Update the error message: "Couple {couple_id!r} must have at least two
  members."
- Add a test for single-member couples being rejected.
- Exit criteria: degenerate single-member couples are caught at validation time.

### 3.4 Document member-order dependency in `_select_couple_targets` (Finding #14)

- Add a note to the `_select_couple_targets()` docstring explaining that member
  iteration order affects which receiver each member gets.
- Add a sentence to `docs/experimental-couples.md` under "Known Failure Modes"
  or a new "Behavior Notes" section.
- Exit criteria: the order-dependence is documented for users and maintainers.

### 3.5 Add debug logging to couples heuristic (Finding #16)

- Add `logger = logging.getLogger(__name__)` to `couples.py`.
- Add `logger.debug()` at: entity creation, proposal, acceptance, rejection,
  displacement, and completion.
- Do not add logging to `core.py` (too simple to need it).
- Exit criteria: `logging.basicConfig(level=logging.DEBUG)` produces a readable
  trace of the heuristic's decisions.

---

## Priority 4: CLI Improvements (Low-Medium)

### 4.1 Support stdin as input source (Finding #9)

- Make `--input` optional.
- When omitted, read JSON from `sys.stdin`.
- Update `README.md` CLI section with a piping example.
- Add a test using `monkeypatch` on `sys.stdin`.
- Exit criteria: `echo '{"proposers":...}' | stable-marriage` works.

### 4.2 Eliminate duplicate validation in CLI path (Finding #15)

- Simplify `_canonicalize_preferences()` to only convert JSON arrays to Python
  lists without re-checking hashability and sequence type.
- Let the library's `validate_inputs()` handle all semantic validation.
- Ensure CLI-specific error messages (JSON structure, expected keys) are
  preserved.
- Exit criteria: preference validation logic exists in exactly one place.

---

## Priority 5: Documentation and Polish (Low)

### 5.1 Update `AGENTS.md` module examples (Finding #12)

- Replace the generic examples (`algorithms.py`, `matching.py`,
  `visualization/`) with actual module names: `core.py`, `validation.py`,
  `cli.py`, `experimental/couples.py`.
- Exit criteria: all file references in AGENTS.md correspond to real files.

### 5.2 Improve `CHANGELOG.md` (Finding #13)

- Add a `## 0.1.0` section summarizing the initial release.
- Add an `## [Unreleased]` section at the top for tracking in-progress changes.
- Consider adopting [Keep a Changelog](https://keepachangelog.com/) format.
- Exit criteria: the changelog reflects the full project history.

### 5.3 Improve `Matching` type alias clarity (Finding #17)

- Add `from typing import TypeAlias` and declare:
  ```python
  Matching: TypeAlias = dict[Hashable, Hashable]
  ```
- Or keep the `TypeVar` approach but add a comment explaining that the type
  safety comes from function signatures, not the alias itself.
- Exit criteria: the type alias intent is clear to readers and type checkers.

---

## Suggested PR grouping

| PR | Items | Theme |
| -- | ----- | ----- |
| PR 1 | 1.1, 1.2, 1.3 | Packaging completeness |
| PR 2 | 2.1, 2.2, 2.3, 2.4 | Code consistency |
| PR 3 | 3.1, 3.2, 3.3, 3.4, 3.5 | Couples heuristic hardening |
| PR 4 | 4.1, 4.2 | CLI improvements |
| PR 5 | 5.1, 5.2, 5.3, 1.4 | Documentation and CI |
