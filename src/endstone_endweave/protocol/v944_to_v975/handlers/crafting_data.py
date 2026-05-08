"""CraftingDataPacket (52) -- v944 server to v975 client.

v975 removed CraftingDataEntryType::FurnaceRecipe and FurnaceAuxRecipe.
Furnaces did not go away on the wire -- they were merged into the regular
SHAPELESS_RECIPE shape, with the existing ``tag`` field
(``furnace`` / ``smoker`` / ``blast_furnace``) telling the client which
block-entity uses each recipe. Convert every v944 furnace entry into a
shapeless entry so v975 clients keep seeing furnace recipes.

This mirrors CloudburstMC/Nukkit ``CraftingDataPacket.java`` (1.26.20 update).
"""

from endstone_endweave.codec import (
    CRAFTING_DATA_ENTRY,
    ArrayType,
    CraftingDataEntryType,
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

# Bedrock convention: aux = 0x7FFF means "match any meta value".
_ANY_AUX = 0x7FFF
# Synthetic net IDs start above any plausible server-assigned value so they
# never collide with real recipes already in the packet.
_SYNTHETIC_NET_ID_BASE = 0x7FFF_0000


def _furnace_to_shapeless(entry: CraftingDataEntry, *, item_aux: int, net_id: int) -> CraftingDataEntry:
    """Repackage a v944 furnace entry as a v975 shapeless entry."""
    ingredient = RecipeIngredient(
        descriptor=ItemDescriptor(
            kind=ItemDescriptorKind.DEFAULT,
            item_id=entry.item_data,
            aux_value=item_aux,
        ),
        count=1,
    )
    recipe = ShapelessRecipe(
        recipe_id=f"endweave:furnace_synth_{net_id}",
        uuid=b"\x00" * 16,
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
    entries = wrapper.read(ArrayType(CRAFTING_DATA_ENTRY))  # Crafting Entries
    converted: list[CraftingDataEntry] = []
    next_synth_id = _SYNTHETIC_NET_ID_BASE
    for entry in entries:
        if entry.type is CraftingDataEntryType.FURNACE_RECIPE:
            converted.append(_furnace_to_shapeless(entry, item_aux=_ANY_AUX, net_id=next_synth_id))
            next_synth_id += 1
        elif entry.type is CraftingDataEntryType.FURNACE_AUX_RECIPE:
            converted.append(_furnace_to_shapeless(entry, item_aux=entry.item_aux, net_id=next_synth_id))
            next_synth_id += 1
        else:
            converted.append(entry)
    wrapper.write(ArrayType(CRAFTING_DATA_ENTRY), converted)
    wrapper.passthrough_all()
