"""DebugHandler filtering, log formatting, and the packet_label helper."""

from __future__ import annotations

from unittest.mock import MagicMock

from endstone_endweave.debug import DebugHandler, packet_label


class TestDebugHandlerToggle:
    def test_disabled_logs_nothing(self, mock_logger: MagicMock) -> None:
        handler = DebugHandler(mock_logger, enabled=False)
        handler.log(42, "test message")
        mock_logger.debug.assert_not_called()

    def test_enabled_no_filter_logs_everything(self, mock_logger: MagicMock) -> None:
        handler = DebugHandler(mock_logger, enabled=True)
        handler.log(42, "msg1")
        handler.log(99, "msg2")
        assert mock_logger.debug.call_count == 2

    def test_enabled_with_filter(self, mock_logger: MagicMock) -> None:
        handler = DebugHandler(mock_logger, enabled=True, packets=frozenset({42}))
        handler.log(42, "should log")
        handler.log(99, "should not log")
        assert mock_logger.debug.call_count == 1
        assert "should log" in mock_logger.debug.call_args[0][0]

    def test_pre_post_flags(self, mock_logger: MagicMock) -> None:
        handler = DebugHandler(mock_logger, enabled=True, log_pre=True, log_post=False)
        assert handler.log_pre_packet_transform
        assert not handler.log_post_packet_transform


class TestDebugHandlerFromConfig:
    def test_with_packet_filter(self, mock_logger: MagicMock) -> None:
        config = {"debug": {"enabled": True, "packets": [11, 193]}}
        handler = DebugHandler.from_config(mock_logger, config)
        assert handler.enabled
        assert handler.should_log(11)
        assert handler.should_log(193)
        assert not handler.should_log(42)
        assert handler.log_pre_packet_transform
        assert not handler.log_post_packet_transform

    def test_with_post_transform(self, mock_logger: MagicMock) -> None:
        config = {"debug": {"enabled": True, "log_post_transform": True}}
        handler = DebugHandler.from_config(mock_logger, config)
        assert handler.log_post_packet_transform

    def test_empty_config_disables(self, mock_logger: MagicMock) -> None:
        handler = DebugHandler.from_config(mock_logger, {})
        assert not handler.enabled


class TestPacketLogFormat:
    def test_log_packet_format(self, mock_logger: MagicMock) -> None:
        handler = DebugHandler(mock_logger, enabled=True)
        handler.log_packet("PRE ", "1.2.3.4:1234", "SERVERBOUND", 11, 944, 256)

        msg = mock_logger.debug.call_args[0][0]
        assert "PRE :" in msg
        assert "SERVERBOUND" in msg
        assert "START_GAME(11)" in msg
        assert "0x0B" in msg
        assert "[944]" in msg
        assert "256b" in msg


class TestPacketLabel:
    def test_known_packet_id(self) -> None:
        label = packet_label(11)
        assert "START_GAME(11)" in label
        assert "(0x0B)" in label

    def test_single_digit_hex_padded(self) -> None:
        assert "(0x05)" in packet_label(5)

    def test_two_digit_hex(self) -> None:
        assert "(0xC1)" in packet_label(193)  # RequestNetworkSettings

    def test_unknown_packet_id(self) -> None:
        label = packet_label(9999)
        assert "9999" in label
        assert "(0x270F)" in label
