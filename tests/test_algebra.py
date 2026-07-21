"""Tests for the scalar reduction and local identities."""

from math import isclose

import numpy as np

from goldberg_s2.algebra import local_coordinates, scalar_function


def test_local_channel_identities() -> None:
    """The local formulas must produce four unit vectors and two vertex balances."""
    x = 0.2
    y = 0.75
    local = local_coordinates(y, x)

    a = np.array([local.a_x, 0.0, local.a_z])
    b = np.array([-local.b_x, y, -local.b_z])
    c = np.array([local.b_x, y, local.b_z])
    p = np.array([-y * x, -y, local.z])

    angle = 2.0 * np.arctan2(1.0, x)
    cosine = np.cos(-angle)
    sine = np.sin(-angle)
    inverse_rotation = np.array(
        [[cosine, -sine, 0.0], [sine, cosine, 0.0], [0.0, 0.0, 1.0]]
    )

    for vector in (a, b, c, p):
        assert isclose(float(np.dot(vector, vector)), 1.0, abs_tol=2e-14)
    assert np.max(np.abs(a + b - inverse_rotation @ p)) < 2e-14
    assert np.max(np.abs(-a + c + p)) < 2e-14


def test_scalar_bracket_at_extreme_parameters() -> None:
    """The theorem bracket must hold at both ends of the x-domain."""
    for x in (0.0, 13.0 / 40.0):
        assert scalar_function(2.0 / 3.0, x) < 0.0
        assert scalar_function(21.0 / 25.0, x) > 0.0
