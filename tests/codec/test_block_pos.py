"""BlockPos / NetworkBlockPos type singletons and cross-format conversion."""

from __future__ import annotations

import pytest

from endstone_endweave.codec import (
    BLOCK_POS,
    NETWORK_BLOCK_POS,
    PacketReader,
    PacketWrapper,
)
from endstone_endweave.codec.writer import PacketWriter
from tests.builders import (
    read_block_pos,
    read_net_block_pos,
    write_block_pos,
    write_net_block_pos,
)


class TestBlockPosTypes:
    def test_network_block_pos_roundtrip(self, writer: PacketWriter) -> None:
        NETWORK_BLOCK_POS.write(writer, (10, 64, -20))
        assert NETWORK_BLOCK_POS.read(PacketReader(writer.to_bytes())) == (10, 64, -20)

    def test_block_pos_roundtrip(self, writer: PacketWriter) -> None:
        BLOCK_POS.write(writer, (10, 64, -20))
        assert BLOCK_POS.read(PacketReader(writer.to_bytes())) == (10, 64, -20)

    def test_uvarint_and_varint_disagree_for_positive_y(self) -> None:
        """uvarint(64) != varint(64) — the encoding difference that motivates the conversion."""
        w_u = PacketWriter()
        w_u.write_uvarint(64)
        w_v = PacketWriter()
        w_v.write_varint(64)
        assert w_u.to_bytes() != w_v.to_bytes()

    def test_passthrough_network_block_pos(self) -> None:
        w = PacketWriter()
        write_net_block_pos(w, 5, 100, -5)
        w.write_byte(0xFF)
        wrapper = PacketWrapper(w.to_bytes())
        assert wrapper.passthrough(NETWORK_BLOCK_POS) == (5, 100, -5)
        assert wrapper.to_bytes() == w.to_bytes()

    @pytest.mark.parametrize("y", [-1, -10, -64])
    def test_network_block_pos_negative_y_roundtrip(self, y: int) -> None:
        """Negative Y must survive roundtrip (uvarint reinterpreted as signed)."""
        w = PacketWriter()
        NETWORK_BLOCK_POS.write(w, (100, y, 50))
        assert NETWORK_BLOCK_POS.read(PacketReader(w.to_bytes())) == (100, y, 50)

    def test_passthrough_network_block_pos_negative_y(self) -> None:
        w = PacketWriter()
        write_net_block_pos(w, 5, -10, -5)
        wrapper = PacketWrapper(w.to_bytes())
        assert wrapper.passthrough(NETWORK_BLOCK_POS) == (5, -10, -5)
        assert wrapper.to_bytes() == w.to_bytes()


class TestBlockPosConversion:
    """NetworkBlockPos <-> BlockPos via wrapper.read/write."""

    def test_net_block_to_block(self) -> None:
        w = PacketWriter()
        write_net_block_pos(w, 10, 64, -30)
        w.write_byte(0xAA)
        wrapper = PacketWrapper(w.to_bytes())
        wrapper.write(BLOCK_POS, wrapper.read(NETWORK_BLOCK_POS))
        r = PacketReader(wrapper.to_bytes())
        assert read_block_pos(r) == (10, 64, -30)
        assert r.read_byte() == 0xAA

    def test_block_to_net_block(self) -> None:
        w = PacketWriter()
        write_block_pos(w, -5, 200, 42)
        w.write_byte(0xBB)
        wrapper = PacketWrapper(w.to_bytes())
        wrapper.write(NETWORK_BLOCK_POS, wrapper.read(BLOCK_POS))
        r = PacketReader(wrapper.to_bytes())
        assert read_net_block_pos(r) == (-5, 200, 42)
        assert r.read_byte() == 0xBB

    def test_y_zero(self) -> None:
        """uvarint(0) == varint(0), but the conversion must still produce correct output."""
        w = PacketWriter()
        write_net_block_pos(w, 0, 0, 0)
        wrapper = PacketWrapper(w.to_bytes())
        wrapper.write(BLOCK_POS, wrapper.read(NETWORK_BLOCK_POS))
        assert read_block_pos(PacketReader(wrapper.to_bytes())) == (0, 0, 0)

    def test_max_overworld_height(self) -> None:
        w = PacketWriter()
        write_net_block_pos(w, 100, 320, -100)
        wrapper = PacketWrapper(w.to_bytes())
        wrapper.write(BLOCK_POS, wrapper.read(NETWORK_BLOCK_POS))
        assert read_block_pos(PacketReader(wrapper.to_bytes())) == (100, 320, -100)

    @pytest.mark.parametrize("y", [-1, -10, -64])
    def test_net_to_block_negative_y(self, y: int) -> None:
        """Regression: issue #3 — negative Y handling across the conversion."""
        w = PacketWriter()
        write_net_block_pos(w, 100, y, 50)
        wrapper = PacketWrapper(w.to_bytes())
        wrapper.write(BLOCK_POS, wrapper.read(NETWORK_BLOCK_POS))
        assert read_block_pos(PacketReader(wrapper.to_bytes())) == (100, y, 50)

    @pytest.mark.parametrize("y", [-1, -10, -64])
    def test_block_to_net_negative_y(self, y: int) -> None:
        w = PacketWriter()
        write_block_pos(w, 100, y, 50)
        wrapper = PacketWrapper(w.to_bytes())
        wrapper.write(NETWORK_BLOCK_POS, wrapper.read(BLOCK_POS))
        assert read_net_block_pos(PacketReader(wrapper.to_bytes())) == (100, y & 0xFFFFFFFF, 50)
