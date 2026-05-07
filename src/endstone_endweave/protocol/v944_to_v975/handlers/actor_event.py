"""ActorEventPacket (27) -- v944 server <-> v975 client.

v975 appended an optional Fire At Position (Vec3) field at the end.
"""

from endstone_endweave.codec import BOOL, BYTE, UVAR_INT64, VAR_INT, VEC3, PacketWrapper
from endstone_endweave.protocol.direction import Direction


def rewrite_actor_event(wrapper: PacketWrapper, direction: Direction) -> None:
    """Bridge the v975 Fire At Position field across versions.

    Clientbound (v944 -> v975): appends the missing optional field.
    Serverbound (v975 -> v944): reads and discards it.

    Args:
        wrapper: Packet wrapper for ActorEventPacket.
        direction: Whether the packet is clientbound or serverbound.
    """
    if direction is Direction.CLIENTBOUND:
        wrapper.passthrough_all()  # Target Runtime ID, Event ID, Data
        wrapper.write(BOOL, False)  # Fire At Position (not present)
        return
    else:
        wrapper.passthrough(UVAR_INT64)  # Target Runtime ID
        wrapper.passthrough(BYTE)  # Event ID
        wrapper.passthrough(VAR_INT)  # Data
        has_fire_at_position = wrapper.read(BOOL)
        if has_fire_at_position:
            wrapper.read(VEC3)
