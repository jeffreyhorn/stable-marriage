"""Core one-to-one stable marriage solver implementation."""

from __future__ import annotations

from collections import deque
from collections.abc import Mapping, Sequence

from .types import Person
from .validation import validate_inputs


def stable_marriage(
    proposers: Mapping[Person, Sequence[Person]],
    receivers: Mapping[Person, Sequence[Person]],
) -> dict[Person, Person]:
    """
    Compute a stable matching using the classical Gale-Shapley algorithm.

    Args:
        proposers: Mapping of proposer identifiers to their ordered preference lists.
        receivers: Mapping of receiver identifiers to their ordered preference lists.

    Returns:
        Dict mapping each proposer to the receiver they are matched with.

    Raises:
        ValueError: If preference lists are inconsistent or omit required
            participants.

    This is the supported public solver for one-to-one stable marriage. It runs
    in :math:`O(n^2)` time for :math:`n` participants on each side.
    """

    validate_inputs(proposers, receivers)
    return _stable_marriage_one_to_one(proposers, receivers)


def _stable_marriage_one_to_one(
    proposers: Mapping[Person, Sequence[Person]],
    receivers: Mapping[Person, Sequence[Person]],
) -> dict[Person, Person]:
    """Classical Gale-Shapley solver without couple constraints."""

    free_proposers = deque(proposers.keys())
    next_choice_index = {proposer: 0 for proposer in proposers}

    receiver_rankings = {
        receiver: {proposer: rank for rank, proposer in enumerate(preferences)}
        for receiver, preferences in receivers.items()
    }

    engagements: dict[Person, Person] = {}

    while free_proposers:
        proposer = free_proposers.popleft()
        preferences = proposers[proposer]

        if next_choice_index[proposer] >= len(preferences):
            raise ValueError(
                f"Proposer {proposer!r} exhausted all preferences without a match."
            )

        receiver = preferences[next_choice_index[proposer]]
        next_choice_index[proposer] += 1

        current_partner = engagements.get(receiver)
        if current_partner is None:
            engagements[receiver] = proposer
            continue

        current_rank = receiver_rankings[receiver][current_partner]
        challenger_rank = receiver_rankings[receiver][proposer]

        if challenger_rank < current_rank:
            engagements[receiver] = proposer
            free_proposers.append(current_partner)
        else:
            free_proposers.append(proposer)

    return {proposer: receiver for receiver, proposer in engagements.items()}


__all__ = ["stable_marriage"]
