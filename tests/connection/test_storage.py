"""Per-connection state storage and ConnectionManager lifecycle."""

from __future__ import annotations

from typing import Callable
from unittest.mock import MagicMock

from endstone_endweave.connection import ConnectionManager, UserConnection


class TestUserConnectionStorage:
    def test_put_and_get(self, make_connection: Callable[..., UserConnection]) -> None:
        conn = make_connection()

        class MyState:
            value = 42

        state = MyState()
        conn.put(state)
        assert conn.get(MyState) is state
        assert conn.get(MyState).value == 42

    def test_has(self, make_connection: Callable[..., UserConnection]) -> None:
        conn = make_connection()

        class Tracker:
            pass

        assert not conn.has(Tracker)
        conn.put(Tracker())
        assert conn.has(Tracker)

    def test_remove(self, make_connection: Callable[..., UserConnection]) -> None:
        conn = make_connection()

        class Tracker:
            pass

        conn.put(Tracker())
        conn.remove(Tracker)
        assert not conn.has(Tracker)
        assert conn.get(Tracker) is None

    def test_remove_nonexistent_is_noop(self, make_connection: Callable[..., UserConnection]) -> None:
        conn = make_connection()

        class Tracker:
            pass

        conn.remove(Tracker)  # must not raise

    def test_clear_storage(self, make_connection: Callable[..., UserConnection]) -> None:
        conn = make_connection()

        class A:
            pass

        class B:
            pass

        conn.put(A())
        conn.put(B())
        conn.clear_storage()
        assert not conn.has(A)
        assert not conn.has(B)

    def test_get_returns_none_for_missing(self, make_connection: Callable[..., UserConnection]) -> None:
        conn = make_connection()

        class Missing:
            pass

        assert conn.get(Missing) is None

    def test_put_overwrites_same_type(self, make_connection: Callable[..., UserConnection]) -> None:
        conn = make_connection()

        class Counter:
            def __init__(self, n: int) -> None:
                self.n = n

        conn.put(Counter(1))
        conn.put(Counter(2))
        assert conn.get(Counter).n == 2


class TestNeedsTranslation:
    def test_false_when_matching(self, make_connection: Callable[..., UserConnection]) -> None:
        conn = make_connection(client_protocol=924, server_protocol=924)
        assert not conn.needs_translation

    def test_true_when_different(self, make_connection: Callable[..., UserConnection]) -> None:
        conn = make_connection(client_protocol=944, server_protocol=924)
        assert conn.needs_translation

    def test_false_when_undetected(self, make_connection: Callable[..., UserConnection]) -> None:
        conn = make_connection()
        assert not conn.needs_translation


class TestConnectionManager:
    def test_get_or_create_returns_same_connection(self) -> None:
        mgr = ConnectionManager()
        c1 = mgr.get_or_create("1.2.3.4:1234")
        c2 = mgr.get_or_create("1.2.3.4:1234")
        assert c1 is c2

    def test_get_returns_none_for_missing(self) -> None:
        assert ConnectionManager().get("nope") is None

    def test_remove_by_address(self) -> None:
        mgr = ConnectionManager()
        mgr.get_or_create("1.2.3.4:1234")
        mgr.remove_by_address("1.2.3.4:1234")
        assert mgr.get("1.2.3.4:1234") is None

    def test_remove_by_player(self) -> None:
        mgr = ConnectionManager()
        mgr.get_or_create("1.2.3.4:1234")
        player = MagicMock()
        player.address = "1.2.3.4:1234"
        mgr.remove_by_player(player)
        assert mgr.get("1.2.3.4:1234") is None

    def test_remove_by_address_clears_storage(self, mock_logger: MagicMock) -> None:
        mgr = ConnectionManager(server_protocol=924, logger=mock_logger)
        conn = mgr.get_or_create("1.2.3.4:1234")

        class Tracker:
            pass

        conn.put(Tracker())
        mgr.remove_by_address("1.2.3.4:1234")
        # Storage on the still-held reference should have been cleared.
        assert not conn.has(Tracker)
