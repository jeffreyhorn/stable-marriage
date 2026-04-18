"""Shared public type aliases for the stable_marriage package."""

from __future__ import annotations

from collections.abc import Hashable
from typing import TypeAlias, TypeVar

Person = TypeVar("Person", bound=Hashable)
# Function signatures using ``Person`` carry the stronger same-side typing;
# this alias documents the concrete runtime shape of returned matchings.
Matching: TypeAlias = dict[Hashable, Hashable]

__all__ = ["Matching", "Person"]
