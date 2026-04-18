"""Compatibility layer for the classical stable marriage solver."""

from __future__ import annotations

from .core import stable_marriage
from .types import Matching
from .validation import validate_inputs as _validate_inputs

__all__ = ["Matching", "stable_marriage", "_validate_inputs"]
