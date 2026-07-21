"""Numerical evaluation of symbolic polynomial systems."""
from __future__ import annotations
import numpy as np

def evaluate_system(equations, variables, point: np.ndarray) -> np.ndarray:
    """Evaluate symbolic equations at a numeric point."""
    if len(variables) != len(point):
        raise ValueError("point dimension does not match variable count")
    substitution=dict(zip(variables, map(float, point), strict=True))
    return np.asarray([float(equation.evalf(subs=substitution)) for equation in equations])

def max_residual(equations, variables, point: np.ndarray) -> float:
    """Return the maximum absolute polynomial residual."""
    values=evaluate_system(equations, variables, point)
    return float(np.max(np.abs(values))) if values.size else 0.0
