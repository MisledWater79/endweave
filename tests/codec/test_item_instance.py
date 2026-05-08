"""NetworkItemInstanceDescriptor (ITEM_INSTANCE) wire format."""

from __future__ import annotations

from endstone_endweave.codec import PacketReader
from endstone_endweave.codec.types import ITEM_INSTANCE, ItemInstance
from endstone_endweave.codec.writer import PacketWriter


class TestNetworkItemInstanceDescriptor:
    def test_air_roundtrip(self) -> None:
        item = ItemInstance(network_id=0)
        w = PacketWriter()
        ITEM_INSTANCE.write(w, item)
        r = PacketReader(w.to_bytes())
        result = ITEM_INSTANCE.read(r)
        assert result.network_id == 0
        assert not r.has_remaining

    def test_full_roundtrip(self) -> None:
        item = ItemInstance(
            network_id=42,
            count=64,
            aux_value=7,
            has_net_id=True,
            stack_net_id=99,
            block_runtime_id=123,
            user_data=b"\xaa\xbb\xcc",
        )
        w = PacketWriter()
        ITEM_INSTANCE.write(w, item)
        r = PacketReader(w.to_bytes())
        result = ITEM_INSTANCE.read(r)
        assert result == item
        assert not r.has_remaining

    def test_roundtrip_no_net_id(self) -> None:
        item = ItemInstance(
            network_id=10,
            count=1,
            aux_value=0,
            has_net_id=False,
            stack_net_id=0,
            block_runtime_id=5,
            user_data=b"",
        )
        w = PacketWriter()
        ITEM_INSTANCE.write(w, item)
        r = PacketReader(w.to_bytes())
        result = ITEM_INSTANCE.read(r)
        assert result == item
        assert not r.has_remaining

    def test_byte_identical_passthrough(self) -> None:
        """Write -> bytes -> read -> write again must produce identical bytes."""
        item = ItemInstance(
            network_id=42,
            count=64,
            aux_value=7,
            has_net_id=True,
            stack_net_id=99,
            block_runtime_id=123,
            user_data=b"\x01\x02\x03\x04",
        )
        w1 = PacketWriter()
        ITEM_INSTANCE.write(w1, item)
        original_bytes = w1.to_bytes()

        roundtripped = ITEM_INSTANCE.read(PacketReader(original_bytes))
        w2 = PacketWriter()
        ITEM_INSTANCE.write(w2, roundtripped)
        assert w2.to_bytes() == original_bytes
