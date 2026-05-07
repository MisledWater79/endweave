"""Text packet handlers for v924 to v898."""

from endstone_endweave.codec import BOOL, BYTE, STRING, PacketWrapper, TextPacketBodyType, TextPacketType, enum_to_label
from endstone_endweave.protocol.direction import Direction

_MESSAGE_ONLY_TYPES = (
    TextPacketType.RAW,
    TextPacketType.TIP,
    TextPacketType.SYSTEM_MESSAGE,
    TextPacketType.TEXT_OBJECT_WHISPER,
    TextPacketType.TEXT_OBJECT_ANNOUNCEMENT,
    TextPacketType.TEXT_OBJECT,
)
_AUTHOR_AND_MESSAGE_TYPES = (
    TextPacketType.CHAT,
    TextPacketType.WHISPER,
    TextPacketType.ANNOUNCEMENT,
)
_MESSAGE_AND_PARAMS_TYPES = (
    TextPacketType.TRANSLATE,
    TextPacketType.POPUP,
    TextPacketType.JUKEBOX_POPUP,
)

_labels = enum_to_label(TextPacketType)


def _build_label_group(types: tuple[TextPacketType, ...]) -> dict[int, tuple[str, ...]]:
    labels = tuple(_labels[t] for t in types)
    return {t: labels for t in types}


_TEXT_MESSAGE_ONLY = _build_label_group(_MESSAGE_ONLY_TYPES)
_TEXT_AUTHOR_AND_MESSAGE = _build_label_group(_AUTHOR_AND_MESSAGE_TYPES)
_TEXT_MESSAGE_AND_PARAMS = _build_label_group(_MESSAGE_AND_PARAMS_TYPES)


def rewrite_text(wrapper: PacketWrapper, direction: Direction) -> None:
    """Bridge the v924 Text format and the v898 Text format.

    Clientbound (v924 -> v898): inject the per-type label strings ahead of the type byte.
    Serverbound (v898 -> v924): strip the per-type label strings before the type byte.

    Args:
        wrapper: Packet wrapper for Text.
        direction: Whether the packet is clientbound or serverbound.
    """
    wrapper.passthrough(BOOL)  # Localize?
    kind = wrapper.read(BYTE)
    wrapper.write(BYTE, kind)

    if direction is Direction.CLIENTBOUND:
        if kind == TextPacketBodyType.MESSAGE_ONLY:
            text_type = wrapper.read(BYTE)
            for label in _TEXT_MESSAGE_ONLY[text_type]:
                wrapper.write(STRING, label)
            wrapper.write(BYTE, text_type)
        elif kind == TextPacketBodyType.AUTHOR_AND_MESSAGE:
            text_type = wrapper.read(BYTE)
            for label in _TEXT_AUTHOR_AND_MESSAGE[text_type]:
                wrapper.write(STRING, label)
            wrapper.write(BYTE, text_type)
        elif kind == TextPacketBodyType.MESSAGE_AND_PARAMS:
            text_type = wrapper.read(BYTE)
            for label in _TEXT_MESSAGE_AND_PARAMS[text_type]:
                wrapper.write(STRING, label)
            wrapper.write(BYTE, text_type)
        else:
            raise ValueError(f"Unknown text kind: {kind}")
    else:
        if kind == TextPacketBodyType.MESSAGE_ONLY:
            for _ in range(6):
                wrapper.read(STRING)
            wrapper.passthrough(BYTE)
        elif kind == TextPacketBodyType.AUTHOR_AND_MESSAGE:
            for _ in range(3):
                wrapper.read(STRING)
            wrapper.passthrough(BYTE)
        elif kind == TextPacketBodyType.MESSAGE_AND_PARAMS:
            for _ in range(3):
                wrapper.read(STRING)
            wrapper.passthrough(BYTE)
        else:
            raise ValueError(f"Unknown text kind: {kind}")
