"""Independent verification of numerical S²-flow candidates."""
from __future__ import annotations
import numpy as np


def verify_candidate(b: np.ndarray, x: np.ndarray, tolerance: float = 1e-8) -> dict[str, object]:
    """Verify Kirchhoff balance, unit norms, and Gram constraints."""
    if x.ndim != 2 or x.shape[0] != b.shape[1]:
        raise ValueError("X must have shape (number_of_edges, dimension)")
    balance = b @ x
    norms = np.linalg.norm(x, axis=1)
    q = x @ x.T
    eig = np.linalg.eigvalsh((q + q.T) / 2.0)
    rank_tol = max(q.shape) * np.finfo(float).eps * max(1.0, float(np.max(np.abs(eig))))
    result = {
        "max_conservation_residual": float(np.max(np.abs(balance))),
        "max_unit_norm_residual": float(np.max(np.abs(norms - 1.0))),
        "gram_min_eigenvalue": float(np.min(eig)),
        "gram_rank": int(np.sum(eig > rank_tol)),
        "max_gram_diagonal_residual": float(np.max(np.abs(np.diag(q) - 1.0))),
        "max_bq_residual": float(np.max(np.abs(b @ q))),
    }
    result["valid"] = bool(result["max_conservation_residual"] <= tolerance and result["max_unit_norm_residual"] <= tolerance)
    return result
