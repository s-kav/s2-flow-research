"""Regression test for the failed fundamental-generator ansatz."""

from math import pi, sin


def test_fundamental_rotation_chord_obstruction() -> None:
    """For k >= 7, a 2*pi/k rotation cannot create a unit chord."""
    for k in (7, 9, 11, 101):
        maximum_chord = 2.0 * sin(pi / k)
        assert maximum_chord < 1.0
