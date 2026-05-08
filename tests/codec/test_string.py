"""String type roundtrips and length-prefix layout."""

from __future__ import annotations

import pytest

from endstone_endweave.codec.reader import PacketReader
from endstone_endweave.codec.writer import PacketWriter


@pytest.mark.parametrize("value", ["", "hello", "hello 🌍"])
def test_string_roundtrip(value: str) -> None:
    w = PacketWriter()
    w.write_string(value)
    assert PacketReader(w.to_bytes()).read_string() == value


def test_string_length_prefix(writer: PacketWriter) -> None:
    writer.write_string("abc")
    data = writer.to_bytes()
    assert data[0] == 3
    assert data[1:] == b"abc"
