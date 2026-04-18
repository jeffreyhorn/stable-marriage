"""Shared internal types for the experimental couples heuristic."""

from __future__ import annotations

from collections.abc import Callable, Hashable, Mapping, Sequence

from ..types import Person

CoupleId = Hashable
CoupleMapping = Mapping[CoupleId, Sequence[Person]]
EntityId = tuple[str, Hashable]
ReceiverBaseFn = Callable[[Hashable], str]

__all__ = ["CoupleId", "CoupleMapping", "EntityId", "ReceiverBaseFn"]
