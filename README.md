# stable-marriage

Pure-Python utilities for solving the classical stable marriage problem.

## Status

- Supported public API: one-to-one stable marriage via Gale-Shapley.
- Experimental API: couples support is available under `stable_marriage.experimental` as a heuristic with narrower guarantees.
- Supported Python versions: 3.11+.

## Installation

For local development from this repository:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

For a non-editable local install:

```bash
pip install .
```

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

Install the package first, then run:

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

- Run tests with `pytest`.
- Check style with `ruff check src tests`.
- Format changes with `ruff format src tests`.
