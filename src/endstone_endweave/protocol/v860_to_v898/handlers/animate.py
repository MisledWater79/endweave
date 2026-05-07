"""Handler for AnimatePacket -- v860 server to v898 client.

v860 uses varint for Action and has a conditional Rowing Time float
when Action & 0x80. v898 uses uint8 for Action and optional SwingSource.
"""

from endstone_endweave.codec import (
    BYTE,
    FLOAT_LE,
    STRING,
    UVAR_INT64,
    VAR_INT,
    OptionalType,
    PacketWrapper,
)
from endstone_endweave.protocol.direction import Direction

_ROWING_FLAG = 0x80


def rewrite_animate(wrapper: PacketWrapper, direction: Direction) -> None:
    """Bridge AnimatePacket between v860 and v898 wire formats.

    Clientbound (v860 -> v898): Action varint -> uint8, drop Rowing Time, append empty SwingSource.
    Serverbound (v898 -> v860): Action uint8 -> varint, strip SwingSource.

    Args:
        wrapper: Packet wrapper for Animate.
        direction: Whether the packet is clientbound or serverbound.
    """
    if direction is Direction.CLIENTBOUND:
        action = wrapper.read(VAR_INT)  # Action (varint in v860)
        wrapper.write(BYTE, action)  # Action (uint8 in v898)
        wrapper.passthrough(UVAR_INT64)  # Target Runtime ID
        wrapper.passthrough(FLOAT_LE)  # Data
        if action & _ROWING_FLAG:
            wrapper.read(FLOAT_LE)  # Rowing Time (strip for v898)
        wrapper.write(OptionalType(STRING), None)  # Swing Source
    else:
        action = wrapper.read(BYTE)  # Action (uint8 in v898)
        wrapper.write(VAR_INT, action)  # Action (varint in v860)
        wrapper.passthrough(UVAR_INT64)  # Target Runtime ID
        wrapper.passthrough(FLOAT_LE)  # Data
        wrapper.read(OptionalType(STRING))  # Swing Source (strip for v860)
