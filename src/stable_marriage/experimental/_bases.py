"""Internal receiver-base parsing helpers for the experimental couples heuristic."""

from __future__ import annotations

from collections.abc import Hashable, Iterable

from ..types import Person
from ._types import ReceiverBaseFn


def _group_receivers_by_base(
    receivers: Iterable[Person],
    base_fn: ReceiverBaseFn | None = None,
) -> dict[str, list[Person]]:
    receiver_base = _receiver_base if base_fn is None else base_fn
    grouped: dict[str, list[Person]] = {}

    for receiver in receivers:
        base = receiver_base(receiver)
        grouped.setdefault(base, []).append(receiver)

    return grouped


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


__all__ = ["_group_receivers_by_base", "_receiver_base"]
