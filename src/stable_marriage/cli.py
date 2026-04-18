"""Command-line entry point for computing stable matchings from JSON input."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Hashable, Mapping, Sequence
from pathlib import Path
from typing import Any, cast

from .core import stable_marriage
from .types import Matching


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Construct the CLI argument parser and parse arguments."""

    parser = argparse.ArgumentParser(
        description="Compute a stable matching using the Gale–Shapley algorithm.",
    )
    parser.add_argument(
        "--input",
        "-i",
        type=Path,
        help="Optional path to a JSON file with `proposers` and `receivers`; defaults to stdin.",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        help="Optional path to write the resulting matching as JSON; defaults to stdout.",
    )
    parser.add_argument(
        "--indent",
        type=int,
        default=2,
        help="Indent level for JSON output (default: 2).",
    )
    return parser.parse_args(argv)


def load_preferences(
    path: Path | None,
) -> tuple[dict[Hashable, list[Any]], dict[Hashable, list[Any]]]:
    """Load and validate proposer and receiver preferences from a file or stdin."""

    if path is None:
        if sys.stdin.isatty():
            raise ValueError(
                "No input provided on stdin. Pass --input PATH or pipe JSON to stdin."
            )
        try:
            stdin_text = sys.stdin.read()
        except OSError as exc:
            raise ValueError(f"Unable to read input from stdin: {exc}") from exc
        if not stdin_text.strip():
            raise ValueError(
                "No input provided on stdin. Pass --input PATH or pipe JSON to stdin."
            )
        try:
            raw = json.loads(stdin_text)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Standard input is not valid JSON: {exc}") from exc
    else:
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise ValueError(f"Input file {path} does not exist.") from exc
        except OSError as exc:
            raise ValueError(f"Unable to read input file {path}: {exc}") from exc
        except json.JSONDecodeError as exc:
            raise ValueError(f"Input file {path} is not valid JSON: {exc}") from exc

    if not isinstance(raw, dict):
        raise ValueError("Preference file must be a JSON object.")

    expected_keys = {"proposers", "receivers"}
    unexpected_keys = sorted(set(raw) - expected_keys)
    if unexpected_keys:
        if unexpected_keys == ["couples"]:
            raise ValueError(
                "The CLI supports only one-to-one inputs; experimental couples "
                "input is available only through "
                "`stable_marriage.experimental.stable_marriage_with_couples(...)`."
            )
        formatted_keys = ", ".join(repr(key) for key in unexpected_keys)
        raise ValueError(
            "Preference file contains unsupported top-level keys: "
            f"{formatted_keys}. Only 'proposers' and 'receivers' are accepted."
        )

    try:
        proposers = raw["proposers"]
        receivers = raw["receivers"]
    except KeyError as exc:
        raise ValueError(
            "Preference file must contain 'proposers' and 'receivers' keys."
        ) from exc

    if not isinstance(proposers, Mapping) or not isinstance(receivers, Mapping):
        raise ValueError("'proposers' and 'receivers' must be JSON objects.")

    normalized_proposers = _canonicalize_preferences(proposers, "proposers")
    normalized_receivers = _canonicalize_preferences(receivers, "receivers")

    return normalized_proposers, normalized_receivers


def _canonicalize_preferences(
    raw_preferences: Mapping[Any, Any],
    label: str,
) -> dict[Hashable, list[Any]]:
    """
    Ensure preference values are JSON arrays and normalize them to Python lists.

    Args:
        raw_preferences: Mapping from participant IDs to their raw preference values.
        label: Human-readable label for error messages.

    Raises:
        ValueError: If a participant's preferences are not represented as a JSON
            array.
    """

    canonical: dict[Hashable, list[Any]] = {}

    for participant, preferences in raw_preferences.items():
        if not isinstance(preferences, list):
            raise ValueError(
                f"{label} preference list for {participant!r} must be a JSON array of identifiers."
            )

        canonical[cast(Hashable, participant)] = list(preferences)

    return canonical


def dump_matching(matching: Matching, output_path: Path | None, indent: int) -> None:
    """Serialize the matching to disk or stdout."""

    effective_indent = indent if indent > 0 else None
    if effective_indent is None:
        payload = json.dumps(matching, sort_keys=True, separators=(",", ":"))
    else:
        payload = json.dumps(matching, indent=effective_indent, sort_keys=True)

    if output_path is None:
        print(payload)
        return

    try:
        output_path.write_text(payload + "\n", encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"Unable to write matching to {output_path}: {exc}") from exc


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point for `stable-marriage` or `python -m stable_marriage.cli`."""

    args = parse_args(argv)

    try:
        proposers, receivers = load_preferences(args.input)
        matching = stable_marriage(
            cast(Mapping[Hashable, Sequence[Hashable]], proposers),
            cast(Mapping[Hashable, Sequence[Hashable]], receivers),
        )
        dump_matching(matching, args.output, args.indent)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":  # pragma: no cover - direct CLI execution
    raise SystemExit(main(sys.argv[1:]))
