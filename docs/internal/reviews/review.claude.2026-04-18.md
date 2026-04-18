# Code Review: `stable_marriage`

Date: 2026-04-18
Reviewer: Claude (Opus 4.6)

## Scope

Full codebase review covering:
- `src/stable_marriage/` (all modules)
- `tests/` (all test files and fixtures)
- `data/`
- `pyproject.toml`, `Makefile`
- `README.md`, `AGENTS.md`, `CHANGELOG.md`
- `docs/`

## Validation performed

- `pytest` -> 54 passed
- `pytest --cov=stable_marriage --cov-report=term-missing` -> 98% coverage
- `ruff check src/ tests/` -> passed
- `mypy src/` -> passed, no issues found in 8 source files
- `black --check src/ tests/` -> passed, 17 files unchanged

## Context: prior review

A previous review (`review.codex.2026-04-17`) identified 10 findings. The
majority have been addressed through PRs #1 and #2:
- API narrowing (couples moved to experimental) -- done
- Python version contract -- fixed to >=3.11
- README and onboarding -- created
- Module split (solver.py decomposed) -- done
- `_receiver_base()` hyphenated parsing -- fixed and tested
- Internal entity ID collisions -- fixed with opaque tuple keys
- CLI/library boundary clarity -- done
- CLI file-I/O error handling -- done (OSError, UTF-8)
- Repository structure -- cleaned
- Test coverage alignment -- now 98%

This review focuses on remaining issues and newly identified concerns.

---

## Findings

### 1. Medium: deprecated typing imports throughout `experimental/couples.py` and test fixtures

**Evidence:**
- `src/stable_marriage/experimental/couples.py:7` imports `Deque, Dict, List, Optional, Set, Tuple, cast` from `typing`.
- `tests/fixtures/preferences.py:5` imports `Dict, List, Sequence, Tuple` from `typing`.
- `tests/fixtures/couples.py:5` imports `Dict, List, Tuple` from `typing`.
- `tests/fixtures/residency.py:5` and `tests/fixtures/worst_case.py:5` do the same.

**Why this matters:**
- The project declares `requires-python = ">=3.11"` and uses modern syntax (`dict[K, V]`, `X | None`) everywhere else. These legacy imports are inconsistent.
- `typing.Deque`, `typing.Dict`, `typing.List`, `typing.Optional`, `typing.Set`, `typing.Tuple` have been deprecated since Python 3.9 (PEP 585).
- Mixing old and new syntax creates confusion about which style to follow.

**Impact:** Code consistency and maintainability.

**Recommendation:**
- Replace all deprecated typing imports with built-in generics and `collections.abc` equivalents.
- `Dict` -> `dict`, `List` -> `list`, `Tuple` -> `tuple`, `Set` -> `set`, `Deque` -> `deque` (from collections), `Optional[X]` -> `X | None`.

### 2. Medium: `_receiver_base()` parsing remains inherently fragile

**Evidence:**
- `src/stable_marriage/experimental/couples.py:372-395` derives base identifiers from receiver labels using string suffix heuristics.
- The logic only recognizes two patterns: single-alpha suffix (`_A`) and `Slot`-prefixed suffix (`-SlotA`).
- Receivers like `Hospital_North`, `Room_12`, or `Ward-3B` would either not be parsed or would be mis-parsed.
- There is no way for callers to supply their own parsing logic or provide explicit base metadata.

**Why this matters:**
- Couple placement depends entirely on correct base extraction.
- The suffix convention is not documented in the public API or enforced at validation time. Users must guess the naming rules or read the source.
- The heuristic fails silently -- a mis-parsed receiver just appears as its own base, causing couple validation to fail with a confusing error about missing bases.

**Impact:** Correctness and usability of the couples heuristic.

**Recommendation:**
- Accept an optional `base_fn: Callable[[Hashable], str]` parameter so callers can supply their own parsing.
- Alternatively, accept a `receiver_bases: Mapping[Person, str]` parameter that provides explicit base assignments, falling back to the heuristic only when not provided.
- Document the naming convention requirements clearly in the experimental API docs.

### 3. Medium: `CoupleMapping` requires `str` keys while the rest of the API is generic

**Evidence:**
- `src/stable_marriage/experimental/couples.py:12`: `CoupleMapping = Mapping[str, Sequence[Person]]`
- The core API is generic over any `Hashable` type for participant IDs, but couple IDs are restricted to `str`.
- No documentation explains why couple IDs must be strings.

**Why this matters:**
- Users who use integer or tuple IDs for proposers/receivers cannot use the same ID scheme for couples without converting to strings.
- The asymmetry suggests an oversight rather than a deliberate design choice.

**Impact:** API consistency.

**Recommendation:**
- Either generalize `CoupleMapping` to `Mapping[Hashable, Sequence[Person]]` or document the `str` restriction and the reason for it.

### 4. Medium: no `py.typed` marker file

**Evidence:**
- The package provides complete type annotations across all modules.
- There is no `py.typed` marker file in `src/stable_marriage/`.
- `pyproject.toml` does not configure `package-data` to include `py.typed`.

**Why this matters:**
- PEP 561 requires a `py.typed` marker for type checkers (mypy, pyright) to recognize the package as typed when installed as a dependency.
- Without it, downstream consumers lose all type-checking benefits.

**Impact:** Type safety for consumers.

**Recommendation:**
- Add an empty `src/stable_marriage/py.typed` file.
- Ensure it is included in the package distribution (setuptools includes it by default with `find` packages).

### 5. Medium: no `__main__.py` for `python -m stable_marriage` execution

**Evidence:**
- `src/stable_marriage/cli.py:172-173` supports `python -m stable_marriage.cli` via `if __name__ == "__main__"`.
- There is no `src/stable_marriage/__main__.py`.
- The conventional invocation `python -m stable_marriage` does not work.

**Why this matters:**
- `python -m <package>` is the standard way to run a package as a script (PEP 338).
- The current `python -m stable_marriage.cli` is less discoverable and non-standard.
- Users who haven't installed the package (e.g., during development before `pip install -e`) can't easily run the CLI.

**Impact:** Developer ergonomics and convention compliance.

**Recommendation:**
- Add `src/stable_marriage/__main__.py` that imports and calls `cli.main()`.

### 6. Medium: no runtime version attribute

**Evidence:**
- `pyproject.toml:7` declares `version = "0.2.0"`.
- `src/stable_marriage/__init__.py` does not expose `__version__`.
- There is no way to check the installed version at runtime (e.g., `stable_marriage.__version__`).

**Why this matters:**
- Runtime version introspection is a common need for debugging, logging, and compatibility checks.
- Users cannot programmatically determine which version they are running.

**Impact:** Operational convenience.

**Recommendation:**
- Add `__version__` to `__init__.py` using `importlib.metadata.version("stable-marriage")` or a static string synchronized with `pyproject.toml`.

### 7. Low-Medium: `PreferenceProfile` type alias defined in two places

**Evidence:**
- `tests/fixtures/preferences.py:7`: `PreferenceProfile = Tuple[Dict[str, Sequence[str]], Dict[str, Sequence[str]]]`
- `tests/fixtures/residency.py:7`: `PreferenceProfile = Tuple[Dict[str, List[str]], Dict[str, List[str]]]`

**Why this matters:**
- The two definitions use different inner types (`Sequence[str]` vs `List[str]`), making them technically different types.
- This violates DRY and makes refactoring error-prone.

**Impact:** Maintainability.

**Recommendation:**
- Define `PreferenceProfile` once in `tests/fixtures/__init__.py` or `tests/fixtures/preferences.py` and import it in `residency.py` and `worst_case.py`.
- Use `Sequence[str]` consistently (broader type).

### 8. Low-Medium: `solver.py` compatibility shim exports a private symbol in `__all__`

**Evidence:**
- `src/stable_marriage/solver.py:9`: `__all__ = ["Matching", "stable_marriage", "_validate_inputs"]`

**Why this matters:**
- `_validate_inputs` has an underscore prefix, signaling it is private.
- Including it in `__all__` contradicts that signal.
- This creates confusion about whether the symbol is part of the supported API.

**Impact:** API clarity.

**Recommendation:**
- Either rename it to `validate_inputs` (without underscore) in the shim if it is intended to be public, or remove it from `__all__`.

### 9. Low-Medium: CLI does not support stdin input

**Evidence:**
- `src/stable_marriage/cli.py:22-28` requires `--input` as a mandatory file path argument.
- There is no way to pipe JSON via stdin (`echo '...' | stable-marriage`).

**Why this matters:**
- Unix convention expects CLI tools to accept stdin when no file is specified.
- The README documents `--indent 0` as being for "shell pipelines" but the tool cannot participate in a full pipeline.

**Impact:** CLI composability and Unix convention compliance.

**Recommendation:**
- Make `--input` optional, defaulting to stdin when omitted.
- Use `sys.stdin` or `-` as the sentinel value.

### 10. Low-Medium: no CI configuration in the repository

**Evidence:**
- `README.md:24` states "CI currently runs on Python 3.11 and 3.12."
- `AGENTS.md:17` states "CI currently validates the project on Python 3.11 and 3.12."
- There is no `.github/workflows/`, `.gitlab-ci.yml`, or equivalent CI configuration file in the repository.

**Why this matters:**
- The documentation references CI as if it exists, but there is no way for contributors to verify what CI runs or reproduce it locally.
- Without CI, there is no automated enforcement of linting, type checking, or test passage on push/PR.

**Impact:** Development workflow reliability and documentation accuracy.

**Recommendation:**
- Either add a CI configuration (GitHub Actions is the natural choice) or remove CI references from documentation until one exists.

### 11. Low-Medium: couples heuristic has no cycle detection or iteration bound

**Evidence:**
- `src/stable_marriage/experimental/couples.py:151-227` runs a `while queue:` loop.
- `next_choice_index` advances monotonically per entity, bounding individual entity iterations.
- However, `release_entity()` requeues displaced entities with their current `next_choice_index` preserved, meaning an entity can be dequeued and re-enqueued many times at the same preference index.
- There is no overall iteration counter, no cycle detection, and no documentation of the worst-case iteration bound.

**Why this matters:**
- While the algorithm appears to terminate (each entity can only advance through its preferences), the interaction between couple and single entities during displacement could lead to pathological performance.
- The lack of an explicit bound or proof makes it hard to reason about worst-case behavior.

**Impact:** Performance predictability for the experimental API.

**Recommendation:**
- Add an iteration counter with a conservative upper bound (e.g., `O(n^2 * k)` where `k` is the number of couples).
- Document the expected complexity in the docstring.
- Raise a clear error if the bound is exceeded, indicating possible infinite loop.

### 12. Low: `AGENTS.md` references non-existent modules as examples

**Evidence:**
- `AGENTS.md:4` says: "grouping algorithms, utilities, and CLI entry points by feature (e.g., `algorithms.py`, `matching.py`, `visualization/`)."
- None of these files exist in the project.

**Why this matters:**
- Contributors reading AGENTS.md may look for these files or create them thinking they are part of the expected structure.
- Examples in contributor guides should reflect reality.

**Impact:** Contributor onboarding clarity.

**Recommendation:**
- Update the examples to reference actual modules: `core.py`, `validation.py`, `cli.py`, `experimental/couples.py`.

### 13. Low: `CHANGELOG.md` has no historical entries and doesn't follow a standard format

**Evidence:**
- `CHANGELOG.md` documents only v0.2.0 with three bullet points.
- No v0.1.0 or earlier entries exist.
- Does not follow Keep a Changelog format or link to diffs.

**Why this matters:**
- Users and contributors cannot understand the project's evolution.
- Missing historical context makes it hard to assess stability.

**Impact:** Project transparency.

**Recommendation:**
- Add a v0.1.0 entry summarizing the initial release.
- Consider adopting Keep a Changelog format with `[Unreleased]` section.

### 14. Low: `_select_couple_targets()` greedy assignment is order-dependent

**Evidence:**
- `src/stable_marriage/experimental/couples.py:338-369` assigns receivers to couple members in iteration order.
- The first member in the couple list gets priority for their preferred receiver at a base.
- If member A and member B both prefer receiver `H1_A`, member A always gets it.

**Why this matters:**
- The assignment depends on the order members appear in the couples mapping, which is an undocumented, arbitrary input detail.
- A different ordering of the same couple members could produce different results.

**Impact:** Result determinism and fairness within couples.

**Recommendation:**
- Document that member order within a couple affects target selection.
- Consider using receiver rankings to break ties instead of member order.

### 15. Low: duplicate validation between CLI and core

**Evidence:**
- `src/stable_marriage/cli.py:93-134` (`_canonicalize_preferences`) validates hashability and sequence type.
- `src/stable_marriage/validation.py:54-73` (`_ensure_preference_sequence`) validates the same properties.
- When `cli.main()` calls `stable_marriage()`, the data is validated twice.

**Why this matters:**
- Double validation adds unnecessary overhead and creates two places where validation error messages must be maintained.
- The CLI validation produces different error messages than the library validation for the same failure.

**Impact:** Maintainability and performance (minor).

**Recommendation:**
- Have the CLI validate only CLI-specific concerns (JSON structure, expected keys) and delegate all preference validation to the library.
- Or, have `_canonicalize_preferences` produce data that is guaranteed to pass library validation, making the library validation a no-op.

### 16. Low: no logging anywhere in the library

**Evidence:**
- No module imports `logging` or produces any log output.
- The couples heuristic in particular involves complex multi-step iteration that is difficult to debug without tracing.

**Why this matters:**
- Users debugging why the couples heuristic fails on their data have no visibility into the algorithm's decision-making.
- Library consumers cannot enable debug logging to understand behavior.

**Impact:** Debuggability.

**Recommendation:**
- Add `logger = logging.getLogger(__name__)` to key modules.
- Add `logger.debug()` calls at proposal/rejection/displacement points in the couples heuristic.
- Do not add logging to the core one-to-one solver (it is simple enough to not need it).

### 17. Low: `Matching` type alias using `TypeVar` is not meaningful at the type level

**Evidence:**
- `src/stable_marriage/types.py:8-9`:
  ```python
  Person = TypeVar("Person", bound=Hashable)
  Matching = dict[Person, Person]
  ```
- `Person` is a free `TypeVar` in the type alias, which means `Matching` is effectively `dict[Any, Any]` to type checkers.

**Why this matters:**
- The type alias provides a false sense of type safety. Type checkers cannot enforce that keys and values are the same `Person` type.
- The `TypeVar` only constrains when used in a function signature (e.g., `def f(x: Mapping[Person, Sequence[Person]]) -> Matching`).

**Impact:** Type safety (cosmetic; the functions themselves are correctly typed).

**Recommendation:**
- Consider using `TypeAlias` from `typing` to make the intent explicit.
- Or define `Matching` as a simple `TypeAlias`: `Matching: TypeAlias = dict[Hashable, Hashable]`.
- The function signatures already use `Person` correctly and provide the actual type safety.

### 18. Low: single-member couples are silently accepted

**Evidence:**
- `src/stable_marriage/experimental/couples.py:269` only checks `if not members`, allowing a couple with exactly one member.
- A single-member couple is semantically equivalent to a single proposer, but processes through the couple code path.

**Why this matters:**
- This is likely an oversight rather than intentional behavior.
- A single-member "couple" goes through base-preference extraction and couple proposal logic unnecessarily.
- It could silently mask user errors where a second member was intended.

**Impact:** Input validation completeness.

**Recommendation:**
- Require `len(members) >= 2` for a couple, or document that single-member couples are valid and explain the semantics.

---

## Scorecard

| Area | Assessment |
| --- | --- |
| Correctness | Strong for one-to-one Gale-Shapley; couples heuristic is correctly scoped as experimental with honest documentation of limitations. |
| Efficiency | Core algorithm is optimal O(n^2); couples heuristic lacks formal complexity analysis. |
| Architecture | Clean module separation after the recent refactor. The experimental namespace is well-conceived. |
| Code Quality | Generally good. Inconsistent typing style (old vs new) is the main blemish. |
| Documentation | Good README, clear API docs, honest experimental caveats. AGENTS.md has stale examples. CI references are inaccurate. |
| Maintainability | Good. Small modules, clear responsibilities. Duplicate validation and duplicate type aliases are minor concerns. |
| Testability | Excellent. 98% coverage, 54 tests, good fixture organization, property-based and worst-case testing. |
| Packaging | Functional but missing `py.typed`, `__main__.py`, and `__version__`. No actual CI despite documentation claims. |

## Strengths

- The core Gale-Shapley implementation is textbook-quality: small, correct, and efficiently structured.
- The previous review's findings were addressed comprehensively. The codebase improved significantly between the two reviews.
- Test suite is exemplary for a library this size: stability assertions, randomized testing, worst-case performance bounds, CLI integration tests, and edge-case coverage.
- The experimental namespace pattern is well-executed. The couples heuristic is honestly documented with clear non-guarantees.
- Error messages throughout are specific and actionable.
- Zero external dependencies for the core library.

## Overall Assessment

The codebase is in good shape following the remediation work from the prior review. The classical one-to-one solver is production-quality. The remaining issues are predominantly in the "polish" category: modernizing typing, adding packaging best practices (`py.typed`, `__main__.py`, `__version__`), and improving the couples heuristic's extensibility and documentation. The most actionable improvement would be modernizing the deprecated typing imports for consistency and adding the missing packaging artifacts. The couples heuristic's reliance on naming-convention parsing remains the biggest design concern, but it is appropriately quarantined in the experimental namespace.
