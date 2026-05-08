"""Fixtures for tests that exercise the routing pipeline end-to-end."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable
from unittest.mock import MagicMock

import pytest

from endstone_endweave.connection import ConnectionManager
from endstone_endweave.pipeline import ProtocolPipeline
from endstone_endweave.protocol.base import create_base_protocol
from endstone_endweave.protocol.manager import ProtocolManager


@dataclass
class PipelineHarness:
    """Bundle of pipeline collaborators that tests typically need to assert on."""

    pipeline: ProtocolPipeline
    connections: ConnectionManager
    manager: ProtocolManager
    logger: MagicMock


@pytest.fixture
def make_pipeline(mock_logger: MagicMock) -> Callable[..., PipelineHarness]:
    """Construct a wired pipeline + connections + manager with the base protocol registered."""

    def _make(server_protocol: int = 924) -> PipelineHarness:
        connections = ConnectionManager(server_protocol=server_protocol, logger=mock_logger)
        manager = ProtocolManager()
        manager.register_base(create_base_protocol(server_protocol))
        pipeline = ProtocolPipeline(manager, connections, mock_logger)
        return PipelineHarness(pipeline=pipeline, connections=connections, manager=manager, logger=mock_logger)

    return _make
