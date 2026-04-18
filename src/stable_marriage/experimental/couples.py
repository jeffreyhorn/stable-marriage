"""Experimental matching helpers for instances that include couples."""

from __future__ import annotations

from collections import deque
from collections.abc import Hashable, Iterable, Mapping, Sequence
from typing import Deque, Dict, List, Optional, Set, Tuple, cast

from ..types import Matching, Person
from ..validation import validate_inputs

CoupleMapping = Mapping[str, Sequence[Person]]
EntityId = Tuple[str, Hashable]


def stable_marriage_with_couples(
    proposers: Mapping[Person, Sequence[Person]],
    receivers: Mapping[Person, Sequence[Person]],
    couples: CoupleMapping,
) -> Matching:
    """
    Compute a matching with an experimental couples heuristic.

    This helper is intentionally available only under
    ``stable_marriage.experimental``. Stable matching with couples is
    substantially harder than classical one-to-one stable marriage, and this
    implementation is a heuristic layered on top of Gale-Shapley style
    proposals over receiver bases.

    Guarantees when this function returns:
        - Every proposer is assigned to exactly one receiver.
        - No receiver is assigned to more than one proposer.
        - Members of the same couple are assigned to distinct receivers that
          share the same derived base identifier.

    This function does not guarantee a stable matching for the general stable
    matching with couples problem. It also does not prove that no acceptable
    assignment exists when it raises ``ValueError``.

    Known failure modes:
        - The heuristic can reject an instance even when a valid assignment may
          exist.
        - Couple members must induce the same ordered base sequence after
          receiver labels are collapsed into bases.
        - Receiver bases are derived from string suffixes such as ``_SlotA`` or
          ``-SlotA`` rather than explicit structured slot metadata.

    Args:
        proposers: Mapping of proposer identifiers to their ordered preference
            lists.
        receivers: Mapping of receiver identifiers to their ordered preference
            lists.
        couples: Mapping describing coupled proposers whose assignments must
            satisfy the heuristic's joint-placement constraints.

    Returns:
        Dict mapping each proposer to the receiver they are matched with.

    Raises:
        ValueError: If preference lists are inconsistent or omit required
            participants, or if the heuristic could not find an acceptable
            assignment for the supplied data. In the latter case, the error
            does not prove that no stable assignment exists.
    """

    validate_inputs(proposers, receivers)
    return _stable_marriage_with_couples(proposers, receivers, couples)


def _stable_marriage_with_couples(
    proposers: Mapping[Person, Sequence[Person]],
    receivers: Mapping[Person, Sequence[Person]],
    couples: CoupleMapping,
) -> Matching:
    """
    Run the experimental couples heuristic over receiver-base preferences.

    Couples must have members whose preference lists collapse to an identical
    ordering of receiver base identifiers. Each couple proposal reserves one
    distinct receiver per member at the targeted base.
    """

    (
        couple_preferences,
        member_base_options,
        _receivers_by_base,
    ) = _validate_couples(proposers, receivers, couples)

    receiver_rankings: Dict[Person, Dict[Person, int]] = {
        receiver: {proposer: rank for rank, proposer in enumerate(preferences)}
        for receiver, preferences in receivers.items()
    }

    engagements: Dict[Person, Person] = {}
    member_assignment: Dict[Person, Optional[Person]] = {
        proposer: None for proposer in proposers.keys()
    }

    entity_members: Dict[EntityId, List[Person]] = {}
    entity_preferences: Dict[EntityId, Sequence[Person] | Sequence[str]] = {}
    next_choice_index: Dict[EntityId, int] = {}
    member_to_entity: Dict[Person, EntityId] = {}

    queue: Deque[EntityId] = deque()
    in_queue: Set[EntityId] = set()

    couple_member_ids: Set[Person] = set()
    for couple_id, members in couples.items():
        name: EntityId = ("couple", couple_id)
        entity_members[name] = list(members)
        entity_preferences[name] = couple_preferences[couple_id]
        next_choice_index[name] = 0
        queue.append(name)
        in_queue.add(name)
        for member in members:
            member_to_entity[member] = name
            couple_member_ids.add(member)

    for proposer in proposers.keys():
        if proposer in couple_member_ids:
            continue
        name = ("single", proposer)
        entity_members[name] = [proposer]
        entity_preferences[name] = proposers[proposer]
        next_choice_index[name] = 0
        queue.append(name)
        in_queue.add(name)
        member_to_entity[proposer] = name

    def entity_label(entity: EntityId) -> str:
        kind, identifier = entity
        return f"{kind}:{identifier!r}"

    def enqueue(entity: EntityId) -> None:
        if entity not in in_queue:
            queue.append(entity)
            in_queue.add(entity)

    def release_entity(entity: EntityId, requeue: bool = True) -> None:
        members = entity_members[entity]
        for member in members:
            current_receiver = member_assignment.get(member)
            if current_receiver is None:
                continue
            if engagements.get(current_receiver) == member:
                del engagements[current_receiver]
            member_assignment[member] = None
        if requeue:
            enqueue(entity)

    while queue:
        entity = queue.popleft()
        in_queue.discard(entity)

        preferences = entity_preferences[entity]
        index = next_choice_index[entity]

        if index >= len(preferences):
            raise ValueError(
                f"{entity_label(entity)} exhausted all preference options without an acceptable heuristic assignment."
            )

        choice = preferences[index]
        next_choice_index[entity] += 1

        if entity[0] == "single":
            member = entity_members[entity][0]
            receiver = cast(Person, choice)

            current_partner = engagements.get(receiver)
            if current_partner is None:
                release_entity(entity, requeue=False)
                engagements[receiver] = member
                member_assignment[member] = receiver
                continue

            if current_partner == member:
                continue

            current_rank = receiver_rankings[receiver][current_partner]
            challenger_rank = receiver_rankings[receiver][member]

            if challenger_rank < current_rank:
                release_entity(member_to_entity[current_partner])
                release_entity(entity, requeue=False)
                engagements[receiver] = member
                member_assignment[member] = receiver
            else:
                enqueue(entity)
            continue

        members = entity_members[entity]
        base = cast(str, choice)
        targeted = _select_couple_targets(members, base, member_base_options)

        rejecting = False
        displaced_entities: Set[EntityId] = set()
        for member, receiver in targeted:
            current_partner = engagements.get(receiver)
            if current_partner is None:
                continue

            if current_partner == member:
                continue

            current_rank = receiver_rankings[receiver][current_partner]
            challenger_rank = receiver_rankings[receiver][member]

            if challenger_rank < current_rank:
                displaced_entities.add(member_to_entity[current_partner])
            else:
                rejecting = True
                break

        if rejecting:
            enqueue(entity)
            continue

        for displaced in displaced_entities:
            release_entity(displaced)

        release_entity(entity, requeue=False)

        for member, receiver in targeted:
            engagements[receiver] = member
            member_assignment[member] = receiver

    unmatched = [
        member for member, receiver in member_assignment.items() if receiver is None
    ]
    if unmatched:
        raise ValueError(
            "The experimental couples heuristic failed to assign every proposer."
        )

    return {
        member: receiver
        for member, receiver in member_assignment.items()
        if receiver is not None
    }


def _validate_couples(
    proposers: Mapping[Person, Sequence[Person]],
    receivers: Mapping[Person, Sequence[Person]],
    couples: CoupleMapping,
) -> Tuple[
    Dict[str, Sequence[str]],
    Dict[Person, Dict[str, List[Person]]],
    Dict[str, List[Person]],
]:
    """
    Validate couple metadata and prepare heuristic preference structures.

    Returns:
        - Mapping of couple identifier to ordered base preferences.
        - Mapping of proposer member to their available receivers per base.
        - Mapping of base identifiers to receivers belonging to that base.
    """

    receivers_by_base = _group_receivers_by_base(receivers.keys())

    seen_members: Set[Person] = set()
    couple_preferences: Dict[str, Sequence[str]] = {}
    member_base_options: Dict[Person, Dict[str, List[Person]]] = {}

    for couple_id, members in couples.items():
        if not members:
            raise ValueError(f"Couple {couple_id!r} must list at least one member.")

        base_sequence: Optional[List[str]] = None
        members_in_couple: Set[Person] = set()

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
            base_order: List[str] = []
            base_receivers: Dict[str, List[Person]] = {}

            for receiver in preferences:
                base = _receiver_base(receiver)
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


def _group_receivers_by_base(receivers: Iterable[Person]) -> Dict[str, List[Person]]:
    grouped: Dict[str, List[Person]] = {}

    for receiver in receivers:
        base = _receiver_base(receiver)
        grouped.setdefault(base, []).append(receiver)

    return grouped


def _select_couple_targets(
    members: Sequence[Person],
    base: str,
    member_base_options: Mapping[Person, Mapping[str, List[Person]]],
) -> List[Tuple[Person, Person]]:
    """Choose distinct receivers for each member of a couple at one base."""

    selected: List[Tuple[Person, Person]] = []
    used_receivers: Set[Person] = set()

    for member in members:
        options = member_base_options[member].get(base)
        if not options:
            raise ValueError(
                f"Member {member!r} lacks receivers for preferred base {base!r}."
            )

        chosen: Optional[Person] = None
        for receiver in options:
            if receiver not in used_receivers:
                chosen = receiver
                break

        if chosen is None:
            raise ValueError(
                f"Base {base!r} lacks enough distinct receivers for the couple members."
            )

        used_receivers.add(chosen)
        selected.append((member, chosen))

    return selected


def _receiver_base(receiver: Hashable) -> str:
    """
    Derive a base identifier from a receiver label.

    Examples:
        H1_A -> H1
        Hospital-1-SlotA -> Hospital-1
    """

    receiver_text = receiver if isinstance(receiver, str) else str(receiver)

    split_at = -1
    for delimiter in ("_", "-"):
        split_at = max(split_at, receiver_text.rfind(delimiter))
    if split_at == -1:
        return receiver_text

    suffix = receiver_text[split_at + 1 :]
    if (len(suffix) == 1 and suffix.isalpha()) or (
        suffix.startswith("Slot") and len(suffix) > 4 and suffix[4:].isalpha()
    ):
        return receiver_text[:split_at]

    return receiver_text


__all__ = ["stable_marriage_with_couples"]
