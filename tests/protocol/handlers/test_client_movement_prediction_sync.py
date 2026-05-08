"""v975 -> v944 ClientMovementPredictionSync handler."""

from __future__ import annotations

from endstone_endweave.codec import PacketWrapper
from endstone_endweave.codec.writer import PacketWriter
from endstone_endweave.protocol.v944_to_v975.handlers.client_movement_prediction_sync import (
    rewrite_client_movement_prediction_sync,
)


def test_strips_v975_only_attributes() -> None:
    """1.26.20 added 3 trailing float attributes; downgrading to v944 must drop them."""
    # Build a v975 body. Bitset 0x83 0x01 = bits 0,1,7. 3 bbox + 6 base + 3 v975-only = 12 floats.
    src = PacketWriter()
    src.write_byte(0x83)
    src.write_byte(0x01)
    for i in range(12):
        src.write_float_le(float(i + 1))
    src.write_varint64(-12345)  # ActorUniqueID
    src.write_bool(True)  # Flying

    wrapper = PacketWrapper(src.to_bytes())
    rewrite_client_movement_prediction_sync(wrapper)

    expected = PacketWriter()
    expected.write_byte(0x83)
    expected.write_byte(0x01)
    for i in range(9):
        expected.write_float_le(float(i + 1))
    expected.write_varint64(-12345)
    expected.write_bool(True)

    assert wrapper.to_bytes() == expected.to_bytes()
