"""Multi-step chain execution and the per-protocol init() hook."""

from __future__ import annotations

import struct
from typing import Callable
from unittest.mock import MagicMock

import pytest

from endstone_endweave.codec import BYTE
from endstone_endweave.protocol import Protocol

from .conftest import PipelineHarness


@pytest.mark.integration
class TestChainTransformOrder:
    """Two protocols (A->B, B->C) compose; verify direction-specific ordering."""

    def test_clientbound_runs_chain_in_reverse(
        self,
        make_pipeline: Callable[..., PipelineHarness],
        make_event: Callable[..., MagicMock],
    ) -> None:
        """Each protocol appends a sentinel byte; verify both ran and in the right order."""
        harness = make_pipeline(server_protocol=100)

        def append_0xAA(wrapper):
            wrapper.passthrough_all()
            wrapper.write(BYTE, 0xAA)

        def append_0xBB(wrapper):
            wrapper.passthrough_all()
            wrapper.write(BYTE, 0xBB)

        p_ab = Protocol(server_protocol=100, client_protocol=200, name="a_to_b")
        p_ab.register_clientbound(42, append_0xAA)
        p_bc = Protocol(server_protocol=200, client_protocol=300, name="b_to_c")
        p_bc.register_clientbound(42, append_0xBB)
        harness.manager.register(p_ab)
        harness.manager.register(p_bc)

        # Detect client protocol via RequestNetworkSettings, then trigger pipeline resolution
        # via a second serverbound packet.
        harness.pipeline.on_packet_receive(make_event(193, struct.pack(">i", 300)))
        harness.pipeline.on_packet_receive(make_event(99, b"\x00"))

        event = make_event(42, b"\x01")
        harness.pipeline.on_packet_send(event)

        # Chain is [p_bc, p_ab]; clientbound runs reversed -> p_ab first (0xAA), then p_bc (0xBB).
        assert event.payload == b"\x01\xaa\xbb"

    def test_serverbound_runs_chain_in_order(
        self,
        make_pipeline: Callable[..., PipelineHarness],
        make_event: Callable[..., MagicMock],
    ) -> None:
        """Same wrapper threads through each step; verify serverbound order is [client-first, server-last]."""
        harness = make_pipeline(server_protocol=100)

        def sb_bc(wrapper):
            wrapper.passthrough(BYTE)
            wrapper.write(BYTE, 0xCC)

        def sb_ab(wrapper):
            wrapper.passthrough_all()
            wrapper.write(BYTE, 0xDD)

        p_ab = Protocol(server_protocol=100, client_protocol=200, name="a_to_b")
        p_ab.register_serverbound(42, sb_ab)
        p_bc = Protocol(server_protocol=200, client_protocol=300, name="b_to_c")
        p_bc.register_serverbound(42, sb_bc)
        harness.manager.register(p_ab)
        harness.manager.register(p_bc)

        harness.pipeline.on_packet_receive(make_event(193, struct.pack(">i", 300)))

        event = make_event(42, b"\x01")
        harness.pipeline.on_packet_receive(event)

        # Chain [p_bc, p_ab], serverbound: p_bc first (0x01 -> 0x01CC), p_ab next (-> 0x01CCDD).
        assert event.payload == b"\x01\xcc\xdd"


@pytest.mark.integration
class TestProtocolInitHook:
    def test_init_called_once_per_protocol_in_chain(
        self,
        make_pipeline: Callable[..., PipelineHarness],
        make_event: Callable[..., MagicMock],
    ) -> None:
        harness = make_pipeline(server_protocol=100)
        init_calls: list[tuple[str, str]] = []

        class TrackingProtocol(Protocol):
            def init(self, connection):
                init_calls.append((self.name, connection.address))

        harness.manager.register(TrackingProtocol(server_protocol=100, client_protocol=200, name="p1"))
        harness.manager.register(TrackingProtocol(server_protocol=200, client_protocol=300, name="p2"))

        harness.pipeline.on_packet_receive(make_event(193, struct.pack(">i", 300)))
        harness.pipeline.on_packet_receive(make_event(42, b"\x00"))

        assert len(init_calls) == 2
        assert {c[0] for c in init_calls} == {"p1", "p2"}

    def test_init_not_called_again_on_subsequent_packets(
        self,
        make_pipeline: Callable[..., PipelineHarness],
        make_event: Callable[..., MagicMock],
    ) -> None:
        harness = make_pipeline(server_protocol=924)
        init_count = [0]

        class CountingProtocol(Protocol):
            def init(self, connection):
                init_count[0] += 1

        harness.manager.register(CountingProtocol(server_protocol=924, client_protocol=944, name="cnt"))

        harness.pipeline.on_packet_receive(make_event(193, struct.pack(">i", 944)))
        for _ in range(5):
            harness.pipeline.on_packet_receive(make_event(42, b"\x00"))

        assert init_count[0] == 1
