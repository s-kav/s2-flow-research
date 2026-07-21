"""Boundary-state compatibility checks for graph gluing."""
from __future__ import annotations
import numpy as np

def boundary_flux(vectors: np.ndarray, signs: np.ndarray) -> np.ndarray:
    """Compute signed flux through a cut boundary."""
    x = np.asarray(vectors, dtype=float)
    s = np.asarray(signs, dtype=float)
    if x.ndim != 2 or s.shape != (x.shape[0],):
        raise ValueError("Incompatible boundary vectors and signs")
    return s @ x

def can_glue(left_vectors: np.ndarray, left_signs: np.ndarray, right_vectors: np.ndarray, right_signs: np.ndarray, tolerance: float = 1e-8) -> bool:
    """Check whether two boundary flow states cancel after gluing."""
    return bool(np.linalg.norm(boundary_flux(left_vectors, left_signs) + boundary_flux(right_vectors, right_signs), ord=np.inf) <= tolerance)
