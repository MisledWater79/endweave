"""Lookup of protocol version objects by patch/exact name."""

from __future__ import annotations

from endstone_endweave.protocol.versions import (
    get_version_by_name,
    v1_26_0,
    v1_26_10,
)


def test_patch_version_maps_to_base() -> None:
    """A patch like 1.26.2 should resolve to the 1.26.0 base entry."""
    assert get_version_by_name("1.26.2") is v1_26_0


def test_exact_version_match() -> None:
    assert get_version_by_name("1.26.10") is v1_26_10


def test_unknown_version_returns_none() -> None:
    assert get_version_by_name("1.99.0") is None
