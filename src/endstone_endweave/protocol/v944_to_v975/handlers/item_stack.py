from endstone_endweave.codec import (
    BOOL,
    BYTE,
    ITEM_INSTANCE,
    ITEM_INSTANCE_V975,
    UINT_LE,
    UVAR_INT,
    UVAR_INT64,
    PacketWrapper,
)
from endstone_endweave.protocol.direction import Direction


def rewrite_mob_equipment(wrapper: PacketWrapper, direction: Direction) -> None:
    """MobEquipmentPacket: bridge v944 byte slot fields and v975 uvarint32 fields.

    Clientbound (v944 -> v975): byte slots widened to uvarint32, item upgraded.
    Serverbound (v975 -> v944): uvarint32 slots truncated back to byte.

    Args:
        wrapper: Packet wrapper for MobEquipmentPacket.
        direction: Whether the packet is clientbound or serverbound.
    """
    wrapper.passthrough(UVAR_INT64)  # Target Runtime ID
    if direction is Direction.CLIENTBOUND:
        wrapper.map(ITEM_INSTANCE, ITEM_INSTANCE_V975)  # Item
        wrapper.map(BYTE, UVAR_INT)  # Slot
        wrapper.map(BYTE, UVAR_INT)  # Selected Slot
        wrapper.map(BYTE, UVAR_INT)  # Container ID
    else:
        wrapper.map(ITEM_INSTANCE_V975, ITEM_INSTANCE)  # Item
        wrapper.map(UVAR_INT, BYTE)  # Slot
        wrapper.map(UVAR_INT, BYTE)  # Selected Slot
        wrapper.map(UVAR_INT, BYTE)  # Container ID


def rewrite_inventory_slot(wrapper: PacketWrapper) -> None:
    """InventorySlotPacket (50): rewrite v944 layout into v975 layout."""
    wrapper.passthrough(UVAR_INT)  # Container Id
    wrapper.passthrough(UVAR_INT)  # Slot

    # v944 always sends FullContainerName flat; v975 wraps it in optional bools.
    container_name = wrapper.read(BYTE)
    dynamic_id = wrapper.read(UVAR_INT)
    wrapper.write(BOOL, True)  # has Full Container Name
    wrapper.write(BYTE, container_name)
    wrapper.write(BOOL, True)  # has Dynamic ID
    wrapper.write(UINT_LE, dynamic_id)

    # v944 always sends Storage Item (with air shortcut); v975 makes it optional.
    storage = wrapper.read(ITEM_INSTANCE)
    if storage.network_id == 0:
        wrapper.write(BOOL, False)
    else:
        wrapper.write(BOOL, True)
        wrapper.write(ITEM_INSTANCE_V975, storage)

    # Item is always present in both versions.
    wrapper.map(ITEM_INSTANCE, ITEM_INSTANCE_V975)
