"""CraftingDataPacket (52) -- v944 server to v975 client.

v975 removed CraftingDataEntryType::FurnaceRecipe and FurnaceAuxRecipe.
Furnaces did not go away on the wire -- they were merged into the regular
SHAPELESS_RECIPE shape, with the existing ``tag`` field
(``furnace`` / ``smoker`` / ``blast_furnace``) telling the client which
block-entity uses each recipe. Convert every v944 furnace entry into a
shapeless entry so v975 clients keep seeing furnace recipes.

This mirrors CloudburstMC/Nukkit ``CraftingDataPacket.java`` (1.26.20 update).
"""

import uuid

from endstone_endweave.codec import (
    CRAFTING_DATA_ENTRY,
    ArrayType,
    CraftingDataEntryType,
    MceUUID,
    PacketWrapper,
)
from endstone_endweave.codec.types.crafting import (
    CraftingDataEntry,
    ItemDescriptor,
    ItemDescriptorKind,
    RecipeIngredient,
    RecipeUnlockingRequirement,
    ShapelessRecipe,
    UnlockingContext,
)
from endstone_endweave.codec.types.item import ItemInstance


def _furnace_recipe_id(tag: str, input_id: int, input_aux: int, result_net_id: int) -> str:
    aux_part = "" if input_aux == 0x7FFF else f"_{input_aux}"
    return f"endweave:{tag}_{input_id}{aux_part}_to_{result_net_id}"


def _furnace_to_shapeless(entry: CraftingDataEntry, *, item_aux: int, net_id: int) -> CraftingDataEntry:
    """Repackage a v944 furnace entry as a v975 shapeless entry."""
    recipe_id = _furnace_recipe_id(
        tag=entry.tag,
        input_id=entry.item_data,
        input_aux=item_aux,
        result_net_id=entry.item_result.network_id,
    )
    synth = uuid.uuid5(uuid.NAMESPACE_DNS, recipe_id)
    ingredient = RecipeIngredient(
        descriptor=ItemDescriptor(
            kind=ItemDescriptorKind.DEFAULT,
            item_id=entry.item_data,
            aux_value=item_aux,
        ),
        count=1,
    )
    recipe = ShapelessRecipe(
        recipe_id=recipe_id,
        uuid=MceUUID(msb=(synth.int >> 64) & 0xFFFFFFFFFFFFFFFF, lsb=synth.int & 0xFFFFFFFFFFFFFFFF),
        priority=0,
        recipe_net_id=net_id,
        ingredients=[ingredient],
        results=[entry.item_result],
        tag=entry.tag,
        requirement=RecipeUnlockingRequirement(
            context=UnlockingContext.ALWAYS_UNLOCKED,
            ingredients=[],
        ),
    )
    return CraftingDataEntry(
        recipe=recipe,
        item_data=0,
        item_aux=0,
        tag="",
        item_result=ItemInstance(),
        type=CraftingDataEntryType.SHAPELESS_RECIPE,
    )


def rewrite_crafting_data(wrapper: PacketWrapper) -> None:
    """Convert FurnaceRecipe / FurnaceAuxRecipe entries to ShapelessRecipe.

    Args:
        wrapper: Packet wrapper for CraftingDataPacket.
    """
    entries = wrapper.read(ArrayType(CRAFTING_DATA_ENTRY))
    existing_max = max(
        (e.recipe.recipe_net_id for e in entries if e.recipe is not None),
        default=0,
    )
    converted: list[CraftingDataEntry] = []
    next_synth_id = existing_max + 1
    for entry in entries:
        if entry.type is CraftingDataEntryType.FURNACE_RECIPE:
            converted.append(_furnace_to_shapeless(entry, item_aux=0x7FFF, net_id=next_synth_id))
            next_synth_id += 1
        elif entry.type is CraftingDataEntryType.FURNACE_AUX_RECIPE:
            converted.append(_furnace_to_shapeless(entry, item_aux=entry.item_aux, net_id=next_synth_id))
            next_synth_id += 1
        else:
            converted.append(entry)
    wrapper.write(ArrayType(CRAFTING_DATA_ENTRY), converted)
    wrapper.passthrough_all()
