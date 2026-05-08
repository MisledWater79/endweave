"""Top-level pytest fixtures shared across the entire suite.

Per-area fixtures (e.g. pipeline scaffolding) live in nearer conftests so the
global namespace stays small and intent-focused.
"""

from __future__ import annotations

from typing import Callable
from unittest.mock import MagicMock

import pytest

from endstone_endweave.codec.reader import PacketReader
from endstone_endweave.codec.writer import PacketWriter
from endstone_endweave.connection import UserConnection


@pytest.fixture
def writer() -> PacketWriter:
    """Fresh PacketWriter ready to be written into."""
    return PacketWriter()


@pytest.fixture
def reader_factory() -> type[PacketReader]:
    """Constructor for ad-hoc PacketReader(bytes) instances."""
    return PacketReader


@pytest.fixture
def mock_logger() -> MagicMock:
    """Logger double — assert against .error/.debug/etc. without real I/O."""
    return MagicMock()


@pytest.fixture
def make_connection(mock_logger: MagicMock) -> Callable[..., UserConnection]:
    """Build a UserConnection with sensible defaults; override per-test as needed."""

    def _make(
        address: str = "1.2.3.4:1234",
        *,
        client_protocol: int = 0,
        server_protocol: int = 924,
    ) -> UserConnection:
        return UserConnection(
            address=address,
            logger=mock_logger,
            client_protocol=client_protocol,
            server_protocol=server_protocol,
        )

    return _make


@pytest.fixture
def make_event() -> Callable[..., MagicMock]:
    """Build a packet-event mock matching the Endstone PacketSendEvent / PacketReceiveEvent shape."""

    def _make(packet_id: int, payload: bytes, address: str = "1.2.3.4:1234") -> MagicMock:
        event = MagicMock()
        event.packet_id = packet_id
        event.payload = payload
        event.address = address
        return event

    return _make
