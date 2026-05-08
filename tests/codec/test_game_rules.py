"""GameRules and Experiments type passthrough."""

from __future__ import annotations

from endstone_endweave.codec import (
    BOOL,
    EXPERIMENTS,
    GAME_RULES,
    PacketWrapper,
)
from endstone_endweave.codec.writer import PacketWriter


class TestGameRules:
    def test_zero_rules(self) -> None:
        w = PacketWriter()
        w.write_uvarint(0)
        w.write_byte(0xFF)
        wrapper = PacketWrapper(w.to_bytes())
        wrapper.passthrough(GAME_RULES)
        assert wrapper.to_bytes() == w.to_bytes()

    def test_mixed_rule_types(self) -> None:
        """A bool, an int, and a float game rule (each with its is-default flag)."""
        w = PacketWriter()
        w.write_uvarint(3)
        w.write_string("rule_bool")
        w.write_bool(True)
        w.write_byte(1)
        w.write_bool(False)
        w.write_string("rule_int")
        w.write_bool(False)
        w.write_byte(2)
        w.write_varint(42)
        w.write_string("rule_float")
        w.write_bool(True)
        w.write_byte(3)
        w.write_float_le(1.5)
        payload = w.to_bytes()

        wrapper = PacketWrapper(payload)
        wrapper.passthrough(GAME_RULES)
        assert wrapper.to_bytes() == payload


class TestExperiments:
    def test_zero_experiments(self) -> None:
        w = PacketWriter()
        w.write_uint_le(0)
        w.write_bool(False)
        payload = w.to_bytes()

        wrapper = PacketWrapper(payload)
        wrapper.passthrough(EXPERIMENTS)
        wrapper.passthrough(BOOL)
        assert wrapper.to_bytes() == payload

    def test_with_experiments(self) -> None:
        w = PacketWriter()
        w.write_uint_le(2)
        w.write_string("exp1")
        w.write_bool(True)
        w.write_string("exp2")
        w.write_bool(False)
        w.write_bool(True)
        payload = w.to_bytes()

        wrapper = PacketWrapper(payload)
        wrapper.passthrough(EXPERIMENTS)
        wrapper.passthrough(BOOL)
        assert wrapper.to_bytes() == payload
