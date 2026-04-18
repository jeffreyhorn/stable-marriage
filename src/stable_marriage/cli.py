"""Command-line entry point for computing stable matchings from JSON input."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Hashable, Mapping, Sequence
from pathlib import Path
from typing import Any

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
        required=True,
        help="Path to a JSON file with `proposers` and `receivers` preference maps.",
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
    path: Path,
) -> tuple[dict[Hashable, list[Hashable]], dict[Hashable, list[Hashable]]]:
    """Load and validate proposer and receiver preferences from a UTF-8 JSON file."""

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
) -> dict[Hashable, list[Hashable]]:
    """
    Ensure preference lists are sequences of hashable identifiers.

    Args:
        raw_preferences: Mapping from participant IDs to their raw preference values.
        label: Human-readable label for error messages.

    Raises:
        ValueError: If a participant key is unhashable, their preferences are not a
            sequence (list/tuple), or contain non-hashable members.
    """

    canonical: dict[Hashable, list[Hashable]] = {}

    for participant, preferences in raw_preferences.items():
        if not isinstance(participant, Hashable):
            raise ValueError(
                f"{label} keys must be hashable identifiers; got {participant!r}."
            )

        if not isinstance(preferences, Sequence) or isinstance(
            preferences, (str, bytes)
        ):
            raise ValueError(
                f"{label} preference list for {participant!r} must be a JSON array of identifiers."
            )

        canonical_preferences: list[Hashable] = []
        for option in preferences:
            if not isinstance(option, Hashable):
                raise ValueError(
                    f"{label} preference for {participant!r} contains non-hashable value {option!r}."
                )
            canonical_preferences.append(option)

        canonical[participant] = canonical_preferences

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
    """CLI entry point for the installed `stable-marriage` console script."""

    args = parse_args(argv)

    try:
        proposers, receivers = load_preferences(args.input)
        matching = stable_marriage(proposers, receivers)
        dump_matching(matching, args.output, args.indent)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":  # pragma: no cover - direct CLI execution
    raise SystemExit(main(sys.argv[1:]))
