"""LocatorBarPacket (341) -- v944 server to v975 client.

In v975 each Waypoint dropped Optional[uint32] TextureId in favour of
Optional[string] TexturePath + Optional[Vec2] IconSize. The 944 server still
emits a numeric texture id; drop it and emit nullopt for both new fields so
the client falls back to its default icon.
"""

from endstone_endweave.codec import (
    BOOL,
    INT_LE,
    UINT_LE,
    UUID,
    UVAR_INT,
    VAR_INT,
    VAR_INT64,
    VEC3,
    PacketWrapper,
)


def rewrite_locator_bar(wrapper: PacketWrapper) -> None:
    """Drop each Waypoint's TextureId and emit nullopt TexturePath + IconSize.

    Args:
        wrapper: Packet wrapper for LocatorBarPacket.
    """
    count = wrapper.passthrough(UVAR_INT)  # Waypoints list size
    for _ in range(count):
        wrapper.passthrough(UUID)  # GroupHandle (mce::UUID = 16 bytes)
        wrapper.passthrough(UINT_LE)  # ServerWaypoint::Payload.UpdateFlag
        if wrapper.passthrough(BOOL):  # Optional IsVisible
            wrapper.passthrough(BOOL)
        if wrapper.passthrough(BOOL):  # Optional WorldPosition
            wrapper.passthrough(VEC3)  # Position
            wrapper.passthrough(VAR_INT)  # DimensionType
        # Optional[uint32] TextureId  ->  Optional[string] TexturePath + Optional[Vec2] IconSize
        if wrapper.read(BOOL):
            wrapper.read(UINT_LE)  # discard TextureId
        wrapper.write(BOOL, False)  # TexturePath: nullopt
        wrapper.write(BOOL, False)  # IconSize: nullopt
        if wrapper.passthrough(BOOL):  # Optional Color (mce::Color = int32)
            wrapper.passthrough(INT_LE)
        if wrapper.passthrough(BOOL):  # Optional ClientPositionAuthority
            wrapper.passthrough(BOOL)
        if wrapper.passthrough(BOOL):  # Optional ActorUniqueID (varint64)
            wrapper.passthrough(VAR_INT64)
        wrapper.passthrough(UVAR_INT)  # ActionFlag (ServerWaypointGroup::Action)
