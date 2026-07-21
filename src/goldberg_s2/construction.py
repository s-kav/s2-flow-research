"""Explicit equivariant S^2-flow templates for Goldberg snarks."""

from __future__ import annotations

from math import pi, sqrt, tan

import numpy as np

from .algebra import local_coordinates, scalar_bracket, scalar_function
from .graph import validate_k

TEMPLATE_NAMES: tuple[str, ...] = (
    "a_12",
    "b_17",
    "c_28",
    "d_34",
    "e_38",
    "f_47",
    "g_56",
    "h_67",
    "i_68",
    "p_2_to_1_next",
    "q_4_to_3_next",
    "r_5_to_5_next",
)


def representation_index(k: int) -> int:
    """Return the index-(k-1)/2 cyclic representation used in the proof."""
    validate_k(k)
    return (k - 1) // 2


def rotation_angle(k: int) -> float:
    """Return phi = 2*pi*((k-1)/2)/k = pi - pi/k."""
    validate_k(k)
    return pi - pi / k


def scalar_parameter_x(k: int) -> float:
    """Return x = tan(pi/(2k)) = cot(phi/2)."""
    validate_k(k)
    return tan(pi / (2.0 * k))


def rotation_matrix(angle: float) -> np.ndarray:
    """Return the right-handed rotation around the z-axis."""
    cosine = np.cos(angle)
    sine = np.sin(angle)
    return np.array(
        [
            [cosine, -sine, 0.0],
            [sine, cosine, 0.0],
            [0.0, 0.0, 1.0],
        ],
        dtype=float,
    )


def solve_scalar_root(k: int, tolerance: float = 1e-15, max_iterations: int = 200) -> float:
    """Solve the unique scalar equation by certified-bracket bisection."""
    x = scalar_parameter_x(k)
    lower, upper = scalar_bracket()
    f_lower = scalar_function(lower, x)
    f_upper = scalar_function(upper, x)
    if not f_lower < 0.0 < f_upper:
        raise RuntimeError(
            f"The theorem bracket failed for k={k}: "
            f"H(lower)={f_lower}, H(upper)={f_upper}"
        )

    for _ in range(max_iterations):
        midpoint = 0.5 * (lower + upper)
        f_midpoint = scalar_function(midpoint, x)
        if abs(f_midpoint) <= tolerance or upper - lower <= tolerance:
            return midpoint
        if f_midpoint < 0.0:
            lower = midpoint
        else:
            upper = midpoint

    raise RuntimeError(f"Bisection did not converge for k={k}")


def build_templates(k: int, scalar_root: float | None = None) -> np.ndarray:
    """Build the twelve unit-vector templates in theorem order."""
    validate_k(k)
    x = scalar_parameter_x(k)
    s = solve_scalar_root(k) if scalar_root is None else float(scalar_root)
    t = 0.5 - s

    left = local_coordinates(s, x)
    right = local_coordinates(t, x)

    a = np.array([left.a_x, 0.0, left.a_z])
    b = np.array([-left.b_x, s, -left.b_z])
    c = np.array([left.b_x, s, left.b_z])

    d = np.array([right.a_x, 0.0, right.a_z])
    e = np.array([-right.b_x, t, -right.b_z])
    f = np.array([right.b_x, t, right.b_z])

    g = np.array([0.0, -1.0, 0.0])
    h = np.array(
        [
            left.b_x - right.b_x,
            -0.5,
            left.b_z - right.b_z,
        ]
    )
    i = np.array(
        [
            right.b_x - left.b_x,
            -0.5,
            right.b_z - left.b_z,
        ]
    )

    p = np.array([-s * x, -s, left.z])
    q = np.array([-t * x, -t, right.z])
    r = np.array([0.5 * x, 0.5, 0.5 * sqrt(3.0 - x * x)])

    return np.vstack((a, b, c, d, e, f, g, h, i, p, q, r))
