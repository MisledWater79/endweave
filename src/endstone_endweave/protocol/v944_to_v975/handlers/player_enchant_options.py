"""PlayerEnchantOptionsPacket (146) -- v944 server to v975 client.

ItemEnchantOption.Cost width changed from unsigned varint (v944) to uint8 (v975).
Read varuint per option, clamp to 0-255, and write a single byte.
"""

from endstone_endweave.codec import BYTE, INT_LE, STRING, UVAR_INT, PacketWrapper


def rewrite_player_enchant_options(wrapper: PacketWrapper) -> None:
    """Re-encode each ItemEnchantOption.Cost as uint8 instead of varuint.

    Args:
        wrapper: Packet wrapper for PlayerEnchantOptionsPacket.
    """
    count = wrapper.passthrough(UVAR_INT)  # Options list size
    for _ in range(count):
        cost = wrapper.read(UVAR_INT)  # Cost (v944: varuint)
        wrapper.write(BYTE, min(cost, 0xFF))  # Cost (v975: uint8)
        wrapper.passthrough(INT_LE)  # ItemEnchants.Slot
        for _ in range(3):  # Three enchantment instance slices
            inner = wrapper.passthrough(UVAR_INT)
            for _ in range(inner):
                wrapper.passthrough(BYTE)  # Enchant Type
                wrapper.passthrough(BYTE)  # Enchant Level
        wrapper.passthrough(STRING)  # Enchant Name
        wrapper.passthrough(UVAR_INT)  # Enchant Net Id (RecipeNetId raw, varuint32)
