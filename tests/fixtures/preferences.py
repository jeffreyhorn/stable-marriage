"""Reusable preference profiles for stable marriage tests."""

from __future__ import annotations

from collections.abc import Sequence

PreferenceProfile = tuple[dict[str, Sequence[str]], dict[str, Sequence[str]]]


def make_unique_matching_preferences() -> PreferenceProfile:
    """
    Return a 3x3 profile where the stable matching is unique.

    The uniqueness ensures that role-swapping tests can assert a single outcome.
    """

    proposers = {
        "A": ["Z", "Y", "X"],
        "B": ["X", "Z", "Y"],
        "C": ["Y", "X", "Z"],
    }

    receivers = {
        "X": ["B", "A", "C"],
        "Y": ["C", "B", "A"],
        "Z": ["A", "C", "B"],
    }

    return proposers, receivers


def make_invalid_roster_preferences() -> tuple[
    dict[str, Sequence[str]],
    dict[str, Sequence[str]],
]:
    """Return mismatched rosters to trigger participant count validation."""

    proposers = {
        "A": ["X", "Y"],
        "B": ["Y", "X"],
    }

    receivers = {
        "X": ["A", "B"],
    }

    return proposers, receivers


def make_invalid_preference_profiles() -> list[PreferenceProfile]:
    """Return preference sets that contain duplicate entries or omissions."""

    duplicate_receiver_entry = (
        {
            "A": ["X", "X", "Y"],
            "B": ["Y", "Z", "X"],
            "C": ["Z", "X", "Y"],
        },
        {
            "X": ["A", "B", "C"],
            "Y": ["B", "C", "A"],
            "Z": ["C", "A", "B"],
        },
    )

    missing_receiver = (
        {
            "A": ["X", "Y"],
            "B": ["Y", "X"],
            "C": ["Z", "Y"],
        },
        {
            "X": ["A", "B", "C"],
            "Y": ["B", "C", "A"],
            "Z": ["C", "A", "B"],
        },
    )

    missing_proposer = (
        {
            "A": ["X", "Y", "Z"],
            "B": ["Y", "Z", "X"],
            "C": ["Z", "X", "Y"],
        },
        {
            "X": ["A", "B", "C"],
            "Y": ["B", "C", "A"],
            # Receiver omits proposer "C"
            "Z": ["A", "B", "A"],
        },
    )

    return [duplicate_receiver_entry, missing_receiver, missing_proposer]
