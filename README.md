# stable-marriage

Pure-Python utilities for solving the classical stable marriage problem.

## Status

- Supported public API: one-to-one stable marriage via Gale-Shapley.
- Experimental API: couples support is available under `stable_marriage.experimental` as a heuristic with narrower guarantees.
- Requires Python 3.11 or newer.
- CI currently runs on Python 3.11 and 3.12.

## Installation

For a fresh repository checkout, use an editable install:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

That installs the package from `src/` and makes the CLI entry module importable
from the repository root while also installing the development tools used in CI.

For a non-editable local install:

```bash
pip install .
```

## Quick start from a fresh checkout

After the editable install completes:

```bash
pytest
ruff check src tests
python -m stable_marriage.cli --input data/sample_preferences.json
```

Those commands should pass from the repository root in a clean local environment.

## Library usage

```python
from stable_marriage import stable_marriage

proposers = {
    "A": ["X", "Y", "Z"],
    "B": ["Y", "Z", "X"],
    "C": ["Y", "X", "Z"],
}

receivers = {
    "X": ["B", "C", "A"],
    "Y": ["C", "B", "A"],
    "Z": ["A", "B", "C"],
}

matches = stable_marriage(proposers, receivers)
```

## CLI usage

Because this project uses a `src/` layout, install the package first and then run:

```bash
python -m stable_marriage.cli --input data/sample_preferences.json
```

To write output to a file:

```bash
python -m stable_marriage.cli \
  --input data/sample_preferences.json \
  --output data/matching.json
```

Preference files are JSON objects with `proposers` and `receivers` keys whose
values map participant IDs to ranked lists of the opposite side.

## Experimental couples API

The project includes an experimental couples heuristic at
`stable_marriage.experimental.stable_marriage_with_couples`.

That heuristic is not part of the supported root API. A returned matching
represents the heuristic's result for the given input, while a `ValueError`
means the heuristic failed to find an acceptable assignment. It does not prove
that no stable assignment exists.

## Development

- Run tests with `make test`.
- Check style with `make lint`.
- Format changes with `make format`.
