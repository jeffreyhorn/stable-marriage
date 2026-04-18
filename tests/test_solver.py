from __future__ import annotations

import random
from collections.abc import Sequence

import pytest

import stable_marriage.solver as solver_module
from stable_marriage import core, stable_marriage, types
from tests.fixtures import (
    make_invalid_preference_profiles,
    make_invalid_roster_preferences,
    make_residency_preferences,
    make_unique_matching_preferences,
    make_worst_case_preferences,
)


def assert_matching_is_stable(
    proposers: dict[str, list[str]],
    receivers: dict[str, list[str]],
    matches: dict[str, str],
) -> None:
    """Verify that no blocking pair exists for the given matching."""

    reverse_matches = {receiver: proposer for proposer, receiver in matches.items()}

    for proposer, preferences in proposers.items():
        matched_receiver = matches[proposer]
        matched_rank = preferences.index(matched_receiver)

        for preferred_receiver in preferences[:matched_rank]:
            current_partner = reverse_matches[preferred_receiver]
            challenger_rank = receivers[preferred_receiver].index(proposer)
            incumbent_rank = receivers[preferred_receiver].index(current_partner)
            assert challenger_rank >= incumbent_rank


def test_stable_marriage_produces_expected_matching():
    proposers = {
        "A": ["X", "Y", "Z"],
        "B": ["Y", "Z", "X"],
        "C": ["Y", "X", "Z"],
    }

    receivers = {
        "X": ["B", "C", "A"],
        "Y": ["C", "B", "A"],
        "Z": ["A", "B", "C"],
    }

    matches = stable_marriage(proposers, receivers)

    assert matches == {"A": "X", "B": "Z", "C": "Y"}

    assert_matching_is_stable(proposers, receivers, matches)


def test_invalid_roster_shapes_raise_value_error():
    proposers, receivers = make_invalid_roster_preferences()

    with pytest.raises(ValueError):
        stable_marriage(proposers, receivers)


def test_empty_proposer_roster_raises_value_error():
    with pytest.raises(ValueError, match="At least one proposer is required."):
        stable_marriage({}, {"X": []})


def test_empty_receiver_roster_raises_value_error():
    with pytest.raises(ValueError, match="At least one receiver is required."):
        stable_marriage({"A": []}, {})


def test_non_sequence_preferences_raise_value_error():
    proposers = {"A": {"X", "Y"}, "B": ["Y", "X"]}  # type: ignore[dict-item]
    receivers = {"X": ["A", "B"], "Y": ["B", "A"]}

    with pytest.raises(ValueError, match="expected an ordered sequence"):
        stable_marriage(proposers, receivers)


@pytest.mark.parametrize(
    ("proposers", "receivers"),
    make_invalid_preference_profiles(),
)
def test_invalid_preference_lists_raise_value_error(proposers, receivers):
    with pytest.raises(ValueError):
        stable_marriage(proposers, receivers)


def test_invalid_preference_lists_report_unexpected_names():
    proposers = {"A": ["Y", "Q"], "B": ["X", "Y"]}
    receivers = {"X": ["A", "B"], "Y": ["B", "A"]}

    with pytest.raises(ValueError, match="unexpected names"):
        stable_marriage(proposers, receivers)


def test_swapping_roles_preserves_matching_consistency():
    proposers, receivers = make_unique_matching_preferences()

    matches = stable_marriage(proposers, receivers)
    swapped_matches = stable_marriage(receivers, proposers)

    assert len(matches) == len(proposers)
    assert {
        receiver: proposer for proposer, receiver in matches.items()
    } == swapped_matches


def test_randomized_preferences_produce_stable_matchings():
    rng = random.Random(0xCAFE)
    participants = ["P0", "P1", "P2", "P3"]

    for _ in range(20):
        proposers = {
            proposer: rng.sample(participants, k=len(participants))
            for proposer in participants
        }
        receivers = {
            receiver: rng.sample(participants, k=len(participants))
            for receiver in participants
        }

        matches = stable_marriage(proposers, receivers)

        assert set(matches.keys()) == set(proposers.keys())
        assert set(matches.values()) == set(receivers.keys())
        assert_matching_is_stable(proposers, receivers, matches)


def test_residency_dataset_completes_and_is_stable():
    proposers, receivers = make_residency_preferences()

    matches = stable_marriage(proposers, receivers)

    assert set(matches.keys()) == set(proposers.keys())
    assert set(matches.values()) == set(receivers.keys())
    assert_matching_is_stable(proposers, receivers, matches)


class CountingPreferences(Sequence[str]):
    """Sequence wrapper that counts index access to track proposal attempts."""

    def __init__(self, values: list[str], counter: dict[str, int]) -> None:
        self._values = values
        self._counter = counter

    def __len__(self) -> int:
        return len(self._values)

    def __getitem__(self, index):  # type: ignore[override]
        if isinstance(index, slice):
            return self._values[index]
        self._counter["proposals"] += 1
        return self._values[index]

    def __iter__(self):
        return iter(self._values)


def test_large_residency_dataset_scales_reasonably():
    proposers, receivers = make_residency_preferences(size=200)

    counter = {"proposals": 0}
    wrapped_proposers = {
        proposer: CountingPreferences(preferences, counter)
        for proposer, preferences in proposers.items()
    }

    matches = stable_marriage(wrapped_proposers, receivers)

    size = len(proposers)
    assert counter["proposals"] <= size * size

    assert set(matches.keys()) == set(proposers.keys())
    assert set(matches.values()) == set(receivers.keys())

    reverse_matches = {receiver: proposer for proposer, receiver in matches.items()}
    proposer_ranks = {
        proposer: {receiver: rank for rank, receiver in enumerate(preferences)}
        for proposer, preferences in proposers.items()
    }
    receiver_ranks = {
        receiver: {proposer: rank for rank, proposer in enumerate(preferences)}
        for receiver, preferences in receivers.items()
    }

    for proposer, matched_receiver in matches.items():
        matched_rank = proposer_ranks[proposer][matched_receiver]
        for receiver, rank in proposer_ranks[proposer].items():
            if rank >= matched_rank:
                continue
            current_partner = reverse_matches[receiver]
            assert (
                receiver_ranks[receiver][proposer]
                >= receiver_ranks[receiver][current_partner]
            )


def test_worst_case_preferences_trigger_quadratic_proposals():
    size = 25
    proposers, receivers = make_worst_case_preferences(size=size)

    counter = {"proposals": 0}
    wrapped_proposers = {
        proposer: CountingPreferences(preferences, counter)
        for proposer, preferences in proposers.items()
    }

    matches = stable_marriage(wrapped_proposers, receivers)

    expected_lower_bound = size * (size + 1) // 2
    assert counter["proposals"] >= expected_lower_bound
    assert counter["proposals"] <= size * size

    assert set(matches.keys()) == set(proposers.keys())
    assert set(matches.values()) == set(receivers.keys())

    assert_matching_is_stable(proposers, receivers, matches)


def test_roommate_reduction_yields_consistent_pairing():
    roommate_preferences = {
        "A": ["B", "C", "D"],
        "B": ["A", "C", "D"],
        "C": ["D", "A", "B"],
        "D": ["C", "A", "B"],
    }

    proposers = {
        f"{participant}_P": [f"{pref}_R" for pref in preferences] + [f"{participant}_R"]
        for participant, preferences in roommate_preferences.items()
    }
    receivers = {
        f"{participant}_R": [f"{pref}_P" for pref in preferences] + [f"{participant}_P"]
        for participant, preferences in roommate_preferences.items()
    }

    matches = stable_marriage(proposers, receivers)

    paired = {
        frozenset({proposer[:-2], receiver[:-2]})
        for proposer, receiver in matches.items()
        if proposer[:-2] != receiver[:-2]
    }

    expected_pairs = {frozenset({"A", "B"}), frozenset({"C", "D"})}
    assert paired == expected_pairs


def test_missing_preferences_raise_value_error():
    proposers = {"A": ["X"], "B": ["X"]}
    receivers = {"X": ["A", "B"], "Y": ["A", "B"]}

    with pytest.raises(ValueError):
        stable_marriage(proposers, receivers)


def test_root_api_is_one_to_one_only():
    proposers, receivers = make_unique_matching_preferences()

    with pytest.raises(TypeError):
        stable_marriage(proposers, receivers, couples={})  # type: ignore[call-arg]


def test_solver_module_remains_compatibility_shim():
    assert solver_module.stable_marriage is core.stable_marriage
    assert solver_module.Matching is types.Matching
    assert callable(solver_module._validate_inputs)
