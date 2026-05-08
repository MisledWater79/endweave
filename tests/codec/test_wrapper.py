"""PacketWrapper API mechanics: passthrough/read/write/map/cancel and handler integration."""

from __future__ import annotations

import struct
from typing import Callable

from endstone_endweave.codec import (
    BOOL,
    BYTE,
    INT_BE,
    INT_LE,
    STRING,
    VAR_INT,
    PacketWrapper,
)
from endstone_endweave.codec.writer import PacketWriter
from endstone_endweave.connection import UserConnection
from endstone_endweave.protocol import Protocol
from endstone_endweave.protocol.direction import Direction


class TestWrapperBasics:
    def test_passthrough_preserves_data(self) -> None:
        w = PacketWriter()
        w.write_int_be(944)
        w.write_string("hello")
        payload = w.to_bytes()

        wrapper = PacketWrapper(payload)
        assert wrapper.passthrough(INT_BE) == 944
        assert wrapper.passthrough(STRING) == "hello"
        assert wrapper.to_bytes() == payload

    def test_read_consumes_without_writing(self) -> None:
        w = PacketWriter()
        w.write_int_be(944)
        w.write_string("hello")

        wrapper = PacketWrapper(w.to_bytes())
        assert wrapper.read(INT_BE) == 944
        wrapper.passthrough(STRING)

        expected = PacketWriter()
        expected.write_string("hello")
        assert wrapper.to_bytes() == expected.to_bytes()

    def test_write_appends_without_reading(self) -> None:
        w = PacketWriter()
        w.write_string("hello")

        wrapper = PacketWrapper(w.to_bytes())
        wrapper.write(INT_BE, 999)
        wrapper.passthrough(STRING)

        expected = PacketWriter()
        expected.write_int_be(999)
        expected.write_string("hello")
        assert wrapper.to_bytes() == expected.to_bytes()

    def test_cancel_flag(self) -> None:
        wrapper = PacketWrapper(b"\x00")
        assert not wrapper.cancelled
        wrapper.cancel()
        assert wrapper.cancelled

    def test_passthrough_all_writes_remaining(self) -> None:
        wrapper = PacketWrapper(b"\x01\x02\x03\x04")
        wrapper.read(BYTE)
        assert wrapper.passthrough_all() == b"\x02\x03\x04"
        assert wrapper.to_bytes() == b"\x02\x03\x04"

    def test_to_bytes_appends_unread_tail(self) -> None:
        payload = b"\x01\x02\x03\x04"
        wrapper = PacketWrapper(payload)
        wrapper.passthrough(BYTE)
        assert wrapper.to_bytes() == payload

    def test_map_converts_type(self) -> None:
        w = PacketWriter()
        w.write_varint(42)
        w.write_byte(0xFF)
        wrapper = PacketWrapper(w.to_bytes())
        assert wrapper.map(VAR_INT, INT_LE) == 42
        result = wrapper.to_bytes()
        assert result[:4] == struct.pack("<i", 42)
        assert result[4] == 0xFF

    def test_has_remaining(self) -> None:
        wrapper = PacketWrapper(b"\x01\x02")
        assert wrapper.has_remaining
        wrapper.read(BYTE)
        assert wrapper.has_remaining
        wrapper.read(BYTE)
        assert not wrapper.has_remaining

    def test_user_attached(self, make_connection: Callable[..., UserConnection]) -> None:
        conn = make_connection()
        wrapper = PacketWrapper(b"\x00", user=conn)
        assert wrapper.user is conn


class TestWrapperTransforms:
    def test_remap_int_field(self) -> None:
        w = PacketWriter()
        w.write_int_be(944)
        w.write_bytes(b"\xde\xad")

        wrapper = PacketWrapper(w.to_bytes())
        assert wrapper.read(INT_BE) == 944
        wrapper.write(INT_BE, 924)
        wrapper.passthrough_all()

        result = wrapper.to_bytes()
        assert struct.unpack(">i", result[:4])[0] == 924
        assert result[4:] == b"\xde\xad"

    def test_delete_middle_field(self) -> None:
        w = PacketWriter()
        w.write_byte(0x01)
        w.write_int_le(42)
        w.write_byte(0x02)

        wrapper = PacketWrapper(w.to_bytes())
        wrapper.passthrough(BYTE)
        wrapper.read(INT_LE)
        wrapper.passthrough(BYTE)
        assert wrapper.to_bytes() == bytes([0x01, 0x02])

    def test_insert_field_in_middle(self) -> None:
        w = PacketWriter()
        w.write_byte(0x01)
        w.write_byte(0x02)

        wrapper = PacketWrapper(w.to_bytes())
        wrapper.passthrough(BYTE)
        wrapper.write(BOOL, True)
        wrapper.passthrough(BYTE)
        assert wrapper.to_bytes() == bytes([0x01, 0x01, 0x02])


class TestWrapperHandlerIntegration:
    """Wrapper-style handlers wired through Protocol.transform."""

    def test_handler_rewrites_packet(self, make_connection: Callable[..., UserConnection]) -> None:
        def rewrite_protocol(wrapper: PacketWrapper) -> None:
            assert wrapper.user is not None
            wrapper.read(INT_BE)
            wrapper.write(INT_BE, wrapper.user.server_protocol)

        p = Protocol(server_protocol=924, client_protocol=944)
        p.register_serverbound(193, rewrite_protocol)

        conn = make_connection(server_protocol=924)
        w = PacketWriter()
        w.write_int_be(944)
        w.write_bytes(b"\xde\xad")
        wrapper = PacketWrapper(w.to_bytes(), user=conn)

        p.transform(Direction.SERVERBOUND, 193, wrapper)
        assert not wrapper.cancelled

        result = wrapper.to_bytes()
        assert struct.unpack(">i", result[:4])[0] == 924
        assert result[4:] == b"\xde\xad"

    def test_handler_can_cancel(self, make_connection: Callable[..., UserConnection]) -> None:
        def cancel_handler(wrapper: PacketWrapper) -> None:
            wrapper.cancel()

        p = Protocol(server_protocol=924, client_protocol=944)
        p.register_serverbound(42, cancel_handler)

        wrapper = PacketWrapper(b"\x00", user=make_connection())
        p.transform(Direction.SERVERBOUND, 42, wrapper)
        assert wrapper.cancelled

    def test_passthrough_all_handler_leaves_payload_unchanged(
        self, make_connection: Callable[..., UserConnection]
    ) -> None:
        def noop_handler(wrapper: PacketWrapper) -> None:
            wrapper.passthrough_all()

        p = Protocol(server_protocol=924, client_protocol=944)
        p.register_serverbound(42, noop_handler)

        wrapper = PacketWrapper(b"\x01\x02\x03", user=make_connection())
        p.transform(Direction.SERVERBOUND, 42, wrapper)
        assert not wrapper.cancelled
        assert wrapper.to_bytes() == b"\x01\x02\x03"
