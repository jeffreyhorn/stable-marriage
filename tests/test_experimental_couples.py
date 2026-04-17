from __future__ import annotations

import pytest

from stable_marriage.experimental import stable_marriage_with_couples
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
