"""Internal validation and preprocessing helpers for the couples heuristic."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from ..types import Person
from ._bases import _group_receivers_by_base, _receiver_base
from ._types import CoupleId, CoupleMapping, ReceiverBaseFn


def _validate_couples(
    proposers: Mapping[Person, Sequence[Person]],
    receivers: Mapping[Person, Sequence[Person]],
    couples: CoupleMapping,
    base_fn: ReceiverBaseFn | None = None,
) -> tuple[
    dict[CoupleId, Sequence[str]],
    dict[Person, dict[str, list[Person]]],
    dict[str, list[Person]],
]:
    """
    Validate couple metadata and prepare heuristic preference structures.

    Returns:
        - Mapping of couple identifier to ordered base preferences.
        - Mapping of proposer member to their available receivers per base.
        - Mapping of base identifiers to receivers belonging to that base.
    """

    receiver_base = _receiver_base if base_fn is None else base_fn
    receivers_by_base = _group_receivers_by_base(receivers.keys(), receiver_base)

    seen_members: set[Person] = set()
    couple_preferences: dict[CoupleId, Sequence[str]] = {}
    member_base_options: dict[Person, dict[str, list[Person]]] = {}

    for couple_id, members in couples.items():
        if len(members) < 2:
            raise ValueError(f"Couple {couple_id!r} must have at least two members.")

        base_sequence: list[str] | None = None
        members_in_couple: set[Person] = set()

        for member in members:
            if member in members_in_couple:
                raise ValueError(
                    f"Participant {member!r} appears more than once in couple {couple_id!r}."
                )
            if member in seen_members:
                raise ValueError(f"Participant {member!r} appears in multiple couples.")
            if member not in proposers:
                raise ValueError(
                    f"Couple member {member!r} is not present in proposer preferences."
                )

            preferences = proposers[member]
            base_order: list[str] = []
            base_receivers: dict[str, list[Person]] = {}

            for receiver in preferences:
                base = receiver_base(receiver)
                if base not in base_receivers:
                    base_receivers[base] = []
                    base_order.append(base)
                base_receivers[base].append(receiver)

            if base_sequence is None:
                base_sequence = base_order
            elif base_order != base_sequence:
                raise ValueError(
                    f"Couple {couple_id!r} members must share identical base preferences."
                )

            member_base_options[member] = base_receivers
            seen_members.add(member)
            members_in_couple.add(member)

        if base_sequence is None:
            raise ValueError(f"Couple {couple_id!r} has empty preference lists.")

        for base in base_sequence:
            if base not in receivers_by_base:
                raise ValueError(
                    f"Couple {couple_id!r} prefers base {base!r} "
                    "which has no corresponding receivers."
                )
            if len(receivers_by_base[base]) < len(members):
                raise ValueError(
                    f"Base {base!r} does not provide enough positions "
                    f"for couple {couple_id!r}."
                )

        couple_preferences[couple_id] = tuple(base_sequence)

    return couple_preferences, member_base_options, receivers_by_base


__all__ = ["_validate_couples"]
