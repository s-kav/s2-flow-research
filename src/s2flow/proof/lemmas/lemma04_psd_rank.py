"""Gram-matrix PSD and rank checks."""
from __future__ import annotations
import numpy as np

def gram_diagnostics(vectors: np.ndarray, tolerance: float = 1e-8) -> dict[str, object]:
    """Return PSD, diagonal, and numerical-rank diagnostics for edge vectors."""
    x = np.asarray(vectors, dtype=float)
    q = x @ x.T
    eigenvalues = np.linalg.eigvalsh((q + q.T) / 2.0)
    rank = int(np.count_nonzero(eigenvalues > tolerance))
    return {
        "psd": bool(eigenvalues.min(initial=0.0) >= -tolerance),
        "rank": rank,
        "rank_at_most_three": rank <= 3,
        "max_diagonal_residual": float(np.max(np.abs(np.diag(q) - 1.0))),
        "eigenvalues": eigenvalues.tolist(),
    }
