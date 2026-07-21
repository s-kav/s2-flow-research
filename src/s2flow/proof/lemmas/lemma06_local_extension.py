"""Local extension of two unit vectors through a cubic conservation law."""
from __future__ import annotations
import numpy as np

def forced_third_vector(first: np.ndarray, second: np.ndarray, signs: tuple[int, int, int] = (1, 1, 1)) -> np.ndarray:
    """Solve s1*u + s2*v + s3*w = 0 for w."""
    u = np.asarray(first, dtype=float)
    v = np.asarray(second, dtype=float)
    s1, s2, s3 = signs
    if u.shape != (3,) or v.shape != (3,) or s3 == 0:
        raise ValueError("Expected two 3D vectors and nonzero third sign")
    return -(s1 * u + s2 * v) / s3

def local_extension_diagnostics(first: np.ndarray, second: np.ndarray, tolerance: float = 1e-8) -> dict[str, float | bool]:
    """Check whether the forced third vector has unit norm."""
    third = forced_third_vector(first, second)
    residual = abs(float(np.linalg.norm(third)) - 1.0)
    return {"extendable": residual <= tolerance, "unit_norm_residual": residual, "dot_product": float(np.dot(first, second))}
