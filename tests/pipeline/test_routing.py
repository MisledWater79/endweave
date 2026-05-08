"""Pipeline routing: session bootstrap, passthrough, and serverbound rewrite."""

from __future__ import annotations

import struct
from typing import Callable
from unittest.mock import MagicMock

import pytest

from endstone_endweave.codec import REMAINING_BYTES
from endstone_endweave.codec.wrapper import PacketWrapper
from endstone_endweave.protocol import Protocol

from .conftest import PipelineHarness


@pytest.mark.integration
class TestSessionBootstrap:
    def test_request_network_settings_creates_session(
        self,
        make_pipeline: Callable[..., PipelineHarness],
        make_event: Callable[..., MagicMock],
    ) -> None:
        harness = make_pipeline()
        event = make_event(193, struct.pack(">i", 944))
        harness.pipeline.on_packet_receive(event)

        connection = harness.connections.get("1.2.3.4:1234")
        assert connection is not None
        assert connection.client_protocol == 944


@pytest.mark.integration
class TestPassthrough:
    def test_no_translation_when_versions_match(
        self,
        make_pipeline: Callable[..., PipelineHarness],
        make_event: Callable[..., MagicMock],
    ) -> None:
        harness = make_pipeline()
        harness.pipeline.on_packet_receive(make_event(193, struct.pack(">i", 924)))

        event = make_event(42, b"\x00\x01")
        harness.pipeline.on_packet_receive(event)
        event.cancel.assert_not_called()

    def test_no_translation_when_no_protocol_chain(
        self,
        make_pipeline: Callable[..., PipelineHarness],
        make_event: Callable[..., MagicMock],
    ) -> None:
        harness = make_pipeline()
        harness.pipeline.on_packet_receive(make_event(193, struct.pack(">i", 999)))

        event = make_event(42, b"\x00\x01")
        harness.pipeline.on_packet_receive(event)
        event.cancel.assert_not_called()

    def test_send_passthrough_without_session(
        self,
        make_pipeline: Callable[..., PipelineHarness],
        make_event: Callable[..., MagicMock],
    ) -> None:
        harness = make_pipeline()
        event = make_event(42, b"\x00\x01")
        harness.pipeline.on_packet_send(event)
        event.cancel.assert_not_called()


@pytest.mark.integration
class TestProtocolDispatch:
    def test_protocol_called_for_serverbound(
        self,
        make_pipeline: Callable[..., PipelineHarness],
        make_event: Callable[..., MagicMock],
    ) -> None:
        harness = make_pipeline()

        def rewrite_handler(wrapper: PacketWrapper) -> None:
            wrapper.read(REMAINING_BYTES)
            wrapper.write(REMAINING_BYTES, b"\xff")

        protocol = Protocol(server_protocol=924, client_protocol=944)
        protocol.register_serverbound(42, rewrite_handler)
        harness.manager.register(protocol)

        harness.pipeline.on_packet_receive(make_event(193, struct.pack(">i", 944)))

        event = make_event(42, b"\x00\x01")
        harness.pipeline.on_packet_receive(event)
        assert event.payload == b"\xff"
