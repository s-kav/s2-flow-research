"""Extend the Z_n equivariant ansatz beyond the stored campaign.

The tau^2 (pure Z_n) ansatz needs only the graph, not a stored certificate, so
this script solves it on canonical flower snarks J_n for all odd n from 5 to
41 on the uniform branch theta = 2*pi/n (k = 1), then measures continuity of
the solution branch: consecutive solutions are gauge-aligned (rotation about
the z-axis, optional z-flip and x-reflection, all of which commute with the
ansatz) and their template distance is reported as a function of theta.

Outputs: printed table, ansatz_extension_results.json, and per-n flows saved
as npz files (graph6, edges, X) in equivariant_flows/ in the same format as
the campaign certificates, ready for Newton-Kantorovich certification.
"""

import json
import os

import numpy as np
import networkx as nx
from scipy.optimize import least_squares

import equivariance_check as eq
import equivariant_ansatz_solve as ea

RNG = np.random.default_rng(20260718)
OUT_DIR = "equivariant_flows"
NS = list(range(5, 42, 2))


def canonical_relabelled(n):
    canon, sigma = eq.canonical_flower(n)
    nodes = sorted(canon.nodes(), key=str)
    relabel = {v: i for i, v in enumerate(nodes)}
    g = nx.relabel_nodes(canon, relabel)
    tau1 = {relabel[v]: relabel[sigma[v]] for v in canon.nodes()}
    edges = sorted((min(u, v), max(u, v)) for u, v in g.edges())
    return g, edges, tau1


def make_system(n, theta):
    g, edges, tau1 = canonical_relabelled(n)
    tau2 = {v: tau1[tau1[v]] for v in tau1}
    pi, s = eq.edge_action(edges, tau2)
    orbits = ea.orbit_structure(edges, pi, s)
    rot = np.array(
        [
            [np.cos(theta), -np.sin(theta), 0.0],
            [np.sin(theta), np.cos(theta), 0.0],
            [0.0, 0.0, 1.0],
        ]
    )
    powers = [np.linalg.matrix_power(rot, k) for k in range(max(len(o) for o in orbits))]
    m = len(edges)
    b = np.zeros((g.number_of_nodes(), m))
    for k, (u, v) in enumerate(edges):
        b[u, k] = 1.0
        b[v, k] = -1.0

    def build_x(tvec):
        t = tvec.reshape(len(orbits), 3)
        x = np.empty((m, 3))
        for oi, orbit in enumerate(orbits):
            for (ei, k, sign) in orbit:
                x[ei] = sign * powers[k] @ t[oi]
        return x

    def residual(tvec):
        x = build_x(tvec)
        return np.concatenate(
            [(b @ x).ravel(), np.einsum("ij,ij->i", x, x) - 1.0]
        )

    return g, edges, orbits, residual, build_x, b


def solve_branch(n, warm=None, starts=40):
    theta = 2.0 * np.pi / n
    g, edges, orbits, residual, build_x, b = make_system(n, theta)
    n_orb = len(orbits)
    best, tbest = np.inf, None
    inits = []
    if warm is not None:
        inits.append(warm)
    inits += [RNG.normal(size=3 * n_orb) for _ in range(starts)]
    for t0 in inits:
        sol = least_squares(
            residual, t0, method="lm", xtol=1e-14, ftol=1e-14, max_nfev=600
        )
        r = float(np.max(np.abs(sol.fun)))
        if r < best:
            best, tbest = r, sol.x.copy()
        if best < 1e-12:
            break
    x = build_x(tbest)
    kirch = float(np.max(np.abs(b @ x)))
    norm = float(np.max(np.abs(np.linalg.norm(x, axis=1) - 1.0)))
    return g, edges, tbest, x, best, kirch, norm


def align(t_ref, t_new):
    """Gauge-align template arrays by rotation about z, optional z-flip and
    x-reflection (the symmetries commuting with R_z)."""
    a = t_ref.reshape(-1, 3)
    c = t_new.reshape(-1, 3)
    best = np.inf
    for zflip in (1.0, -1.0):
        for xrefl in (False, True):
            d = c.copy()
            d[:, 2] *= zflip
            if xrefl:
                d[:, 1] *= -1.0
            num = np.sum(a[:, 0] * d[:, 0] + a[:, 1] * d[:, 1]) + 1j * np.sum(
                a[:, 1] * d[:, 0] - a[:, 0] * d[:, 1]
            )
            phi = -np.angle(num)
            cph, sph = np.cos(phi), np.sin(phi)
            e = d.copy()
            e[:, 0] = cph * d[:, 0] - sph * d[:, 1]
            e[:, 1] = sph * d[:, 0] + cph * d[:, 1]
            best = min(best, float(np.max(np.linalg.norm(a - e, axis=1))))
    return best


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    results = []
    warm = None
    prev_templates = None
    print(f"{'n':>4}{'theta/pi':>10}{'max residual':>14}{'kirchhoff':>12}"
          f"{'norm dev':>12}{'branch step':>13}")
    for n in NS:
        g, edges, t, x, r, kirch, norm = solve_branch(n, warm=warm)
        step = None if prev_templates is None else align(prev_templates, t)
        g6 = nx.to_graph6_bytes(g, header=False).decode().strip()
        np.savez(
            f"{OUT_DIR}/flower_J{n}_equivariant.npz",
            graph6=np.array([g6]),
            edges=np.array(edges),
            X=x,
        )
        print(f"{n:>4}{2.0 / n:>10.4f}{r:>14.3e}{kirch:>12.3e}{norm:>12.3e}"
              + (f"{step:>13.3e}" if step is not None else f"{'--':>13}"))
        results.append(
            {
                "n": n,
                "theta_over_pi": 2.0 / n,
                "max_residual": r,
                "kirchhoff_residual": kirch,
                "norm_deviation": norm,
                "branch_step_from_previous": step,
                "solved": bool(r < 1e-10),
            }
        )
        warm = t
        prev_templates = t
    with open("ansatz_extension_results.json", "w") as f:
        json.dump(results, f, indent=1)
    print("saved ansatz_extension_results.json and flows in", OUT_DIR)


if __name__ == "__main__":
    main()
