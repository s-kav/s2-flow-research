"""Groebner-basis diagnostics for small graph instances."""
from __future__ import annotations

def groebner_diagnostics(equations, variables, order: str = "grevlex") -> dict[str, object]:
    """Build a Groebner basis and detect the unit ideal."""
    import sympy as sp
    basis=sp.groebner(equations, *variables, order=order)
    expressions=[poly.as_expr() for poly in basis.polys]
    inconsistent=any(expression == 1 for expression in expressions)
    return {"inconsistent": inconsistent, "basis_size": len(expressions), "basis": expressions}
