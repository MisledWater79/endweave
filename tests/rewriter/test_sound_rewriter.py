"""SoundRewriter handler integration: LevelSoundEvent + ActorData remapping."""

from __future__ import annotations

import pytest

from endstone_endweave.codec import (
    ACTOR_DATA_LIST,
    PacketWrapper,
)
from endstone_endweave.codec.reader import PacketReader
from endstone_endweave.codec.writer import PacketWriter
from endstone_endweave.protocol.mappings.v924_v944 import MAPPINGS as M_924_944
from endstone_endweave.rewriter import SoundRewriter
from tests.builders import varint_bytes, write_actor_data_list

REMAP_V924_TO_V944 = M_924_944.sound.shift_up


@pytest.fixture
def rewriter() -> SoundRewriter:
    return SoundRewriter(
        sound_remap=REMAP_V924_TO_V944,
        actor_data_int_remappers={126: REMAP_V924_TO_V944},
    )


class TestLevelSoundEvent:
    def test_event_id_at_threshold_is_remapped(self, rewriter: SoundRewriter) -> None:
        w = PacketWriter()
        w.write_uvarint(597)  # at threshold
        w.write_bytes(b"\xaa\xbb")  # trailing (Position, ActorType, etc.)

        wrapper = PacketWrapper(w.to_bytes())
        rewriter.rewrite_level_sound_event(wrapper)

        r = PacketReader(wrapper.to_bytes())
        assert r.read_uvarint() == 599
        assert r.read_remaining() == b"\xaa\xbb"

    def test_event_id_below_threshold_unchanged(self, rewriter: SoundRewriter) -> None:
        w = PacketWriter()
        w.write_uvarint(100)
        w.write_bytes(b"\xcc")

        wrapper = PacketWrapper(w.to_bytes())
        rewriter.rewrite_level_sound_event(wrapper)

        r = PacketReader(wrapper.to_bytes())
        assert r.read_uvarint() == 100
        assert r.read_remaining() == b"\xcc"


class TestSetActorData:
    def test_heartbeat_int_value_is_remapped(self, rewriter: SoundRewriter) -> None:
        """ActorData key 126 (heartbeat) with int type (2) gets remapped."""
        w = PacketWriter()
        w.write_uvarint64(1)  # Target Runtime ID
        write_actor_data_list(w, [(126, 2, varint_bytes(597))])
        w.write_bytes(b"\xdd")  # trailing

        wrapper = PacketWrapper(w.to_bytes())
        rewriter.rewrite_set_actor_data(wrapper)

        r = PacketReader(wrapper.to_bytes())
        assert r.read_uvarint64() == 1
        entries = ACTOR_DATA_LIST.read(r)
        assert len(entries) == 1
        assert entries[0].key == 126
        assert entries[0].type_id == 2
        assert entries[0].value == 599  # remapped from 597
        assert r.read_remaining() == b"\xdd"

    def test_non_matching_key_unchanged(self, rewriter: SoundRewriter) -> None:
        w = PacketWriter()
        w.write_uvarint64(1)
        write_actor_data_list(w, [(99, 2, varint_bytes(597))])
        w.write_bytes(b"\xee")

        wrapper = PacketWrapper(w.to_bytes())
        rewriter.rewrite_set_actor_data(wrapper)

        r = PacketReader(wrapper.to_bytes())
        r.read_uvarint64()
        entries = ACTOR_DATA_LIST.read(r)
        assert len(entries) == 1
        assert entries[0].value == 597
