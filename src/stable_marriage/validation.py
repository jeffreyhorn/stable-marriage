"""Validation helpers shared across stable_marriage solver entry points."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import cast

from .types import Person


def validate_inputs(
    proposers: Mapping[Person, Sequence[Person]],
    receivers: Mapping[Person, Sequence[Person]],
) -> None:
    """
    Ensure participant rosters and preference lists are structurally sound.

    Args:
        proposers: Mapping of proposers to their ordered preferences.
        receivers: Mapping of receivers to their ordered preferences.

    Raises:
        ValueError: If either side is empty, the rosters differ in size, or
            any participant omits or duplicates members of the opposite side.
    """

    try:
        proposer_ids = set(proposers.keys())
        receiver_ids = set(receivers.keys())
    except TypeError as exc:
        raise ValueError("Participant identifiers must be hashable.") from exc

    if not proposer_ids:
        raise ValueError("At least one proposer is required.")

    if not receiver_ids:
        raise ValueError("At least one receiver is required.")

    if len(proposer_ids) != len(receiver_ids):
        raise ValueError("The number of proposers must equal the number of receivers.")

    expected_receivers = receiver_ids
    expected_proposers = proposer_ids

    for proposer, preferences in proposers.items():
        validated_preferences = _ensure_preference_sequence(proposer, preferences)
        _validate_preference_list(proposer, validated_preferences, expected_receivers)

    for receiver, preferences in receivers.items():
        validated_preferences = _ensure_preference_sequence(receiver, preferences)
        _validate_preference_list(receiver, validated_preferences, expected_proposers)


def _ensure_preference_sequence(
    participant: Person, preferences: object
) -> Sequence[Person]:
    """
    Ensure a participant's preferences are provided as an ordered sequence.

    Args:
        participant: The participant whose preferences are being validated.
        preferences: The raw preferences value supplied by the caller.

    Raises:
        ValueError: If preferences is not a sequence or is a string/bytes value.
    """

    if isinstance(preferences, (str, bytes)) or not isinstance(preferences, Sequence):
        raise ValueError(
            f"Invalid preferences for {participant!r}: expected an ordered sequence of participants."
        )

    return cast(Sequence[Person], preferences)


def _validate_preference_list(
    participant: Person,
    preferences: Sequence[Person],
    expected: Iterable[Person],
) -> None:
    """
    Verify that a single participant lists every partner exactly once.

    Args:
        participant: The participant whose list is being validated.
        preferences: Ordered sequence of preferred partners.
        expected: Iterable containing the full roster that must be ranked.

    Raises:
        ValueError: If the preference list has an incorrect length or does not
            contain precisely the expected roster members.
    """

    try:
        preference_set = set(preferences)
        expected_set = set(expected)
    except TypeError as exc:
        raise ValueError(
            f"Invalid preferences for {participant!r}: preference entries must be hashable."
        ) from exc

    if len(preferences) != len(expected_set):
        raise ValueError(
            f"{participant!r} must rank every participant exactly once; "
            f"received {len(preferences)} entries but expected {len(expected_set)}."
        )

    if preference_set != expected_set:
        missing = expected_set - preference_set
        extra = preference_set - expected_set
        messages: list[str] = []
        if missing:
            messages.append(
                f"missing preferences for: {sorted(repr(item) for item in missing)}"
            )
        if extra:
            messages.append(f"unexpected names: {sorted(repr(item) for item in extra)}")
        problem = "; ".join(messages)
        raise ValueError(f"Invalid preferences for {participant!r}: {problem}.")


__all__ = ["validate_inputs"]
