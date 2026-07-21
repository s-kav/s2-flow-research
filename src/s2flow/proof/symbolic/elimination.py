"""Symbolic elimination helpers."""
from __future__ import annotations

def eliminate_variables(equations, eliminate, keep):
    """Compute an elimination ideal basis with lexicographic ordering."""
    import sympy as sp
    ordered=tuple(eliminate)+tuple(keep)
    basis=sp.groebner(equations, *ordered, order="lex")
    eliminated=[]
    eliminate_set=set(eliminate)
    for polynomial in basis.polys:
        expression=polynomial.as_expr()
        if not expression.free_symbols.intersection(eliminate_set):
            eliminated.append(expression)
    return eliminated
