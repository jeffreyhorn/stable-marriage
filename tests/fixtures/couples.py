"""Preference profiles modelling couples for matching experiments."""

from __future__ import annotations

from typing import Dict, List, Tuple

CoupleProfile = Tuple[Dict[str, List[str]], Dict[str, List[str]], Dict[str, List[str]]]


def make_coupled_preferences() -> CoupleProfile:
    """
    Construct a profile where a single couple can align on the same hospital.

    Returns:
        Tuple of (proposers, receivers, couples) where `couples` maps a couple
        identifier to the list of proposer member identifiers.
    """

    proposers: Dict[str, List[str]] = {
        "C1_A": ["H1_A", "H2_A", "H1_B", "H2_B"],
        "C1_B": ["H1_B", "H2_B", "H1_A", "H2_A"],
        "S1": ["H2_A", "H1_A", "H2_B", "H1_B"],
        "S2": ["H2_B", "H1_B", "H2_A", "H1_A"],
    }

    receivers: Dict[str, List[str]] = {
        "H1_A": ["C1_A", "S1", "S2", "C1_B"],
        "H1_B": ["C1_B", "S2", "S1", "C1_A"],
        "H2_A": ["S1", "C1_A", "S2", "C1_B"],
        "H2_B": ["S2", "C1_B", "S1", "C1_A"],
    }

    couples = {"C1": ["C1_A", "C1_B"]}
    return proposers, receivers, couples


def make_conflicting_coupled_preferences() -> CoupleProfile:
    """
    Build a profile where the couple's aligned preferences cannot be satisfied.

    The construction highlights the solver's limitation: matching members
    independently can separate them across hospitals despite identical orders.
    """

    proposers: Dict[str, List[str]] = {
        "C1_A": ["H1_A", "H2_A", "H1_B", "H2_B"],
        "C1_B": ["H1_B", "H2_B", "H1_A", "H2_A"],
        "S1": ["H1_A", "H2_A", "H1_B", "H2_B"],
        "S2": ["H2_B", "H1_B", "H2_A", "H1_A"],
    }

    receivers: Dict[str, List[str]] = {
        "H1_A": ["S1", "C1_A", "C1_B", "S2"],
        "H1_B": ["S2", "C1_B", "C1_A", "S1"],
        "H2_A": ["C1_A", "S1", "S2", "C1_B"],
        "H2_B": ["S2", "S1", "C1_B", "C1_A"],
    }

    couples = {"C1": ["C1_A", "C1_B"]}
    return proposers, receivers, couples
