"""Shared public type aliases for the stable_marriage package."""

from __future__ import annotations

from collections.abc import Hashable
from typing import TypeAlias, TypeVar

Person = TypeVar("Person", bound=Hashable)
# Matchings map participants to participants of the same inferred identifier type.
Matching: TypeAlias = dict[Person, Person]

__all__ = ["Matching", "Person"]
