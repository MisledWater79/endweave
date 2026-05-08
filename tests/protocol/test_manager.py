"""ProtocolManager registration and BFS chain resolution."""

from __future__ import annotations

from endstone_endweave.protocol import Protocol
from endstone_endweave.protocol.manager import ProtocolManager


class TestProtocolManager:
    def test_register_and_get(self) -> None:
        mgr = ProtocolManager()
        protocol = Protocol(server_protocol=924, client_protocol=944)
        mgr.register(protocol)
        assert mgr.get(924, 944) is protocol

    def test_get_missing_returns_none(self) -> None:
        assert ProtocolManager().get(924, 999) is None


class TestChainResolution:
    """BFS over registered protocols to translate between non-adjacent versions."""

    def test_two_step_chain(self) -> None:
        mgr = ProtocolManager()
        p_ab = Protocol(server_protocol=100, client_protocol=200, name="a_to_b")
        p_bc = Protocol(server_protocol=200, client_protocol=300, name="b_to_c")
        mgr.register(p_ab)
        mgr.register(p_bc)

        chain = mgr.get_path(100, 300)
        assert chain is not None
        assert len(chain) == 2
        # client 300 -> server 200, then 200 -> 100
        assert chain[0] is p_bc
        assert chain[1] is p_ab
