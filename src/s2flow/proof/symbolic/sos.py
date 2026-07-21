"""Sum-of-squares relaxation interface."""
from __future__ import annotations

def availability() -> dict[str, bool]:
    """Report optional SOS-related package availability without importing them eagerly."""
    import importlib.util
    return {name: importlib.util.find_spec(name) is not None for name in ("cvxpy", "sympy", "ncpol2sdpa")}

def residual_polynomial(equations):
    """Return the sum of squared polynomial residuals."""
    return sum(equation**2 for equation in equations)
