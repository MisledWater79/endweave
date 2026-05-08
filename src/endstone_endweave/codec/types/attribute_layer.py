"""EAS attribute layer types -- AttributeLayerSettings, AttributeData variants, EnvironmentAttributeData.

Mirrors the EndstoneMC/protocol-docs definitions for r26_u1 / r26_u2:
  - EAS::AttributeLayerSettings (v944 weight switch removed in v975)
  - EAS::BoolAttributeData
  - EAS::FloatAttributeData
  - EAS::ColorAttributeData
  - EAS::EnvironmentAttributeData

The polymorphic AttributeData (Bool / Float / Color, selected by uvarint32
type tag) is exposed as the ``ATTRIBUTE_DATA`` Type singleton; the named
variants stay accessible for callers that need the underlying form.
"""

from dataclasses import dataclass

from endstone_endweave.codec.reader import PacketReader
from endstone_endweave.codec.writer import PacketWriter

from .enums import AttributeDataType, AttributeLayerWeightType
from .primitives import BOOL, FLOAT_LE, INT_LE, STRING, UINT_LE, Type


@dataclass
class BoolAttributeData:
    """EAS::BoolAttributeData."""

    value: bool
    operation: str | None  # None when absent on the wire


@dataclass
class FloatAttributeData:
    """EAS::FloatAttributeData."""

    value: float
    operation: str | None
    constraint_min: float | None
    constraint_max: float | None


@dataclass
class ColorAttributeData:
    """EAS::ColorAttributeData. ``value`` is a Color255RGBA hex string like ``#aabbccdd``."""

    value: str
    operation: str | None


@dataclass
class AttributeData:
    """EAS attribute polymorphic value, tagged by ``kind`` (uvarint32 on the wire)."""

    kind: AttributeDataType
    bool_data: BoolAttributeData | None = None
    float_data: FloatAttributeData | None = None
    color_data: ColorAttributeData | None = None


@dataclass
class EnvironmentAttributeData:
    """EAS::EnvironmentAttributeData."""

    name: str
    from_attribute: AttributeData | None
    attribute: AttributeData
    to_attribute: AttributeData | None
    current_transition_ticks: int
    total_transition_ticks: int
    easing: str


class _BoolAttributeDataType(Type[BoolAttributeData]):
    def read(self, reader: PacketReader) -> BoolAttributeData:
        value = reader.read_bool()
        operation = reader.read_string() if reader.read_bool() else None
        return BoolAttributeData(value=value, operation=operation)

    def write(self, writer: PacketWriter, value: BoolAttributeData) -> None:
        writer.write_bool(value.value)
        if value.operation is not None:
            writer.write_bool(True)
            writer.write_string(value.operation)
        else:
            writer.write_bool(False)


class _FloatAttributeDataType(Type[FloatAttributeData]):
    def read(self, reader: PacketReader) -> FloatAttributeData:
        value = reader.read_float_le()
        operation = reader.read_string() if reader.read_bool() else None
        constraint_min = reader.read_float_le() if reader.read_bool() else None
        constraint_max = reader.read_float_le() if reader.read_bool() else None
        return FloatAttributeData(
            value=value,
            operation=operation,
            constraint_min=constraint_min,
            constraint_max=constraint_max,
        )

    def write(self, writer: PacketWriter, value: FloatAttributeData) -> None:
        writer.write_float_le(value.value)
        if value.operation is not None:
            writer.write_bool(True)
            writer.write_string(value.operation)
        else:
            writer.write_bool(False)
        if value.constraint_min is not None:
            writer.write_bool(True)
            writer.write_float_le(value.constraint_min)
        else:
            writer.write_bool(False)
        if value.constraint_max is not None:
            writer.write_bool(True)
            writer.write_float_le(value.constraint_max)
        else:
            writer.write_bool(False)


class _ColorAttributeDataType(Type[ColorAttributeData]):
    def read(self, reader: PacketReader) -> ColorAttributeData:
        value = reader.read_string()
        operation = reader.read_string() if reader.read_bool() else None
        return ColorAttributeData(value=value, operation=operation)

    def write(self, writer: PacketWriter, value: ColorAttributeData) -> None:
        writer.write_string(value.value)
        if value.operation is not None:
            writer.write_bool(True)
            writer.write_string(value.operation)
        else:
            writer.write_bool(False)


BOOL_ATTRIBUTE_DATA = _BoolAttributeDataType()
FLOAT_ATTRIBUTE_DATA = _FloatAttributeDataType()
COLOR_ATTRIBUTE_DATA = _ColorAttributeDataType()


class _AttributeDataType(Type[AttributeData]):
    """Polymorphic AttributeData: uvarint32 kind tag + matching variant."""

    def read(self, reader: PacketReader) -> AttributeData:
        kind = AttributeDataType(reader.read_uvarint())
        if kind is AttributeDataType.BOOL:
            return AttributeData(kind=kind, bool_data=BOOL_ATTRIBUTE_DATA.read(reader))
        if kind is AttributeDataType.FLOAT:
            return AttributeData(kind=kind, float_data=FLOAT_ATTRIBUTE_DATA.read(reader))
        return AttributeData(kind=kind, color_data=COLOR_ATTRIBUTE_DATA.read(reader))

    def write(self, writer: PacketWriter, value: AttributeData) -> None:
        writer.write_uvarint(value.kind.value)
        if value.kind is AttributeDataType.BOOL:
            assert value.bool_data is not None
            BOOL_ATTRIBUTE_DATA.write(writer, value.bool_data)
        elif value.kind is AttributeDataType.FLOAT:
            assert value.float_data is not None
            FLOAT_ATTRIBUTE_DATA.write(writer, value.float_data)
        else:
            assert value.color_data is not None
            COLOR_ATTRIBUTE_DATA.write(writer, value.color_data)


ATTRIBUTE_DATA = _AttributeDataType()


class _EnvironmentAttributeDataType(Type[EnvironmentAttributeData]):
    def read(self, reader: PacketReader) -> EnvironmentAttributeData:
        name = STRING.read(reader)
        from_attribute = ATTRIBUTE_DATA.read(reader) if BOOL.read(reader) else None
        attribute = ATTRIBUTE_DATA.read(reader)
        to_attribute = ATTRIBUTE_DATA.read(reader) if BOOL.read(reader) else None
        current_ticks = UINT_LE.read(reader)
        total_ticks = UINT_LE.read(reader)
        easing = STRING.read(reader)
        return EnvironmentAttributeData(
            name=name,
            from_attribute=from_attribute,
            attribute=attribute,
            to_attribute=to_attribute,
            current_transition_ticks=current_ticks,
            total_transition_ticks=total_ticks,
            easing=easing,
        )

    def write(self, writer: PacketWriter, value: EnvironmentAttributeData) -> None:
        STRING.write(writer, value.name)
        if value.from_attribute is not None:
            BOOL.write(writer, True)
            ATTRIBUTE_DATA.write(writer, value.from_attribute)
        else:
            BOOL.write(writer, False)
        ATTRIBUTE_DATA.write(writer, value.attribute)
        if value.to_attribute is not None:
            BOOL.write(writer, True)
            ATTRIBUTE_DATA.write(writer, value.to_attribute)
        else:
            BOOL.write(writer, False)
        UINT_LE.write(writer, value.current_transition_ticks)
        UINT_LE.write(writer, value.total_transition_ticks)
        STRING.write(writer, value.easing)


ENVIRONMENT_ATTRIBUTE_DATA = _EnvironmentAttributeDataType()


@dataclass
class AttributeLayerSettings:
    """EAS::AttributeLayerSettings.

    The v944 wire encoded ``weight`` as a tagged union of float-or-string;
    v975 dropped the union and serializes ``weight`` as a plain float. This
    dataclass keeps only the float since the string form has no v975 encoding,
    so a v944 string weight is coerced to ``string_weight_default`` on read.
    """

    priority: int
    weight: float
    enabled: bool
    transitions_paused: bool


# Default float weight used when a v944 server emits a string weight that has
# no representation on the v975 wire.
_V944_STRING_WEIGHT_DEFAULT = 1.0


class _AttributeLayerSettingsV944Type(Type[AttributeLayerSettings]):
    """v944 AttributeLayerSettings: Weight is a switch(uvarint32) of float|string."""

    def read(self, reader: PacketReader) -> AttributeLayerSettings:
        priority = INT_LE.read(reader)
        weight_type = AttributeLayerWeightType(reader.read_uvarint())
        if weight_type is AttributeLayerWeightType.FLOAT:
            weight = FLOAT_LE.read(reader)
        else:
            STRING.read(reader)  # discarded -- no v975 representation
            weight = _V944_STRING_WEIGHT_DEFAULT
        enabled = BOOL.read(reader)
        transitions_paused = BOOL.read(reader)
        return AttributeLayerSettings(
            priority=priority,
            weight=weight,
            enabled=enabled,
            transitions_paused=transitions_paused,
        )

    def write(self, writer: PacketWriter, value: AttributeLayerSettings) -> None:
        INT_LE.write(writer, value.priority)
        writer.write_uvarint(AttributeLayerWeightType.FLOAT.value)
        FLOAT_LE.write(writer, value.weight)
        BOOL.write(writer, value.enabled)
        BOOL.write(writer, value.transitions_paused)


class _AttributeLayerSettingsV975Type(Type[AttributeLayerSettings]):
    """v975 AttributeLayerSettings: Weight is a plain float."""

    def read(self, reader: PacketReader) -> AttributeLayerSettings:
        return AttributeLayerSettings(
            priority=INT_LE.read(reader),
            weight=FLOAT_LE.read(reader),
            enabled=BOOL.read(reader),
            transitions_paused=BOOL.read(reader),
        )

    def write(self, writer: PacketWriter, value: AttributeLayerSettings) -> None:
        INT_LE.write(writer, value.priority)
        FLOAT_LE.write(writer, value.weight)
        BOOL.write(writer, value.enabled)
        BOOL.write(writer, value.transitions_paused)


ATTRIBUTE_LAYER_SETTINGS_V944 = _AttributeLayerSettingsV944Type()
ATTRIBUTE_LAYER_SETTINGS_V975 = _AttributeLayerSettingsV975Type()
