"""SymPy construction of polynomial S²-flow constraints."""
from __future__ import annotations

def build_symbolic_system(graph):
    """Return variables and polynomial conservation/unit-norm equations."""
    import sympy as sp
    from s2flow.algebra.incidence import oriented_incidence
    b, edges = oriented_incidence(graph)
    variables = sp.symbols(f"x0:{len(edges)*3}")
    rows=[variables[3*i:3*i+3] for i in range(len(edges))]
    equations=[]
    for vertex in range(b.shape[0]):
        for coordinate in range(3):
            equations.append(sp.expand(sum(int(b[vertex,e])*rows[e][coordinate] for e in range(len(edges)))))
    equations.extend(sp.expand(sum(component**2 for component in row)-1) for row in rows)
    return variables, equations, edges
