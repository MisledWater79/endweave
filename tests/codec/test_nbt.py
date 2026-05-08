"""NBT compound parsing via read_nbt + the NAMED_COMPOUND_TAG type singleton."""

from __future__ import annotations

import struct

from endstone_endweave.codec import (
    NAMED_COMPOUND_TAG,
    ByteTag,
    CompoundTag,
    PacketReader,
    PacketWrapper,
)
from endstone_endweave.codec.types.nbt import read_nbt
from tests.builders import nbt_string, nbt_varint, nbt_varint64


class TestSkipNbtCompound:
    """read_nbt must consume exactly the NBT bytes, leaving sentinels behind."""

    def test_empty_compound(self) -> None:
        data = bytes([10]) + nbt_string("") + bytes([0])
        r = PacketReader(data + b"\xff")
        read_nbt(r)
        assert r.read_byte() == 0xFF

    def test_null_root(self) -> None:
        """Root type byte 0 is sentinel for absent NBT — read_nbt returns None."""
        r = PacketReader(bytes([0]) + b"\xab")
        assert read_nbt(r) is None
        assert r.read_byte() == 0xAB

    def test_compound_with_primitives(self) -> None:
        buf = bytearray()
        buf.append(10)
        buf.extend(nbt_string("root"))
        buf.append(1)
        buf.extend(nbt_string("b"))
        buf.append(42)
        buf.append(2)
        buf.extend(nbt_string("s"))
        buf.extend(struct.pack("<h", -100))
        buf.append(3)
        buf.extend(nbt_string("i"))
        buf.extend(nbt_varint(999))
        buf.append(4)
        buf.extend(nbt_string("l"))
        buf.extend(nbt_varint64(123456789))
        buf.append(5)
        buf.extend(nbt_string("f"))
        buf.extend(struct.pack("<f", 3.14))
        buf.append(6)
        buf.extend(nbt_string("d"))
        buf.extend(struct.pack("<d", 2.718))
        buf.append(0)
        buf.extend(b"\xee")
        r = PacketReader(bytes(buf))
        read_nbt(r)
        assert r.read_byte() == 0xEE

    def test_compound_with_string_and_arrays(self) -> None:
        buf = bytearray()
        buf.append(10)
        buf.extend(nbt_string(""))
        buf.append(8)
        buf.extend(nbt_string("str"))
        buf.extend(nbt_string("hello"))
        buf.append(7)
        buf.extend(nbt_string("ba"))
        buf.extend(nbt_varint(3))
        buf.extend(b"\x01\x02\x03")
        buf.append(11)
        buf.extend(nbt_string("ia"))
        buf.extend(nbt_varint(2))
        buf.extend(nbt_varint(10))
        buf.extend(nbt_varint(20))
        buf.append(0)
        buf.extend(b"\xdd")
        r = PacketReader(bytes(buf))
        read_nbt(r)
        assert r.read_byte() == 0xDD

    def test_nested_compound(self) -> None:
        buf = bytearray()
        buf.append(10)
        buf.extend(nbt_string(""))
        buf.append(10)
        buf.extend(nbt_string("inner"))
        buf.append(1)
        buf.extend(nbt_string("x"))
        buf.append(7)
        buf.append(0)
        buf.append(0)
        buf.extend(b"\xcc")
        r = PacketReader(bytes(buf))
        read_nbt(r)
        assert r.read_byte() == 0xCC

    def test_list_of_ints(self) -> None:
        buf = bytearray()
        buf.append(10)
        buf.extend(nbt_string(""))
        buf.append(9)
        buf.extend(nbt_string("nums"))
        buf.append(3)
        buf.extend(nbt_varint(3))
        buf.extend(nbt_varint(100))
        buf.extend(nbt_varint(200))
        buf.extend(nbt_varint(300))
        buf.append(0)
        buf.extend(b"\xbb")
        r = PacketReader(bytes(buf))
        read_nbt(r)
        assert r.read_byte() == 0xBB

    def test_list_of_compounds(self) -> None:
        buf = bytearray()
        buf.append(10)
        buf.extend(nbt_string(""))
        buf.append(9)
        buf.extend(nbt_string("items"))
        buf.append(10)
        buf.extend(nbt_varint(2))
        buf.append(1)
        buf.extend(nbt_string("a"))
        buf.append(1)
        buf.append(0)
        buf.append(3)
        buf.extend(nbt_string("b"))
        buf.extend(nbt_varint(42))
        buf.append(0)
        buf.append(0)
        buf.extend(b"\xaa")
        r = PacketReader(bytes(buf))
        read_nbt(r)
        assert r.read_byte() == 0xAA


class TestNamedCompoundTagPassthrough:
    def test_passthrough_returns_compound_tag(self) -> None:
        """NAMED_COMPOUND_TAG parses into CompoundTag and round-trips identically."""
        buf = bytearray()
        buf.append(10)
        buf.extend(nbt_string(""))
        buf.append(1)
        buf.extend(nbt_string("x"))
        buf.append(5)
        buf.append(0)
        nbt_bytes = bytes(buf)

        wrapper = PacketWrapper(nbt_bytes + b"\x99")
        tag = wrapper.passthrough(NAMED_COMPOUND_TAG)
        assert isinstance(tag, CompoundTag)
        assert isinstance(tag["x"], ByteTag)
        assert tag["x"].value == 5

        trailing = wrapper.passthrough_all()
        assert trailing == b"\x99"
        assert wrapper.to_bytes() == nbt_bytes + b"\x99"
