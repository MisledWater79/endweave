"""ClientboundAttributeLayerSyncPacket (345) -- v944 server to v975 client.

In v975 AttributeLayerSettings.Weight switched from a tagged union (uvarint32
type tag selecting float or string) to a plain float. Map each Settings block
from the v944 type to the v975 type; string-weighted v944 settings fall back
to a default float since v975 has no encoding for them.
"""

from endstone_endweave.codec import (
    ATTRIBUTE_LAYER_SETTINGS_V944,
    ATTRIBUTE_LAYER_SETTINGS_V975,
    ENVIRONMENT_ATTRIBUTE_DATA,
    STRING,
    UVAR_INT,
    VAR_INT,
    AttributeLayerSyncPayloadType,
    PacketWrapper,
)


def rewrite_clientbound_attribute_layer_sync(wrapper: PacketWrapper) -> None:
    """Translate AttributeLayerSettings to remove the v944 weight switch.

    Args:
        wrapper: Packet wrapper for ClientboundAttributeLayerSyncPacket.
    """
    payload = AttributeLayerSyncPayloadType(wrapper.passthrough(UVAR_INT))
    if payload is AttributeLayerSyncPayloadType.UPDATE_LAYERS:
        count = wrapper.passthrough(UVAR_INT)
        for _ in range(count):
            wrapper.passthrough(STRING)  # Layer Name
            wrapper.passthrough(VAR_INT)  # Dimension (AutomaticID/DimensionType)
            wrapper.map(ATTRIBUTE_LAYER_SETTINGS_V944, ATTRIBUTE_LAYER_SETTINGS_V975)
            attr_count = wrapper.passthrough(UVAR_INT)
            for _ in range(attr_count):
                wrapper.passthrough(ENVIRONMENT_ATTRIBUTE_DATA)
    elif payload is AttributeLayerSyncPayloadType.UPDATE_SETTINGS:
        wrapper.passthrough(STRING)  # Layer Name
        wrapper.passthrough(VAR_INT)  # Dimension
        wrapper.map(ATTRIBUTE_LAYER_SETTINGS_V944, ATTRIBUTE_LAYER_SETTINGS_V975)
    elif payload in (
        AttributeLayerSyncPayloadType.UPDATE_ENVIRONMENT,
        AttributeLayerSyncPayloadType.REMOVE_ENVIRONMENT,
    ):
        # No AttributeLayerSettings in these payloads -- copy the rest as-is.
        wrapper.passthrough_all()
