from __future__ import annotations

import pytest

import stable_marriage
from stable_marriage.experimental import stable_marriage_with_couples
from stable_marriage.experimental.couples import (
    _receiver_base,
    _select_couple_targets,
    _validate_couples,
)
from tests.fixtures import (
    make_conflicting_coupled_preferences,
    make_coupled_preferences,
)


def test_coupled_members_align_in_cooperative_preferences():
    proposers, receivers, couples = make_coupled_preferences()

    matches = stable_marriage_with_couples(proposers, receivers, couples)

    def hospital_base(receiver: str) -> str:
        return receiver.split("_")[0]

    for members in couples.values():
        placements = {hospital_base(matches[member]) for member in members}
        assert len(placements) == 1


def test_conflicting_coupled_preferences_expose_limitation():
    proposers, receivers, couples = make_conflicting_coupled_preferences()

    with pytest.raises(ValueError):
        stable_marriage_with_couples(proposers, receivers, couples)


def test_receiver_base_keeps_hyphenated_hospital_name():
    assert _receiver_base("Hospital-1-SlotA") == "Hospital-1"
    assert _receiver_base("Hospital-1-SlotB") == "Hospital-1"
    assert _receiver_base("H1_A") == "H1"
    assert _receiver_base("Hospital-1") == "Hospital-1"
    assert _receiver_base("Hospital_1") == "Hospital_1"


def test_couples_mode_accepts_hyphenated_receiver_bases():
    proposers = {
        "C1_A": [
            "Hospital-1-SlotA",
            "Hospital-1-SlotB",
            "Clinic-2-SlotA",
            "Clinic-2-SlotB",
        ],
        "C1_B": [
            "Hospital-1-SlotB",
            "Hospital-1-SlotA",
            "Clinic-2-SlotB",
            "Clinic-2-SlotA",
        ],
        "Single_A": [
            "Clinic-2-SlotA",
            "Clinic-2-SlotB",
            "Hospital-1-SlotA",
            "Hospital-1-SlotB",
        ],
        "Single_B": [
            "Clinic-2-SlotB",
            "Clinic-2-SlotA",
            "Hospital-1-SlotB",
            "Hospital-1-SlotA",
        ],
    }
    receivers = {
        "Hospital-1-SlotA": ["C1_A", "Single_A", "Single_B", "C1_B"],
        "Hospital-1-SlotB": ["C1_B", "Single_B", "Single_A", "C1_A"],
        "Clinic-2-SlotA": ["Single_A", "Single_B", "C1_A", "C1_B"],
        "Clinic-2-SlotB": ["Single_B", "Single_A", "C1_B", "C1_A"],
    }
    couples = {"C1": ["C1_A", "C1_B"]}

    matches = stable_marriage_with_couples(proposers, receivers, couples)

    assert {
        matches["Single_A"],
        matches["Single_B"],
    } == {"Clinic-2-SlotA", "Clinic-2-SlotB"}
    assert {
        _receiver_base(matches["C1_A"]),
        _receiver_base(matches["C1_B"]),
    } == {"Hospital-1"}


def test_single_entities_do_not_collide_on_stringified_ids():
    proposers = {
        1: ["X", "Y"],
        "1": ["Y", "X"],
    }
    receivers = {
        "X": [1, "1"],
        "Y": ["1", 1],
    }

    matches = stable_marriage_with_couples(proposers, receivers, couples={})

    assert matches == {1: "X", "1": "Y"}


def test_couples_mode_uses_opaque_internal_ids():
    proposers = {
        "member_a": ["Hospital-1-SlotA", "Hospital-1-SlotB", "Solo-A", "Solo-B"],
        "member_b": ["Hospital-1-SlotB", "Hospital-1-SlotA", "Solo-B", "Solo-A"],
        "couple:C1": ["Solo-A", "Solo-B", "Hospital-1-SlotA", "Hospital-1-SlotB"],
        "single": ["Solo-B", "Solo-A", "Hospital-1-SlotB", "Hospital-1-SlotA"],
    }
    receivers = {
        "Hospital-1-SlotA": ["member_a", "couple:C1", "single", "member_b"],
        "Hospital-1-SlotB": ["member_b", "single", "couple:C1", "member_a"],
        "Solo-A": ["couple:C1", "single", "member_a", "member_b"],
        "Solo-B": ["single", "couple:C1", "member_b", "member_a"],
    }
    couples = {"C1": ["member_a", "member_b"]}

    matches = stable_marriage_with_couples(proposers, receivers, couples)

    assert matches == {
        "member_a": "Hospital-1-SlotA",
        "member_b": "Hospital-1-SlotB",
        "couple:C1": "Solo-A",
        "single": "Solo-B",
    }


def test_root_package_does_not_export_experimental_couples_api():
    assert not hasattr(stable_marriage, "stable_marriage_with_couples")


def test_couples_validation_rejects_empty_couple():
    proposers = {"A": ["X"], "B": ["Y"]}
    receivers = {"X": ["A", "B"], "Y": ["B", "A"]}

    with pytest.raises(ValueError, match="must list at least one member"):
        _validate_couples(proposers, receivers, {"C1": []})


def test_couples_validation_rejects_duplicate_member_across_couples():
    proposers = {
        "A": ["H1_A", "H1_B", "H2_A", "H2_B"],
        "B": ["H1_B", "H1_A", "H2_B", "H2_A"],
        "C": ["H1_A", "H1_B", "H2_A", "H2_B"],
        "D": ["H1_B", "H1_A", "H2_B", "H2_A"],
    }
    receivers = {
        "H1_A": ["A", "B", "C", "D"],
        "H1_B": ["B", "A", "D", "C"],
        "H2_A": ["C", "D", "A", "B"],
        "H2_B": ["D", "C", "B", "A"],
    }

    with pytest.raises(ValueError, match="appears in multiple couples"):
        _validate_couples(proposers, receivers, {"C1": ["A", "B"], "C2": ["A", "C"]})


def test_couples_validation_rejects_duplicate_member_within_same_couple():
    proposers = {
        "A": ["H1_A", "H1_B", "H2_A", "H2_B"],
        "B": ["H1_B", "H1_A", "H2_B", "H2_A"],
        "C": ["H1_A", "H1_B", "H2_A", "H2_B"],
        "D": ["H1_B", "H1_A", "H2_B", "H2_A"],
    }
    receivers = {
        "H1_A": ["A", "B", "C", "D"],
        "H1_B": ["B", "A", "D", "C"],
        "H2_A": ["C", "D", "A", "B"],
        "H2_B": ["D", "C", "B", "A"],
    }

    with pytest.raises(ValueError, match="appears more than once in couple 'C1'"):
        _validate_couples(proposers, receivers, {"C1": ["A", "A"]})


def test_couples_validation_rejects_missing_member():
    proposers = {"A": ["X", "Y"], "B": ["Y", "X"]}
    receivers = {"X": ["A", "B"], "Y": ["B", "A"]}

    with pytest.raises(ValueError, match="is not present in proposer preferences"):
        _validate_couples(proposers, receivers, {"C1": ["A", "missing"]})


def test_couples_validation_rejects_mismatched_base_order():
    proposers = {
        "A": ["H1_A", "H2_A", "H2_B", "H1_B"],
        "B": ["H2_A", "H1_A", "H1_B", "H2_B"],
        "C": ["H1_B", "H2_B", "H1_A", "H2_A"],
        "D": ["H2_B", "H1_B", "H2_A", "H1_A"],
    }
    receivers = {
        "H1_A": ["A", "B", "C", "D"],
        "H1_B": ["C", "D", "A", "B"],
        "H2_A": ["B", "A", "D", "C"],
        "H2_B": ["D", "C", "B", "A"],
    }

    with pytest.raises(ValueError, match="must share identical base preferences"):
        _validate_couples(proposers, receivers, {"C1": ["A", "B"]})


def test_couples_validation_rejects_unknown_base():
    proposers = {
        "A": ["H1_A", "H1_B", "Missing_A", "Missing_B"],
        "B": ["H1_B", "H1_A", "Missing_B", "Missing_A"],
        "C": ["H1_A", "H1_B", "Missing_A", "Missing_B"],
        "D": ["H1_B", "H1_A", "Missing_B", "Missing_A"],
    }
    receivers = {
        "H1_A": ["A", "B", "C", "D"],
        "H1_B": ["B", "A", "D", "C"],
        "H2_A": ["C", "D", "A", "B"],
        "H2_B": ["D", "C", "B", "A"],
    }

    with pytest.raises(ValueError, match="has no corresponding receivers"):
        _validate_couples(proposers, receivers, {"C1": ["A", "B"]})


def test_couples_validation_rejects_base_with_too_few_positions():
    proposers = {
        "A": ["H1_A", "Solo", "H2_A", "H2_B"],
        "B": ["H1_A", "Solo", "H2_B", "H2_A"],
        "C": ["H2_A", "H2_B", "H1_A", "Solo"],
        "D": ["H2_B", "H2_A", "Solo", "H1_A"],
    }
    receivers = {
        "H1_A": ["A", "B", "C", "D"],
        "Solo": ["B", "A", "D", "C"],
        "H2_A": ["C", "D", "A", "B"],
        "H2_B": ["D", "C", "B", "A"],
    }

    with pytest.raises(ValueError, match="does not provide enough positions"):
        _validate_couples(proposers, receivers, {"C1": ["A", "B"]})


def test_select_couple_targets_requires_receivers_for_base():
    with pytest.raises(ValueError, match="lacks receivers for preferred base"):
        _select_couple_targets(["A", "B"], "H1", {"A": {"H1": ["H1_A"]}, "B": {}})


def test_select_couple_targets_requires_distinct_receivers():
    with pytest.raises(ValueError, match="lacks enough distinct receivers"):
        _select_couple_targets(
            ["A", "B"],
            "H1",
            {
                "A": {"H1": ["H1_A"]},
                "B": {"H1": ["H1_A"]},
            },
        )
