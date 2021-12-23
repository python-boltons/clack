"""Tests for the clack package."""

from __future__ import annotations

from clack import dummy


def test_dummy() -> None:
    """Test the dummy() function."""
    assert dummy(1, 2) == 3
