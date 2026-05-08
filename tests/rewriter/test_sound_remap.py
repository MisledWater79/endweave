"""Sound-id remap functions across every supported version pair.

Each pair exposes a `shift_up` (forward) and `shift_down`/`cap` (backward)
function on its mapping data; these tests assert the threshold behaviour for
both directions in one parametrized table.
"""

from __future__ import annotations

from typing import Callable

import pytest

from endstone_endweave.protocol.mappings.v860_v898 import MAPPINGS as M_860_898
from endstone_endweave.protocol.mappings.v898_v924 import MAPPINGS as M_898_924
from endstone_endweave.protocol.mappings.v924_v944 import MAPPINGS as M_924_944


@pytest.mark.parametrize(
    ("remap", "below", "at_threshold_input", "at_threshold_output", "above_input", "above_output"),
    [
        # v860 -> v898: Undefined shifts 566 -> 578, IDs above shift by +12.
        pytest.param(M_860_898.sound.shift_up, 565, 566, 578, 600, 612, id="v860_to_v898"),
        # v898 -> v924: Undefined shifts 578 -> 597, IDs above shift by +19.
        pytest.param(M_898_924.sound.shift_up, 577, 578, 597, 600, 619, id="v898_to_v924"),
        # v924 -> v944: Undefined shifts 597 -> 599, IDs above shift by +2.
        pytest.param(M_924_944.sound.shift_up, 596, 597, 599, 598, 600, id="v924_to_v944"),
    ],
)
def test_shift_up(
    remap: Callable[[int], int],
    below: int,
    at_threshold_input: int,
    at_threshold_output: int,
    above_input: int,
    above_output: int,
) -> None:
    assert remap(0) == 0
    assert remap(below) == below
    assert remap(at_threshold_input) == at_threshold_output
    assert remap(above_input) == above_output


class TestShiftDownV898ToV860:
    """Going backwards: new sounds collapse to the older Undefined ID."""

    remap = staticmethod(M_860_898.sound.shift_down)

    def test_below_threshold_unchanged(self) -> None:
        assert self.remap(0) == 0
        assert self.remap(565) == 565

    @pytest.mark.parametrize("v", list(range(566, 578)))
    def test_new_sounds_collapse_to_v860_undefined(self, v: int) -> None:
        assert self.remap(v) == 566

    def test_v898_undefined_maps_back(self) -> None:
        assert self.remap(578) == 566

    def test_above_v898_undefined_shifts_back(self) -> None:
        assert self.remap(579) == 567
        assert self.remap(600) == 588


class TestCapV924ToV898:
    """Sounds added after v898 cap at v898 Undefined."""

    remap = staticmethod(M_898_924.sound.cap)

    def test_below_threshold(self) -> None:
        assert self.remap(0) == 0
        assert self.remap(577) == 577

    @pytest.mark.parametrize("v", [578, 597, 1000])
    def test_at_or_above_caps_to_578(self, v: int) -> None:
        assert self.remap(v) == 578


class TestShiftDownV944ToV924:
    remap = staticmethod(M_924_944.sound.shift_down)

    def test_below_threshold(self) -> None:
        assert self.remap(0) == 0
        assert self.remap(596) == 596

    @pytest.mark.parametrize("v", [597, 598])
    def test_growth_events_collapse_to_v924_undefined(self, v: int) -> None:
        """v944 PauseGrowth(597) and ResetGrowth(598) -> v924 Undefined (597)."""
        assert self.remap(v) == 597

    def test_v944_undefined_maps_back(self) -> None:
        assert self.remap(599) == 597

    def test_above_v944_undefined_shifts_back(self) -> None:
        assert self.remap(600) == 598
        assert self.remap(1000) == 998
