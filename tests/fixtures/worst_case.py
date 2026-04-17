"""Worst-case instances for the Gale–Shapley algorithm."""

from __future__ import annotations

from typing import Dict, List, Tuple

PreferenceProfile = Tuple[Dict[str, List[str]], Dict[str, List[str]]]


def make_worst_case_preferences(size: int = 10) -> PreferenceProfile:
    """
    Build Irving's worst-case instance for the proposer-optimal Gale–Shapley run.

    The construction forces proposers to cycle through roughly :math:`n^2 / 2`
    proposals before convergence, offering a regression harness for performance
    and stability checks.
    """

    if size <= 1:
        raise ValueError("size must be greater than 1 to form a meaningful instance.")

    width = max(2, len(str(size - 1)))
    proposers = [f"M{i:0{width}d}" for i in range(size)]
    receivers = [f"W{i:0{width}d}" for i in range(size)]

    proposer_preferences: Dict[str, List[str]] = {
        proposer: receivers[:] for proposer in proposers
    }

    receiver_preferences: Dict[str, List[str]] = {}
    for idx, receiver in enumerate(receivers):
        # Women prefer earlier-indexed proposers first (in reverse order),
        # then wrap to the remaining proposers descending from the end.
        prefix = [proposers[i] for i in range(idx - 1, -1, -1)]
        suffix = [proposers[i] for i in range(size - 1, idx - 1, -1)]
        receiver_preferences[receiver] = prefix + suffix

    return proposer_preferences, receiver_preferences
