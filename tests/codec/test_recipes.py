"""Crafting recipe wire formats: assume_symmetry, RecipeUnlockingRequirement, smithing."""

from __future__ import annotations

from endstone_endweave.codec import (
    SHAPED_CHEMISTRY_RECIPE,
    SHAPED_RECIPE,
    SHAPELESS_CHEMISTRY_RECIPE,
    SHAPELESS_RECIPE,
    SMITHING_TRANSFORM_RECIPE,
    USER_DATA_SHAPELESS_RECIPE,
    PacketWrapper,
)
from endstone_endweave.codec.writer import PacketWriter


def _shapeless_bytes(*, requirement_byte: int, requirement_ingredients: int = 0) -> bytes:
    w = PacketWriter()
    w.write_string("recipe:test")
    w.write_uvarint(0)  # ingredients
    w.write_uvarint(0)  # results
    w.write_bytes(b"\x01" * 16)  # uuid
    w.write_string("crafting_table")
    w.write_varint(50)  # priority
    w.write_byte(requirement_byte)
    if requirement_byte == 0:
        w.write_uvarint(requirement_ingredients)
    w.write_uvarint(123)  # net id
    return w.to_bytes()


def _shaped_bytes(*, assume_symmetry: bool, requirement_byte: int) -> bytes:
    w = PacketWriter()
    w.write_string("recipe:shaped")
    w.write_varint(2)  # width
    w.write_varint(2)  # height
    for _ in range(4):
        # kind=DEFAULT, item_id=0 (so no aux), count=1
        w.write_byte(1)
        w.write_short_le(0)
        w.write_varint(1)
    w.write_uvarint(0)  # results
    w.write_bytes(b"\x02" * 16)  # uuid
    w.write_string("crafting_table")
    w.write_varint(0)  # priority
    w.write_bool(assume_symmetry)
    w.write_byte(requirement_byte)
    if requirement_byte == 0:
        w.write_uvarint(0)
    w.write_uvarint(7)  # net id
    return w.to_bytes()


class TestShapelessRecipe:
    def test_requirement_none_empty(self) -> None:
        payload = _shapeless_bytes(requirement_byte=0)
        wrapper = PacketWrapper(payload)
        wrapper.passthrough(SHAPELESS_RECIPE)
        assert wrapper.to_bytes() == payload

    def test_requirement_always_unlocked(self) -> None:
        payload = _shapeless_bytes(requirement_byte=1)
        wrapper = PacketWrapper(payload)
        wrapper.passthrough(SHAPELESS_RECIPE)
        assert wrapper.to_bytes() == payload


class TestShapedRecipe:
    def test_assume_symmetry_and_requirement(self) -> None:
        payload = _shaped_bytes(assume_symmetry=True, requirement_byte=2)
        wrapper = PacketWrapper(payload)
        wrapper.passthrough(SHAPED_RECIPE)
        assert wrapper.to_bytes() == payload


class TestChemistryRecipes:
    """Chemistry variants do NOT serialize RecipeUnlockingRequirement (v944)."""

    def test_shaped_chemistry_has_assume_symmetry_no_requirement(self) -> None:
        w = PacketWriter()
        w.write_string("recipe:chem")
        w.write_varint(1)
        w.write_varint(1)
        w.write_byte(1)
        w.write_short_le(0)
        w.write_varint(1)
        w.write_uvarint(0)
        w.write_bytes(b"\x03" * 16)
        w.write_string("brewing_stand")
        w.write_varint(0)
        w.write_bool(False)
        w.write_uvarint(99)
        payload = w.to_bytes()

        wrapper = PacketWrapper(payload)
        wrapper.passthrough(SHAPED_CHEMISTRY_RECIPE)
        assert wrapper.to_bytes() == payload

    def test_shapeless_chemistry_no_requirement(self) -> None:
        w = PacketWriter()
        w.write_string("recipe:chem_shapeless")
        w.write_uvarint(0)  # ingredients
        w.write_uvarint(0)  # results
        w.write_bytes(b"\x04" * 16)
        w.write_string("brewing_stand")
        w.write_varint(0)
        w.write_uvarint(99)
        payload = w.to_bytes()

        wrapper = PacketWrapper(payload)
        wrapper.passthrough(SHAPELESS_CHEMISTRY_RECIPE)
        assert wrapper.to_bytes() == payload


class TestUserDataShapelessRecipe:
    def test_has_requirement(self) -> None:
        payload = _shapeless_bytes(requirement_byte=0, requirement_ingredients=0)
        wrapper = PacketWrapper(payload)
        wrapper.passthrough(USER_DATA_SHAPELESS_RECIPE)
        assert wrapper.to_bytes() == payload


class TestSmithingTransformRecipe:
    def test_result_is_network_item_instance_descriptor(self) -> None:
        """Recipe results use NetworkItemInstanceDescriptor (no HasNetID byte)."""
        w = PacketWriter()
        w.write_string("recipe:smith")
        # 3 ingredients (template, base, addition), each kind=DEFAULT, item_id=0, count=1
        for _ in range(3):
            w.write_byte(1)
            w.write_short_le(0)
            w.write_varint(1)
        # Result item (NetworkItemInstanceDescriptor: NO has_net_id byte)
        w.write_varint(649)  # network_id
        w.write_ushort_le(1)  # count
        w.write_uvarint(0)  # aux
        w.write_varint(0)  # block_runtime_id
        w.write_uvarint(10)  # extra_len
        w.write_bytes(b"\x00" * 10)  # extra_data
        w.write_string("smithing_table")  # tag
        w.write_uvarint(1112)  # net id
        payload = w.to_bytes()

        wrapper = PacketWrapper(payload)
        wrapper.passthrough(SMITHING_TRANSFORM_RECIPE)
        assert wrapper.to_bytes() == payload
