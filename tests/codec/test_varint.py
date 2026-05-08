"""Varint, signed varint, and varlong encode/decode."""

from __future__ import annotations

import pytest

from endstone_endweave.codec.reader import PacketReader
from endstone_endweave.codec.writer import PacketWriter


class TestUnsignedVarint:
    @pytest.mark.parametrize("value", [0, 1, 42, 127, 128, 300, 16384, 2097152, 0xFFFFFFFF])
    def test_roundtrip(self, value: int) -> None:
        w = PacketWriter()
        w.write_uvarint(value)
        assert PacketReader(w.to_bytes()).read_uvarint() == value

    def test_single_byte_encoding(self, writer: PacketWriter) -> None:
        writer.write_uvarint(1)
        assert writer.to_bytes() == b"\x01"

    def test_two_byte_encoding(self, writer: PacketWriter) -> None:
        writer.write_uvarint(300)
        data = writer.to_bytes()
        assert len(data) == 2
        assert PacketReader(data).read_uvarint() == 300


class TestSignedVarint:
    @pytest.mark.parametrize("value", [0, 1, -1, 42, -42, 2147483647, -2147483648])
    def test_roundtrip(self, value: int) -> None:
        w = PacketWriter()
        w.write_varint(value)
        assert PacketReader(w.to_bytes()).read_varint() == value

    @pytest.mark.parametrize(
        ("value", "encoded"),
        [
            (0, b"\x00"),
            (-1, b"\x01"),
            (1, b"\x02"),
        ],
    )
    def test_zigzag_encoding(self, value: int, encoded: bytes) -> None:
        """zigzag: 0->0, -1->1, 1->2, -2->3."""
        w = PacketWriter()
        w.write_varint(value)
        assert w.to_bytes() == encoded


class TestUnsignedVarint64:
    @pytest.mark.parametrize("value", [0, 1, 0xFFFFFFFF, 0xFFFFFFFFFFFFFFFF])
    def test_roundtrip(self, value: int) -> None:
        w = PacketWriter()
        w.write_uvarint64(value)
        assert PacketReader(w.to_bytes()).read_uvarint64() == value
