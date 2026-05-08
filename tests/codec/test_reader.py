"""PacketReader bounds checks and cursor-state behaviour."""

from __future__ import annotations

import pytest

from endstone_endweave.codec.reader import PacketReader
from endstone_endweave.codec.writer import PacketWriter


class TestBoundsChecks:
    def test_read_bytes_overread(self) -> None:
        with pytest.raises(ValueError, match="read_bytes"):
            PacketReader(b"\x00\x01").read_bytes(3)

    def test_read_bytes_negative(self) -> None:
        with pytest.raises(ValueError, match="read_bytes"):
            PacketReader(b"\x00\x01").read_bytes(-1)

    def test_read_bytes_exact_remaining(self) -> None:
        assert PacketReader(b"\x00\x01\x02").read_bytes(3) == b"\x00\x01\x02"

    def test_skip_past_end(self) -> None:
        with pytest.raises(ValueError, match="skip"):
            PacketReader(b"\x00\x01").skip(3)

    def test_skip_negative(self) -> None:
        with pytest.raises(ValueError, match="skip"):
            PacketReader(b"\x00\x01").skip(-1)

    def test_skip_exact_remaining(self) -> None:
        r = PacketReader(b"\x00\x01")
        r.skip(2)
        assert not r.has_remaining

    def test_oversized_string_length_rejected(self) -> None:
        """String length prefix exceeding 131068 bytes must raise."""
        w = PacketWriter()
        w.write_uvarint(200000)
        w.write_bytes(b"\x00" * 200000)
        with pytest.raises(ValueError, match="String length"):
            PacketReader(w.to_bytes()).read_string()


class TestCursorState:
    def test_position_advances(self) -> None:
        r = PacketReader(b"\x00\x01\x02\x03")
        assert r.position == 0
        r.read_byte()
        assert r.position == 1

    def test_has_remaining(self) -> None:
        r = PacketReader(b"\x00")
        assert r.has_remaining
        r.read_byte()
        assert not r.has_remaining

    def test_remaining_count(self) -> None:
        r = PacketReader(b"\x00\x01\x02")
        assert r.remaining == 3
        r.read_byte()
        assert r.remaining == 2

    def test_skip(self) -> None:
        r = PacketReader(b"\x00\x01\x02\x03")
        r.skip(2)
        assert r.read_byte() == 0x02

    def test_read_remaining_drains_buffer(self) -> None:
        r = PacketReader(b"\x00\x01\x02\x03")
        r.read_byte()
        assert r.read_remaining() == b"\x01\x02\x03"
        assert not r.has_remaining
