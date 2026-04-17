"""Residency-style preference profiles with larger rosters for testing."""

from __future__ import annotations

from typing import Dict, List, Tuple

PreferenceProfile = Tuple[Dict[str, List[str]], Dict[str, List[str]]]


def make_residency_preferences(size: int = 20) -> PreferenceProfile:
    """
    Construct a residency-style preference profile of the requested size.

    Each proposer rotates the receiver list to create varied but deterministic
    preferences, and receivers mirror the pattern to avoid degenerate matchings.
    """

    if size <= 0:
        raise ValueError("size must be a positive integer.")

    width = max(2, len(str(size - 1)))
    proposers = [f"P{i:0{width}d}" for i in range(size)]
    receivers = [f"R{i:0{width}d}" for i in range(size)]

    proposer_preferences: Dict[str, List[str]] = {}
    for idx, proposer in enumerate(proposers):
        rotation = receivers[idx:] + receivers[:idx]
        proposer_preferences[proposer] = rotation

    receiver_preferences: Dict[str, List[str]] = {}
    for idx, receiver in enumerate(receivers):
        rotation = proposers[idx:] + proposers[:idx]
        receiver_preferences[receiver] = rotation

    return proposer_preferences, receiver_preferences
