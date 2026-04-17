"""Fixtures package exposing reusable preference profiles for tests."""

from .couples import make_conflicting_coupled_preferences, make_coupled_preferences
from .preferences import (
    PreferenceProfile,
    make_invalid_preference_profiles,
    make_invalid_roster_preferences,
    make_unique_matching_preferences,
)
from .residency import make_residency_preferences
from .worst_case import make_worst_case_preferences

__all__ = [
    "PreferenceProfile",
    "make_invalid_preference_profiles",
    "make_invalid_roster_preferences",
    "make_unique_matching_preferences",
    "make_conflicting_coupled_preferences",
    "make_coupled_preferences",
    "make_residency_preferences",
    "make_worst_case_preferences",
]
