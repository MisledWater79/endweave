"""PartyChangedPacket (342) -- v975 client to v944 server.

v944 carried ``Optional[string party_id]``; v975 widened it to
``Optional[PlayerPartyInfo { string party_id, bool is_party_leader }]``.
Strip the trailing ``is_party_leader`` bool so the v944 server only sees the
fields it expects.
"""

from endstone_endweave.codec import BOOL, STRING, PacketWrapper


def rewrite_party_changed(wrapper: PacketWrapper) -> None:
    """Drop the v975-only is_party_leader bool from the optional party info.

    Args:
        wrapper: Packet wrapper for PartyChangedPacket.
    """
    if wrapper.passthrough(BOOL):  # Optional present?
        wrapper.passthrough(STRING)  # party_id
        wrapper.read(BOOL)  # is_party_leader -- strip
