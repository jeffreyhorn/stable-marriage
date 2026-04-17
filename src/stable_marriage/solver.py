"""Pure-Python implementation of stable matching helpers."""

from __future__ import annotations

from collections import deque
from typing import (
    Deque,
    Dict,
    Hashable,
    Iterable,
    List,
    Mapping,
    Optional,
    Sequence,
    Set,
    Tuple,
    TypeVar,
)

Person = TypeVar("Person", bound=Hashable)
Matching = Dict[Person, Person]
CoupleMapping = Mapping[str, Sequence[Person]]


def stable_marriage(
    proposers: Mapping[Person, Sequence[Person]],
    receivers: Mapping[Person, Sequence[Person]],
) -> Matching:
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

    _validate_inputs(proposers, receivers)
    return _stable_marriage_one_to_one(proposers, receivers)


def stable_marriage_with_couples(
    proposers: Mapping[Person, Sequence[Person]],
    receivers: Mapping[Person, Sequence[Person]],
    couples: CoupleMapping,
) -> Matching:
    """
    Compute a matching with an experimental couples heuristic.

    This function is intentionally separate from the supported public
    :func:`stable_marriage` API. Stable matching with couples is substantially
    harder than classical one-to-one stable marriage, and this implementation
    is a heuristic layered on top of Gale-Shapley style proposals.

    A returned matching satisfies the heuristic's constraints for the supplied
    data. A ``ValueError`` indicates that the heuristic could not find an
    acceptable assignment; it does not prove that no stable assignment exists.
    """

    _validate_inputs(proposers, receivers)
    return _stable_marriage_with_couples(proposers, receivers, couples)


def _stable_marriage_one_to_one(
    proposers: Mapping[Person, Sequence[Person]],
    receivers: Mapping[Person, Sequence[Person]],
) -> Matching:
    """Classical Gale–Shapley solver without couple constraints."""

    free_proposers: Deque[Person] = deque(proposers.keys())
    next_choice_index: Dict[Person, int] = {proposer: 0 for proposer in proposers}

    receiver_rankings: Dict[Person, Dict[Person, int]] = {
        receiver: {proposer: rank for rank, proposer in enumerate(preferences)}
        for receiver, preferences in receivers.items()
    }

    engagements: Dict[Person, Person] = {}

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


def _stable_marriage_with_couples(
    proposers: Mapping[Person, Sequence[Person]],
    receivers: Mapping[Person, Sequence[Person]],
    couples: CoupleMapping,
) -> Matching:
    """
    Solve the stable marriage problem while ensuring couples share placements.

    Couples must have members whose preference lists collapse to an identical
    ordering of receiver base identifiers (e.g., hospitals). Each proposal made
    by a couple reserves one receiver per member at the targeted base.
    """

    (
        couple_preferences,
        member_base_options,
        receivers_by_base,
    ) = _validate_couples(proposers, receivers, couples)

    receiver_rankings: Dict[Person, Dict[Person, int]] = {
        receiver: {proposer: rank for rank, proposer in enumerate(preferences)}
        for receiver, preferences in receivers.items()
    }

    engagements: Dict[Person, Person] = {}
    member_assignment: Dict[Person, Optional[Person]] = {
        proposer: None for proposer in proposers.keys()
    }

    entity_members: Dict[str, List[Person]] = {}
    entity_preferences: Dict[str, Sequence[str]] = {}
    entity_kind: Dict[str, str] = {}
    next_choice_index: Dict[str, int] = {}
    member_to_entity: Dict[Person, str] = {}

    queue: Deque[str] = deque()
    in_queue: Set[str] = set()

    couple_member_ids: Set[Person] = set()
    for couple_id, members in couples.items():
        name = f"couple:{couple_id}"
        entity_members[name] = list(members)
        entity_preferences[name] = couple_preferences[couple_id]
        entity_kind[name] = "couple"
        next_choice_index[name] = 0
        queue.append(name)
        in_queue.add(name)
        for member in members:
            member_to_entity[member] = name
            couple_member_ids.add(member)

    for proposer in proposers.keys():
        if proposer in couple_member_ids:
            continue
        name = str(proposer)
        entity_members[name] = [proposer]
        entity_preferences[name] = list(proposers[proposer])
        entity_kind[name] = "single"
        next_choice_index[name] = 0
        queue.append(name)
        in_queue.add(name)
        member_to_entity[proposer] = name

    def enqueue(entity: str) -> None:
        if entity not in in_queue:
            queue.append(entity)
            in_queue.add(entity)

    def release_entity(entity: str, requeue: bool = True) -> None:
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
                f"{entity!r} exhausted all preference options without a stable match."
            )

        choice = preferences[index]
        next_choice_index[entity] += 1

        if entity_kind[entity] == "single":
            member = entity_members[entity][0]
            receiver = choice  # type: ignore[assignment]

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

        # Couple proposal.
        members = entity_members[entity]
        base = choice

        targeted = _select_couple_targets(members, base, member_base_options)

        rejecting = False
        displaced_entities: Set[str] = set()
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

    unmatched = [member for member, receiver in member_assignment.items() if receiver is None]
    if unmatched:
        raise ValueError(
            "Failed to compute a stable matching that satisfies the couple constraints."
        )

    return {member: receiver for member, receiver in member_assignment.items() if receiver}


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
    Validate couple metadata and prepare preference structures.

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

        for member in members:
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
    """
    Choose distinct receivers for each member of a couple at the specified base.
    """

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


def _receiver_base(receiver: Person) -> str:
    """
    Derive a base identifier from a receiver label.

    Examples:
        H1_A -> H1
        Hospital-1-SlotA -> Hospital-1
    """

    if isinstance(receiver, str):
        for delimiter in ("_", "-"):
            if delimiter in receiver:
                return receiver.split(delimiter, 1)[0]
        return receiver
    return str(receiver)


def _validate_inputs(
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

    proposer_ids = set(proposers.keys())
    receiver_ids = set(receivers.keys())

    if not proposer_ids:
        raise ValueError("At least one proposer is required.")

    if not receiver_ids:
        raise ValueError("At least one receiver is required.")

    if len(proposer_ids) != len(receiver_ids):
        raise ValueError(
            "The number of proposers must equal the number of receivers."
        )

    # Capture the required identities for each side so every participant ranks
    # all possible partners exactly once.
    expected_receivers = receiver_ids
    expected_proposers = proposer_ids

    for proposer, preferences in proposers.items():
        _validate_preference_list(proposer, preferences, expected_receivers)

    for receiver, preferences in receivers.items():
        _validate_preference_list(receiver, preferences, expected_proposers)


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

    preference_set = set(preferences)
    expected_set = set(expected)

    if len(preferences) != len(expected_set):
        raise ValueError(
            f"{participant!r} must rank every participant exactly once; "
            f"received {len(preferences)} entries but expected {len(expected_set)}."
        )

    if preference_set != expected_set:
        missing = expected_set - preference_set
        extra = preference_set - expected_set
        messages: List[str] = []
        if missing:
            messages.append(f"missing preferences for: {sorted(missing)}")
        if extra:
            messages.append(f"unexpected names: {sorted(extra)}")
        problem = "; ".join(messages)
        raise ValueError(f"Invalid preferences for {participant!r}: {problem}.")
