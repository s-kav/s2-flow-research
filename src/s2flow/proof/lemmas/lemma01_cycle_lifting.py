"""Cycle-space lifting checks."""
from __future__ import annotations
import numpy as np
from s2flow.algebra.incidence import cycle_basis_matrix

def lift_cycle_coordinates(graph, coordinates: np.ndarray) -> np.ndarray:
    """Lift cycle-space coordinates to an edge-vector flow."""
    _, z, _ = cycle_basis_matrix(graph)
    y = np.asarray(coordinates, dtype=float)
    if y.ndim != 2 or y.shape[0] != z.shape[1]:
        raise ValueError("coordinates must have shape (cycle_rank, dimension)")
    return z @ y

def verify_cycle_lifting(graph, coordinates: np.ndarray, tolerance: float = 1e-10) -> dict[str, float | bool]:
    """Verify that a lifted vector lies in the incidence null space."""
    b, _, _ = cycle_basis_matrix(graph)
    x = lift_cycle_coordinates(graph, coordinates)
    residual = float(np.max(np.abs(b @ x))) if x.size else 0.0
    return {"valid": residual <= tolerance, "max_conservation_residual": residual}
