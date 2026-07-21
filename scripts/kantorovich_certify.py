"""Rigorous computer-assisted existence proofs of exact S2-flows.

For each graph that only has a floating-point certificate, we prove the
existence of an EXACT S2-flow near the numerical one via a simplified-Newton
contraction argument (a Newton-Kantorovich type certificate), evaluated
entirely in exact rational arithmetic so that every inequality is proved,
not approximated.

Setup.  Let B be the oriented incidence matrix and Z an INTEGER matrix whose
columns are fundamental cycles (so B Z = 0 exactly over the integers).  Every
X = Z Y automatically satisfies Kirchhoff's law, hence only the unit-norm
equations remain:

    f_e(Y) = || z_e Y ||^2 - 1 = 0   for every edge e   (m equations),

plus three linear gauge equations Y[0,1] = Y[0,2] = Y[1,2] = 0 that remove
the SO(3) symmetry.  For a connected cubic graph m = 3n/2 and the cycle rank
is c = m - n + 1 = n/2 + 1, hence 3c = m + 3 and the system F: R^{3c} ->
R^{m+3} is square.

Certificate.  Let y0 be a rational approximate solution and A a rational
approximate inverse of the Jacobian J(y0).  Define G(y) = y - A F(y).  With
(all norms Euclidean on vectorized Y, all bounds proved rationally):

    alpha >= || A F(y0) ||,
    beta  >= || I - A J(y0) ||,
    L     =  2 * max_e ||z_e|| * ||Z||_2   (global Lipschitz constant of J),
    omega >= ||A|| * L,

if for some radius r > 0

    kappa := beta + omega * r < 1   and   alpha <= (1 - kappa) * r,

then G is a kappa-contraction of the closed ball B(y0, r) into itself, so it
has a unique fixed point y* there; since beta < 1 makes A J(y0) (hence A)
nonsingular, A F(y*) = 0 forces F(y*) = 0.  Consequently X* = Z y* is an
EXACT S2-flow, with || X* - Z y0 ||_F <= ||Z||_2 * r.

Matrix 2-norms are bounded by sqrt(||M||_1 ||M||_inf); square roots of
rationals q = a/b are bounded above by (isqrt(a*b) + 1)/b.  Every quantity
below is a Fraction; no floating-point value is trusted in the final
inequalities (floats are used only to produce the candidates y0 and A).
"""
from __future__ import annotations

import json
import math
from fractions import Fraction

import networkx as nx
import numpy as np

CERTS = [
    ("petersen", "00000_petersen.npz"),
    ("flower_J5", "00005_flower_J5.npz"),
    ("flower_J7", "00006_flower_J7.npz"),
    ("flower_J9", "00007_flower_J9.npz"),
    ("flower_J11", "00008_flower_J11.npz"),
    ("flower_J13", "00009_flower_J13.npz"),
    ("generalized_petersen_5_2", "00010_generalized_petersen_5_2.npz"),
    ("random_n18_seed2515491800", "00160_random_n18_seed2515491800.npz"),
]
CERT_DIR = "/home/claude/work/s2-flow-research/results/massive_run/certificates"


def integer_cycle_basis(n_nodes: int, edges: list[tuple[int, int]]) -> np.ndarray:
    """Fundamental cycle basis: m x c integer matrix Z with B Z = 0 exactly."""
    g = nx.Graph()
    g.add_nodes_from(range(n_nodes))
    for j, (u, v) in enumerate(edges):
        g.add_edge(u, v, idx=j)
    tree = nx.minimum_spanning_tree(g)
    tree_edges = {frozenset((u, v)) for u, v in tree.edges()}
    m = len(edges)
    non_tree = [j for j, (u, v) in enumerate(edges) if frozenset((u, v)) not in tree_edges]
    cols = []
    for j in non_tree:
        u, v = edges[j]
        path = nx.shortest_path(tree, v, u)
        col = [0] * m
        col[j] = 1  # edge j traversed from u to v ... cycle: u->v then path v..u
        for a, b in zip(path[:-1], path[1:]):
            k = g[a][b]["idx"]
            eu, ev = edges[k]
            col[k] = 1 if (eu, ev) == (a, b) else -1
        cols.append(col)
    z = np.array(cols, dtype=np.int64).T  # m x c
    return z


def sqrt_upper(q: Fraction) -> Fraction:
    """Rational upper bound for sqrt(q), q >= 0."""
    if q < 0:
        raise ValueError("negative")
    a, b = q.numerator, q.denominator
    return Fraction(math.isqrt(a * b) + 1, b)


def norm1_inf_bound_sq(mat: list[list[Fraction]]) -> Fraction:
    """Rational upper bound for ||M||_2^2 via ||M||_1 * ||M||_inf."""
    rows = len(mat)
    cols = len(mat[0]) if rows else 0
    col_sums = [Fraction(0)] * cols
    row_max = Fraction(0)
    for i in range(rows):
        s = Fraction(0)
        for j in range(cols):
            a = abs(mat[i][j])
            s += a
            col_sums[j] += a
        row_max = max(row_max, s)
    return max(col_sums, default=Fraction(0)) * row_max


def frac_matmul(a: list[list[Fraction]], b: list[list[Fraction]]) -> list[list[Fraction]]:
    n, k = len(a), len(a[0])
    k2, p = len(b), len(b[0])
    assert k == k2
    bt = list(zip(*b))
    return [[sum(ra[t] * cb[t] for t in range(k)) for cb in bt] for ra in a]


def build_f_and_jac_exact(z_int: np.ndarray, y: list[list[Fraction]]):
    """Exact F(y) (length m+3) and J(y) ((m+3) x 3c) as Fraction structures."""
    m, c = z_int.shape
    zy = []  # m x 3 rows: z_e Y
    for e in range(m):
        row = [Fraction(0)] * 3
        for k in range(c):
            zk = int(z_int[e, k])
            if zk:
                for j in range(3):
                    row[j] += zk * y[k][j]
        zy.append(row)
    f = [sum(v * v for v in zy[e]) - 1 for e in range(m)]
    f += [y[0][1], y[0][2], y[1][2]]
    n_var = 3 * c
    jac = [[Fraction(0)] * n_var for _ in range(m + 3)]
    for e in range(m):
        for k in range(c):
            zk = int(z_int[e, k])
            if zk:
                for j in range(3):
                    jac[e][3 * k + j] = 2 * zy[e][j] * zk
    jac[m][0 * 3 + 1] = Fraction(1)
    jac[m + 1][0 * 3 + 2] = Fraction(1)
    jac[m + 2][1 * 3 + 2] = Fraction(1)
    return f, jac


def certify(name: str, filename: str) -> dict:
    data = np.load(f"{CERT_DIR}/{filename}", allow_pickle=True)
    graph6 = str(data["graph6"][0])
    graph = nx.from_graph6_bytes(graph6.encode("ascii"))
    edges = [tuple(int(a) for a in e) for e in data["edges"].tolist()]
    x = np.asarray(data["X"], dtype=float)
    n, m = graph.number_of_nodes(), len(edges)
    z_int = integer_cycle_basis(n, edges)
    c = z_int.shape[1]
    assert 3 * c == m + 3, (m, c)
    zf = z_int.astype(float)

    # Float stage: initial Y, gauge rotation, Newton refinement.
    y0, *_ = np.linalg.lstsq(zf, x, rcond=None)
    r1 = y0[0] / np.linalg.norm(y0[0])
    r2 = y0[1] - (y0[1] @ r1) * r1
    r2 /= np.linalg.norm(r2)
    r3 = np.cross(r1, r2)
    q = np.column_stack([r1, r2, r3])
    y0 = y0 @ q

    def f_float(yv):
        y = yv.reshape(c, 3)
        zy = zf @ y
        return np.concatenate([np.sum(zy * zy, axis=1) - 1.0, [y[0, 1], y[0, 2], y[1, 2]]])

    def jac_float(yv):
        y = yv.reshape(c, 3)
        zy = zf @ y
        jac = np.zeros((m + 3, 3 * c))
        for e in range(m):
            jac[e] = 2.0 * np.kron(zf[e], np.ones(3)) * np.tile(zy[e], c)
        jac[m, 1] = 1.0
        jac[m + 1, 2] = 1.0
        jac[m + 2, 5] = 1.0
        return jac

    yv = y0.reshape(-1).copy()
    for _ in range(60):
        fv = f_float(yv)
        res = np.max(np.abs(fv))
        if res < 3e-16:
            break
        yv = yv - np.linalg.solve(jac_float(yv), fv)
    jf = jac_float(yv)
    cond = np.linalg.cond(jf)
    a_float = np.linalg.inv(jf)

    # Exact stage.
    y_exact = [[Fraction(float(yv[3 * k + j])) for j in range(3)] for k in range(c)]
    a_exact = [[Fraction(float(a_float[i, j])) for j in range(len(yv))] for i in range(len(yv))]
    f_exact, j_exact = build_f_and_jac_exact(z_int, y_exact)

    # alpha^2 = || A F ||_2^2.
    af = [sum(a_exact[i][t] * f_exact[t] for t in range(len(f_exact))) for i in range(len(yv))]
    alpha = sqrt_upper(sum(v * v for v in af))

    # beta >= || I - A J ||_2.
    aj = frac_matmul(a_exact, j_exact)
    n_var = len(yv)
    e_mat = [[(Fraction(1) if i == j else Fraction(0)) - aj[i][j] for j in range(n_var)] for i in range(n_var)]
    beta = sqrt_upper(norm1_inf_bound_sq(e_mat))

    # omega >= ||A||_2 * L,  L = 2 * max_e ||z_e|| * ||Z||_2.
    a_norm = sqrt_upper(norm1_inf_bound_sq(a_exact))
    z_frac = [[Fraction(int(z_int[i, j])) for j in range(c)] for i in range(m)]
    z_norm = sqrt_upper(norm1_inf_bound_sq(z_frac))
    max_ze = sqrt_upper(Fraction(int(max(np.sum(z_int * z_int, axis=1)))))
    lip = 2 * max_ze * z_norm
    omega = a_norm * lip

    # Choose the radius and verify the contraction inequalities exactly.
    result = {"graph": name, "n": n, "m": m, "cycle_rank": c, "float_condition_number": float(cond)}
    ok = False
    r_used = None
    kappa = None
    for exp in range(6, 16):
        r = Fraction(1, 10**exp)
        kap = beta + omega * r
        if kap < 1 and alpha <= (1 - kap) * r:
            ok, r_used, kappa = True, r, kap
            break
    result.update(
        {
            "alpha_upper": float(alpha),
            "beta_upper": float(beta),
            "omega_upper": float(omega),
            "radius": (float(r_used) if r_used is not None else None),
            "kappa_upper": (float(kappa) if kappa is not None else None),
            "certified": ok,
        }
    )
    return result


def main() -> None:
    results = []
    for name, filename in CERTS:
        res = certify(name, filename)
        results.append(res)
        status = "PROVED" if res["certified"] else "FAILED"
        print(
            f"{status}  {name}: n={res['n']}, m={res['m']}, alpha<={res['alpha_upper']:.3e}, "
            f"beta<={res['beta_upper']:.3e}, omega<={res['omega_upper']:.3e}, "
            f"r={res['radius']}, kappa<={res['kappa_upper'] if res['kappa_upper'] else float('nan'):.3e}, "
            f"cond(J)~{res['float_condition_number']:.2e}"
        )
    with open("/home/claude/work/kantorovich_results.json", "w") as fh:
        json.dump(results, fh, indent=2)


if __name__ == "__main__":
    main()
