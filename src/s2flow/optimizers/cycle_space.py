"""Cycle-space nonlinear least-squares solver."""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from scipy.optimize import least_squares
from s2flow.algebra.incidence import cycle_basis_matrix
from s2flow.flows.verification import verify_candidate

@dataclass(frozen=True)
class SolveResult:
    x: np.ndarray
    y: np.ndarray
    metrics: dict[str, object]
    cost: float
    nfev: int


def solve_cycle_space(g, dimension: int = 3, restarts: int = 12, seed: int = 20260717, max_nfev: int = 20000, tolerance: float = 1e-8) -> SolveResult:
    """Search for X = ZY with unit row norms; conservation is exact up to null-space precision."""
    b, z, _ = cycle_basis_matrix(g)
    rng = np.random.default_rng(seed)
    best = None
    def residual(flat: np.ndarray) -> np.ndarray:
        y = flat.reshape(z.shape[1], dimension)
        x = z @ y
        return np.sum(x * x, axis=1) - 1.0
    for _ in range(restarts):
        y0 = rng.normal(size=(z.shape[1], dimension))
        out = least_squares(residual, y0.ravel(), max_nfev=max_nfev, xtol=tolerance, ftol=tolerance, gtol=tolerance)
        y = out.x.reshape(z.shape[1], dimension)
        x = z @ y
        metrics = verify_candidate(b, x, tolerance=tolerance * 10)
        candidate = SolveResult(x=x, y=y, metrics=metrics, cost=float(out.cost), nfev=int(out.nfev))
        if best is None or candidate.cost < best.cost:
            best = candidate
        if metrics["valid"]:
            break
    assert best is not None
    return best
