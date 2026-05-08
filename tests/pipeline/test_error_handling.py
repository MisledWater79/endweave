"""Pipeline error paths: handler exceptions, truncated payloads, structured error context."""

from __future__ import annotations

import struct
from typing import Callable
from unittest.mock import MagicMock

import pytest

from endstone_endweave.codec import INT64_LE, INT_LE
from endstone_endweave.codec.wrapper import PacketWrapper
from endstone_endweave.exception import InformativeException
from endstone_endweave.protocol import Protocol

from .conftest import PipelineHarness


@pytest.mark.integration
class TestHandlerException:
    def test_serverbound_exception_cancels_packet(
        self,
        make_pipeline: Callable[..., PipelineHarness],
        make_event: Callable[..., MagicMock],
    ) -> None:
        harness = make_pipeline()

        def bad_handler(wrapper: PacketWrapper) -> None:
            raise ValueError("boom")

        protocol = Protocol(server_protocol=924, client_protocol=944)
        protocol.register_serverbound(42, bad_handler)
        harness.manager.register(protocol)

        harness.pipeline.on_packet_receive(make_event(193, struct.pack(">i", 944)))

        event = make_event(42, b"\x00\x01")
        harness.pipeline.on_packet_receive(event)
        event.cancel.assert_called_once()

    def test_clientbound_exception_cancels_packet(
        self,
        make_pipeline: Callable[..., PipelineHarness],
        make_event: Callable[..., MagicMock],
    ) -> None:
        harness = make_pipeline()

        def bad_handler(wrapper: PacketWrapper) -> None:
            raise ValueError("boom")

        protocol = Protocol(server_protocol=924, client_protocol=944)
        protocol.register_clientbound(42, bad_handler)
        harness.manager.register(protocol)

        harness.pipeline.on_packet_receive(make_event(193, struct.pack(">i", 944)))
        # Trigger pipeline resolution via an arbitrary serverbound packet.
        harness.pipeline.on_packet_receive(make_event(99, b"\x00"))

        event = make_event(42, b"\x00\x01")
        harness.pipeline.on_packet_send(event)
        event.cancel.assert_called_once()


@pytest.mark.integration
class TestTruncatedPayload:
    def test_serverbound_overread_cancels(
        self,
        make_pipeline: Callable[..., PipelineHarness],
        make_event: Callable[..., MagicMock],
    ) -> None:
        """Handler reading 4 bytes from a 1-byte payload should cancel, not crash."""
        harness = make_pipeline()

        def greedy_handler(wrapper):
            wrapper.passthrough(INT_LE)

        protocol = Protocol(server_protocol=924, client_protocol=944)
        protocol.register_serverbound(42, greedy_handler)
        harness.manager.register(protocol)

        harness.pipeline.on_packet_receive(make_event(193, struct.pack(">i", 944)))

        event = make_event(42, b"\x01")
        harness.pipeline.on_packet_receive(event)
        event.cancel.assert_called_once()
        harness.logger.error.assert_called_once()

    def test_clientbound_overread_cancels(
        self,
        make_pipeline: Callable[..., PipelineHarness],
        make_event: Callable[..., MagicMock],
    ) -> None:
        harness = make_pipeline()

        def greedy_handler(wrapper):
            wrapper.passthrough(INT64_LE)

        protocol = Protocol(server_protocol=924, client_protocol=944)
        protocol.register_clientbound(42, greedy_handler)
        harness.manager.register(protocol)

        harness.pipeline.on_packet_receive(make_event(193, struct.pack(">i", 944)))
        harness.pipeline.on_packet_receive(make_event(99, b"\x00"))

        event = make_event(42, b"\x01\x02")
        harness.pipeline.on_packet_send(event)
        event.cancel.assert_called_once()
        harness.logger.error.assert_called_once()


@pytest.mark.integration
class TestStructuredErrorContext:
    def test_error_log_contains_protocol_and_direction(
        self,
        make_pipeline: Callable[..., PipelineHarness],
        make_event: Callable[..., MagicMock],
    ) -> None:
        harness = make_pipeline()

        def bad_handler(wrapper):
            raise RuntimeError("test explosion")

        protocol = Protocol(server_protocol=924, client_protocol=944, name="v924_to_v944")
        protocol.register_serverbound(42, bad_handler)
        harness.manager.register(protocol)

        harness.pipeline.on_packet_receive(make_event(193, struct.pack(">i", 944)))

        event = make_event(42, b"\x00")
        harness.pipeline.on_packet_receive(event)
        event.cancel.assert_called_once()

        msg = harness.logger.error.call_args[0][0]
        assert "Direction: SERVERBOUND" in msg
        assert "Protocol: v924_to_v944" in msg
        assert "Address: 1.2.3.4:1234" in msg
        assert "Please report" in msg


class TestInformativeException:
    def test_set_chaining(self) -> None:
        cause = ValueError("bad data")
        err = InformativeException(cause).set("Direction", "SB").set("Packet", "FOO(1)")
        msg = err.message
        assert "Direction: SB" in msg
        assert "Packet: FOO(1)" in msg
        assert "bad data" in msg

    def test_format_includes_cause_type(self) -> None:
        err = InformativeException(IndexError("out of bounds"))
        msg = err.message
        assert "IndexError" in msg
        assert "out of bounds" in msg

    def test_add_source(self) -> None:
        err = InformativeException(RuntimeError("boom")).add_source(dict).add_source(list)
        msg = err.message
        assert "Source 0: dict" in msg
        assert "Source 1: list" in msg

    def test_comma_separated_format(self) -> None:
        err = InformativeException(RuntimeError("x")).set("A", "1").set("B", "2")
        assert "A: 1, B: 2" in err.message
