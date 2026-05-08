"""Base protocol: client-version detection and login rewriting."""

from __future__ import annotations

import struct
from typing import Callable

from endstone_endweave.codec import PacketWrapper
from endstone_endweave.connection import UserConnection
from endstone_endweave.protocol.base import (
    create_base_protocol,
    detect_client_protocol,
)
from endstone_endweave.protocol.direction import Direction
from endstone_endweave.protocol.packet_ids import PacketId


class TestDetectClientProtocol:
    def test_reads_protocol_and_sets_on_connection(self, make_connection: Callable[..., UserConnection]) -> None:
        connection = make_connection(server_protocol=924)
        payload = struct.pack(">i", 944)
        wrapper = PacketWrapper(payload, user=connection)

        detect_client_protocol(wrapper)

        assert connection.client_protocol == 944
        assert not wrapper.cancelled
        # Outbound payload is rewritten to the server's protocol so the server accepts the login.
        assert wrapper.to_bytes() == struct.pack(">i", 924)

    def test_short_payload_does_not_crash(self, make_connection: Callable[..., UserConnection]) -> None:
        connection = make_connection(server_protocol=924)
        wrapper = PacketWrapper(b"\x00", user=connection)
        try:
            detect_client_protocol(wrapper)
        except Exception:
            pass
        assert connection.client_protocol == 0


class TestCreateBaseProtocol:
    def test_registers_correct_handlers(self, make_connection: Callable[..., UserConnection]) -> None:
        bp = create_base_protocol(924)
        assert bp.server_protocol == 924
        assert bp.client_protocol == 0
        assert bp.is_base

        connection = make_connection(server_protocol=924)
        wrapper = PacketWrapper(struct.pack(">i", 944), user=connection)
        bp.transform(Direction.SERVERBOUND, PacketId.REQUEST_NETWORK_SETTINGS, wrapper)
        assert connection.client_protocol == 944
