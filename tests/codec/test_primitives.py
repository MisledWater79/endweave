"""PacketReader / PacketWriter primitive type roundtrips and the type-singleton wrappers."""

from __future__ import annotations

import struct

import pytest

from endstone_endweave.codec import (
    BOOL,
    BYTE,
    FLOAT_LE,
    INT64_LE,
    INT_BE,
    INT_LE,
    REMAINING_BYTES,
    SHORT_LE,
    STRING,
    UINT_LE,
    USHORT_LE,
    UUID,
    UVAR_INT,
    UVAR_INT64,
    VAR_INT,
    VAR_INT64,
    PacketReader,
    PacketWrapper,
)
from endstone_endweave.codec.writer import PacketWriter


class TestRawPrimitives:
    def test_byte(self, writer: PacketWriter) -> None:
        writer.write_byte(0xFF)
        assert PacketReader(writer.to_bytes()).read_byte() == 0xFF

    def test_bool(self, writer: PacketWriter) -> None:
        writer.write_bool(True)
        writer.write_bool(False)
        r = PacketReader(writer.to_bytes())
        assert r.read_bool() is True
        assert r.read_bool() is False

    def test_short_le(self, writer: PacketWriter) -> None:
        writer.write_short_le(-1234)
        assert PacketReader(writer.to_bytes()).read_short_le() == -1234

    def test_int_le(self, writer: PacketWriter) -> None:
        writer.write_int_le(-100000)
        assert PacketReader(writer.to_bytes()).read_int_le() == -100000

    def test_int_be(self, writer: PacketWriter) -> None:
        writer.write_int_be(924)
        data = writer.to_bytes()
        assert struct.unpack(">i", data)[0] == 924
        assert PacketReader(data).read_int_be() == 924

    def test_long_le(self, writer: PacketWriter) -> None:
        writer.write_int64_le(1234567890123)
        assert PacketReader(writer.to_bytes()).read_int64_le() == 1234567890123

    def test_float_le(self, writer: PacketWriter) -> None:
        writer.write_float_le(3.14)
        assert abs(PacketReader(writer.to_bytes()).read_float_le() - 3.14) < 0.001

    def test_bytes(self, writer: PacketWriter) -> None:
        writer.write_bytes(b"\x01\x02\x03")
        assert PacketReader(writer.to_bytes()).read_bytes(3) == b"\x01\x02\x03"


def _roundtrip(field_type: object, value: object) -> None:
    w = PacketWriter()
    field_type.write(w, value)  # type: ignore[attr-defined]
    payload = w.to_bytes()
    wrapper = PacketWrapper(payload)
    result = wrapper.passthrough(field_type)
    assert result == value
    assert wrapper.to_bytes() == payload


class TestTypeSingletons:
    """Each type singleton must read what it writes through the wrapper."""

    def test_byte(self) -> None:
        _roundtrip(BYTE, 0xFF)

    @pytest.mark.parametrize("value", [True, False])
    def test_bool(self, value: bool) -> None:
        _roundtrip(BOOL, value)

    def test_short_le(self) -> None:
        _roundtrip(SHORT_LE, -1234)

    def test_ushort_le(self) -> None:
        _roundtrip(USHORT_LE, 65535)

    def test_int_le(self) -> None:
        _roundtrip(INT_LE, -100000)

    def test_int_be(self) -> None:
        _roundtrip(INT_BE, 924)

    def test_uint_le(self) -> None:
        _roundtrip(UINT_LE, 0xDEADBEEF)

    def test_long_le(self) -> None:
        _roundtrip(INT64_LE, 1234567890123)

    def test_float_le(self) -> None:
        w = PacketWriter()
        FLOAT_LE.write(w, 3.14)
        wrapper = PacketWrapper(w.to_bytes())
        assert abs(wrapper.passthrough(FLOAT_LE) - 3.14) < 0.001

    @pytest.mark.parametrize("value", [0, 1, -1, 42, -42, 2147483647, -2147483648])
    def test_var_int(self, value: int) -> None:
        _roundtrip(VAR_INT, value)

    @pytest.mark.parametrize("value", [0, 1, 127, 128, 300, 0xFFFFFFFF])
    def test_uvar_int(self, value: int) -> None:
        _roundtrip(UVAR_INT, value)

    @pytest.mark.parametrize("value", [0, 1, -1, 2147483647])
    def test_var_long(self, value: int) -> None:
        _roundtrip(VAR_INT64, value)

    @pytest.mark.parametrize("value", [0, 1, 0xFFFFFFFF, 0xFFFFFFFFFFFFFFFF])
    def test_uvar_long(self, value: int) -> None:
        _roundtrip(UVAR_INT64, value)

    @pytest.mark.parametrize("value", ["", "hello world"])
    def test_string(self, value: str) -> None:
        _roundtrip(STRING, value)

    def test_uuid(self) -> None:
        _roundtrip(UUID, b"\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f\x10")

    def test_remaining_bytes(self) -> None:
        _roundtrip(REMAINING_BYTES, b"\xde\xad\xbe\xef")
