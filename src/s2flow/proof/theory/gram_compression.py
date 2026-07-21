"""Cycle-space Gram compression certificates for S2-flows."""
from __future__ import annotations

import numpy as np


def verify_cycle_gram_certificate(
    cycle_matrix: np.ndarray,
    gram: np.ndarray,
    *,
    tolerance: float = 1e-8,
) -> dict[str, object]:
    """Verify the sufficient rank-three PSD cycle-space criterion.

    If ``gram`` is positive semidefinite of rank at most three and every row
    ``z_e`` of ``cycle_matrix`` satisfies ``z_e.T @ gram @ z_e == 1``, then a
    factorisation ``gram = A @ A.T`` gives the S2-flow ``X = cycle_matrix @ A``.
    """
    q = np.asarray(gram, dtype=float)
    z = np.asarray(cycle_matrix, dtype=float)
    symmetry_residual = float(np.max(np.abs(q - q.T)))
    q = (q + q.T) / 2.0
    eigenvalues, eigenvectors = np.linalg.eigh(q)
    min_eigenvalue = float(eigenvalues.min(initial=0.0))
    positive = eigenvalues > tolerance
    rank = int(np.count_nonzero(positive))
    edge_quadratics = np.einsum("ij,jk,ik->i", z, q, z)
    unit_residual = float(np.max(np.abs(edge_quadratics - 1.0)))

    clipped = np.clip(eigenvalues, 0.0, None)
    factors = eigenvectors[:, clipped > tolerance] * np.sqrt(clipped[clipped > tolerance])
    if factors.shape[1] < 3:
        factors = np.pad(factors, ((0, 0), (0, 3 - factors.shape[1])))
    x = z @ factors[:, :3]

    return {
        "valid": bool(
            symmetry_residual <= tolerance
            and min_eigenvalue >= -tolerance
            and rank <= 3
            and unit_residual <= tolerance
        ),
        "symmetry_residual": symmetry_residual,
        "minimum_eigenvalue": min_eigenvalue,
        "rank": rank,
        "unit_quadratic_residual": unit_residual,
        "flow": x,
    }
