"""Direct numerical test of the equivariant ansatz for flower snarks.

The stored certificates are far from equivariant (see equivariance_check.py),
which says nothing about whether equivariant S2-flows exist: Newton iteration
from generic starting points has no reason to land on the symmetric branch.
This script tests the ansatz itself.

Ansatz: fix the rotation R = R_z(theta) about the z-axis with theta = j*pi/n
for odd j (so that R^(2n) = I and R^n is the half-turn realising the Moebius
twist of the strand cycle).  Under the one-block automorphism tau of order 2n
the 6n edges split into four orbits (hub-outer and outer-outer of size n,
hub-strand and strand-strand of size 2n).  The flow is generated from four
template vectors a, b, c, d in R^3 (12 unknowns) by

    x_{tau^k(e0)} = s^(k) R^k x_{e0},

with the orientation signs s^(k) inherited from the stored edge list.  The
full residual (Kirchhoff at all 4n vertices plus all 6n unit norms) is then
minimised over the 12 template unknowns by Levenberg-Marquardt from many
random starts.  A residual at rounding level means the ansatz is numerically
solvable for that (n, j); the wrap-around consistency of each orbit is
automatically enforced because the residual includes the seam equations.

Output: printed table plus equivariant_ansatz_results.json with, for every
n in {5, 7, 9, 11, 13} and every odd j in 1..n, the best residual achieved
and the solved template vectors.
"""

import glob
import json
import os

import numpy as np
import networkx as nx
from networkx.algorithms.isomorphism import GraphMatcher
from scipy.optimize import least_squares

import equivariance_check as eq

RNG = np.random.default_rng(20260718)
N_STARTS = 30
MAX_NFEV = 400


def load_certificate_graph(n):
    hits = [
        f
        for f in glob.glob(f"{eq.CERT_DIR}/*.npz")
        if os.path.basename(f).split("_", 1)[1].rsplit(".", 1)[0] == f"flower_J{n}"
    ]
    data = np.load(hits[0], allow_pickle=True)
    g = nx.from_graph6_bytes(str(data["graph6"][0]).encode("ascii"))
    edges = [tuple(int(a) for a in e) for e in data["edges"].tolist()]
    return g, edges


def orbit_structure(edges, pi, s):
    """Decompose edge indices into <tau>-orbits with cumulative signs.

    Returns a list of orbits; each orbit is a list of (edge_index, k, sign)
    meaning edge_index = tau^k(rep) carries sign * R^k * x_rep.
    """
    m = len(edges)
    seen = np.zeros(m, bool)
    orbits = []
    for e0 in range(m):
        if seen[e0]:
            continue
        orbit = [(e0, 0, 1.0)]
        seen[e0] = True
        cur, sign, k = pi[e0], float(s[e0]), 1
        while cur != e0:
            orbit.append((cur, k, sign))
            seen[cur] = True
            sign, cur, k = sign * s[cur], pi[cur], k + 1
        orbits.append(orbit)
    return orbits


def build_system(n, j):
    g, edges = load_certificate_graph(n)
    canon, sigma = eq.canonical_flower(n)
    gm = GraphMatcher(canon, g)
    assert gm.is_isomorphic()
    phi = gm.mapping
    tau = {phi[v]: phi[sigma[v]] for v in canon.nodes()}
    pi, s = eq.edge_action(edges, tau)
    orbits = orbit_structure(edges, pi, s)
    assert sorted(len(o) for o in orbits) == [n, n, 2 * n, 2 * n]

    theta = j * np.pi / n
    rot = np.array(
        [
            [np.cos(theta), -np.sin(theta), 0.0],
            [np.sin(theta), np.cos(theta), 0.0],
            [0.0, 0.0, 1.0],
        ]
    )
    powers = [np.linalg.matrix_power(rot, k) for k in range(2 * n)]

    m = len(edges)
    nv = g.number_of_nodes()
    b_mat = np.zeros((nv, m))
    for k, (u, v) in enumerate(edges):
        b_mat[u, k] = 1.0
        b_mat[v, k] = -1.0

    def flow_from_templates(t12):
        t = t12.reshape(4, 3)
        x = np.empty((m, 3))
        for oi, orbit in enumerate(orbits):
            for (ei, k, sign) in orbit:
                x[ei] = sign * powers[k] @ t[oi]
        return x

    def residual(t12):
        x = flow_from_templates(t12)
        kirchhoff = (b_mat @ x).ravel()
        norms = np.einsum("ij,ij->i", x, x) - 1.0
        return np.concatenate([kirchhoff, norms])

    return residual, flow_from_templates, b_mat


def solve_case(n, j):
    residual, flow_from_templates, b_mat = build_system(n, j)
    best = (np.inf, None)
    for _ in range(N_STARTS):
        t0 = RNG.normal(size=12)
        sol = least_squares(
            residual, t0, method="lm", xtol=1e-14, ftol=1e-14, max_nfev=MAX_NFEV
        )
        r = np.max(np.abs(sol.fun))
        if r < best[0]:
            best = (r, sol.x.copy())
        if best[0] < 1e-11:
            break
    return best


def main():
    results = []
    print(f"{'graph':<12}{'j':>4}{'theta/pi':>10}{'best max residual':>20}")
    for n in eq.FLOWER_NS:
        for j in range(1, n + 1, 2):
            r, templates = solve_case(n, j)
            solvable = bool(r < 1e-10)
            print(f"flower_J{n:<5}{j:>4}{j / n:>10.4f}{r:>20.3e}"
                  f"   {'SOLVED' if solvable else '--'}")
            results.append(
                {
                    "graph": f"flower_J{n}",
                    "n": n,
                    "j": j,
                    "theta_over_pi": j / n,
                    "best_max_residual": float(r),
                    "solvable": solvable,
                    "templates": None if templates is None else templates.tolist(),
                }
            )
    with open("equivariant_ansatz_results.json", "w") as f:
        json.dump(results, f, indent=1)
    print("saved equivariant_ansatz_results.json")


if __name__ == "__main__":
    main()
