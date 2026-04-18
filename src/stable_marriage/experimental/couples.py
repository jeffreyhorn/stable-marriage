"""Experimental matching helpers for instances that include couples."""

from __future__ import annotations

import logging
from collections import deque
from collections.abc import Mapping, Sequence
from typing import cast

from ..types import Person
from ..validation import validate_inputs
from ._bases import _receiver_base
from ._types import CoupleMapping, EntityId, ReceiverBaseFn
from ._validation import _validate_couples

logger = logging.getLogger(__name__)


def stable_marriage_with_couples(
    proposers: Mapping[Person, Sequence[Person]],
    receivers: Mapping[Person, Sequence[Person]],
    couples: CoupleMapping,
    base_fn: ReceiverBaseFn | None = None,
) -> dict[Person, Person]:
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
        - By default, receiver bases are derived from string suffixes such as
          ``_A``, ``_SlotA``, or ``-SlotA`` rather than explicit structured
          slot metadata. Callers with different naming schemes must pass a
          custom ``base_fn``.

    Args:
        proposers: Mapping of proposer identifiers to their ordered preference
            lists.
        receivers: Mapping of receiver identifiers to their ordered preference
            lists.
        couples: Mapping describing coupled proposers whose assignments must
            satisfy the heuristic's joint-placement constraints.
        base_fn: Optional function used to collapse a receiver identifier into
            a base string for couple alignment. When omitted, the heuristic
            uses ``_receiver_base()``, which strips trailing slot suffixes such
            as ``_A``, ``_SlotA``, and ``-SlotA``.

    Returns:
        Dict mapping each proposer to the receiver they are matched with.

    Raises:
        ValueError: If preference lists are inconsistent or omit required
            participants, or if the heuristic could not find an acceptable
            assignment for the supplied data. In the latter case, the error
            does not prove that no stable assignment exists.
    """

    validate_inputs(proposers, receivers)
    return _stable_marriage_with_couples(proposers, receivers, couples, base_fn)


def _stable_marriage_with_couples(
    proposers: Mapping[Person, Sequence[Person]],
    receivers: Mapping[Person, Sequence[Person]],
    couples: CoupleMapping,
    base_fn: ReceiverBaseFn | None = None,
) -> dict[Person, Person]:
    """
    Run the experimental couples heuristic over receiver-base preferences.

    Couples must have members whose preference lists collapse to an identical
    ordering of receiver base identifiers. Each couple proposal reserves one
    distinct receiver per member at the targeted base. The implementation
    enforces a conservative upper bound of ``n^2 * max(len(couples), 1)``
    queue iterations, where ``n`` is the number of proposers, and raises
    ``ValueError`` if that bound is exceeded.
    """

    receiver_base = _receiver_base if base_fn is None else base_fn

    (
        couple_preferences,
        member_base_options,
        _receivers_by_base,
    ) = _validate_couples(proposers, receivers, couples, receiver_base)

    receiver_rankings: dict[Person, dict[Person, int]] = {
        receiver: {proposer: rank for rank, proposer in enumerate(preferences)}
        for receiver, preferences in receivers.items()
    }

    engagements: dict[Person, Person] = {}
    member_assignment: dict[Person, Person | None] = {
        proposer: None for proposer in proposers.keys()
    }

    entity_members: dict[EntityId, list[Person]] = {}
    entity_preferences: dict[EntityId, Sequence[Person] | Sequence[str]] = {}
    next_choice_index: dict[EntityId, int] = {}
    member_to_entity: dict[Person, EntityId] = {}

    queue: deque[EntityId] = deque()
    in_queue: set[EntityId] = set()

    def entity_label(entity: EntityId) -> str:
        kind, identifier = entity
        return f"{kind}:{identifier!r}"

    couple_member_ids: set[Person] = set()
    for couple_id, members in couples.items():
        name: EntityId = ("couple", couple_id)
        entity_members[name] = list(members)
        entity_preferences[name] = couple_preferences[couple_id]
        next_choice_index[name] = 0
        queue.append(name)
        in_queue.add(name)
        logger.debug("Created %s with members %s", entity_label(name), list(members))
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
        logger.debug("Created %s with member %r", entity_label(name), proposer)

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

    max_iterations = _max_heuristic_iterations(proposers, couples)
    iteration_count = 0
    while queue:
        iteration_count += 1
        if iteration_count > max_iterations:
            raise ValueError(
                "The experimental couples heuristic exceeded its iteration bound "
                f"({max_iterations}) without converging."
            )

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
        logger.debug("%s proposes to %r", entity_label(entity), choice)

        if entity[0] == "single":
            member = entity_members[entity][0]
            receiver = cast(Person, choice)

            current_partner = engagements.get(receiver)
            if current_partner is None:
                release_entity(entity, requeue=False)
                engagements[receiver] = member
                member_assignment[member] = receiver
                logger.debug(
                    "%s accepted by %r; %r is now matched",
                    entity_label(entity),
                    receiver,
                    member,
                )
                continue

            if current_partner == member:
                continue

            current_rank = receiver_rankings[receiver][current_partner]
            challenger_rank = receiver_rankings[receiver][member]

            if challenger_rank < current_rank:
                logger.debug(
                    "%s displaces %r at %r",
                    entity_label(entity),
                    current_partner,
                    receiver,
                )
                release_entity(member_to_entity[current_partner])
                release_entity(entity, requeue=False)
                engagements[receiver] = member
                member_assignment[member] = receiver
                logger.debug(
                    "%s accepted by %r after displacement",
                    entity_label(entity),
                    receiver,
                )
            else:
                logger.debug(
                    "%s rejected by %r in favor of %r",
                    entity_label(entity),
                    receiver,
                    current_partner,
                )
                enqueue(entity)
            continue

        members = entity_members[entity]
        base = cast(str, choice)
        targeted = _select_couple_targets(members, base, member_base_options)
        logger.debug(
            "%s targets base %r with receivers %s", entity_label(entity), base, targeted
        )

        rejecting = False
        displaced_entities: set[EntityId] = set()
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
                logger.debug(
                    "%s rejected at %r because %r outranks %r",
                    entity_label(entity),
                    receiver,
                    current_partner,
                    member,
                )
                rejecting = True
                break

        if rejecting:
            enqueue(entity)
            continue

        for displaced in displaced_entities:
            logger.debug(
                "%s displaced by %s", entity_label(displaced), entity_label(entity)
            )
            release_entity(displaced)

        release_entity(entity, requeue=False)

        for member, receiver in targeted:
            engagements[receiver] = member
            member_assignment[member] = receiver
        logger.debug(
            "%s accepted at base %r with assignments %s",
            entity_label(entity),
            base,
            targeted,
        )

    unmatched = [
        member for member, receiver in member_assignment.items() if receiver is None
    ]
    if unmatched:
        raise ValueError(
            "The experimental couples heuristic failed to assign every proposer."
        )

    result: dict[Person, Person] = {
        member: receiver
        for member, receiver in member_assignment.items()
        if receiver is not None
    }
    logger.debug("Completed couples heuristic with matching %s", result)
    return result


def _max_heuristic_iterations(
    proposers: Mapping[Person, Sequence[Person]],
    couples: CoupleMapping,
) -> int:
    """Return a conservative queue-iteration bound for the couples heuristic."""

    size = len(proposers)
    return size * size * max(len(couples), 1)


def _select_couple_targets(
    members: Sequence[Person],
    base: str,
    member_base_options: Mapping[Person, Mapping[str, list[Person]]],
) -> list[tuple[Person, Person]]:
    """
    Choose distinct receivers for each member of a couple at one base.

    Member iteration order affects which receiver each member gets when
    multiple distinct receivers are available at the same base.
    """

    selected: list[tuple[Person, Person]] = []
    used_receivers: set[Person] = set()

    for member in members:
        options = member_base_options[member].get(base)
        if not options:
            raise ValueError(
                f"Member {member!r} lacks receivers for preferred base {base!r}."
            )

        chosen: Person | None = None
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


__all__ = ["stable_marriage_with_couples"]
