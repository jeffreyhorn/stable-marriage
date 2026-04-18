"""Shared public type aliases for the stable_marriage package."""

from __future__ import annotations

from collections.abc import Hashable
from typing import TypeVar

Person = TypeVar("Person", bound=Hashable)
Matching = dict[Person, Person]

__all__ = ["Matching", "Person"]
