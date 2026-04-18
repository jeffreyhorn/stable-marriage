# stable-marriage

Pure-Python utilities for solving the classical stable marriage problem with
the Gale-Shapley algorithm.

## Overview

`stable-marriage` is a small library and CLI for the one-to-one stable
marriage problem. The supported public API is the classical
`stable_marriage(...)` solver.

The package also includes an experimental couples heuristic under
`stable_marriage.experimental`, but that workflow is not part of the supported
root API and is not exposed through the CLI. See
[`docs/experimental-couples.md`](docs/experimental-couples.md) for its exact
model and limitations.

## Status

- Supported public API: one-to-one stable marriage via Gale-Shapley.
- Experimental API: couples support is available under
  `stable_marriage.experimental` as a heuristic with narrower guarantees.
- Requires Python 3.11 or newer.
- CI currently runs on Python 3.11 and 3.12.

## Installation

For a fresh repository checkout, use an editable install:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

That installs the package from `src/`, makes the `stable-marriage` CLI
available in the active environment, and installs the development tools used in
CI.

For a non-editable local install:

```bash
pip install .
```

## Quick Start

After the editable install completes:

```bash
pytest
ruff check src tests
stable-marriage --input data/sample_preferences.json
```

Those commands should pass from the repository root in a clean local
environment.

## Python API

```python
import json

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
print(json.dumps(matches, sort_keys=True))
```

Example JSON output:

```json
{"A": "X", "B": "Z", "C": "Y"}
```

The solver expects complete strict preference lists on both sides:

- Every proposer must rank every receiver exactly once.
- Every receiver must rank every proposer exactly once.
- The two sides must contain the same number of participants.

If those requirements are not met, the solver raises `ValueError`.

## CLI

Because this project uses a `src/` layout, install the package first and then
run:

```bash
stable-marriage --input data/sample_preferences.json
```

Write the matching to a file:

```bash
stable-marriage \
  --input data/sample_preferences.json \
  --output data/matching.json
```

Emit compact JSON for shell pipelines:

```bash
stable-marriage \
  --input data/sample_preferences.json \
  --indent 0
```

The installed CLI intentionally supports only the classical one-to-one solver.
It rejects experimental couples input; use the library API for that workflow.

### Exit behavior

- Exit code `0`: successful solve and output write.
- Exit code `1`: invalid input or expected file I/O errors such as malformed
  JSON, unreadable input, or unwritable output paths.

## Input JSON Schema

The CLI expects a JSON object with exactly two top-level keys:

- `proposers`: object mapping proposer IDs to ordered arrays of receiver IDs
- `receivers`: object mapping receiver IDs to ordered arrays of proposer IDs

Schema shape:

```json
{
  "proposers": {
    "<proposer-id>": ["<receiver-id-1>", "<receiver-id-2>"]
  },
  "receivers": {
    "<receiver-id>": ["<proposer-id-1>", "<proposer-id-2>"]
  }
}
```

Rules:

- Participant IDs must be JSON scalars that become hashable Python values in
  the loaded data. In practice, string IDs are the expected format.
- Preference values must be JSON arrays.
- Each participant must rank the full opposite side exactly once.
- The CLI rejects extra top-level keys such as `couples`.

Reference input file:

```json
{
  "proposers": {
    "A": ["X", "Y", "Z"],
    "B": ["Y", "Z", "X"],
    "C": ["Y", "X", "Z"]
  },
  "receivers": {
    "X": ["B", "C", "A"],
    "Y": ["C", "B", "A"],
    "Z": ["A", "B", "C"]
  }
}
```

This same example is checked into
[`data/sample_preferences.json`](data/sample_preferences.json).

## Output JSON

The CLI writes a single JSON object mapping each proposer to its assigned
receiver:

```json
{
  "A": "X",
  "B": "Z",
  "C": "Y"
}
```

## Experimental Couples API

The project includes an experimental couples heuristic at
`stable_marriage.experimental.stable_marriage_with_couples`.

That heuristic is not part of the supported root API. When it returns, it:

- assigns each proposer to one receiver
- avoids double-assigning receivers
- keeps each couple on distinct receivers from the same derived base

It does not guarantee a stable matching for the general couples problem, and a
`ValueError` only means the heuristic failed on that input. It does not prove
that no acceptable assignment exists.

For the exact model, failure modes, and constraints, see
[`docs/experimental-couples.md`](docs/experimental-couples.md).

## Development

- Run tests with `make test`.
- Check style with `make lint`.
- Format changes with `make format`.
