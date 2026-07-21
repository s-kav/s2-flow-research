"""Fully independent verification of every stored S2-flow certificate.

This script deliberately shares no code with the uploaded repository.
For each NPZ certificate it:
  1. decodes the stored graph6 string with networkx,
  2. checks the graph is simple, connected, cubic, and bridgeless,
  3. rebuilds the oriented incidence matrix B from the stored edge order,
  4. recomputes max |B X| (Kirchhoff residual), max | ||x_e|| - 1 | (unit-norm
     residual), and the numerical rank of the Gram matrix Q = X X^T,
  5. classifies the certificate as constructive (entries in {0, +-1/sqrt(2)})
     or numerical.
"""
from __future__ import annotations

import glob
import json
import math

import networkx as nx
import numpy as np

CERT_DIR = "/home/claude/work/s2-flow-research/results/massive_run/certificates"
TOL_NUMERICAL = 1e-7


def oriented_incidence_from_edges(n_nodes: int, edges: list[tuple[int, int]]) -> np.ndarray:
    b = np.zeros((n_nodes, len(edges)))
    for j, (u, v) in enumerate(edges):
        b[u, j] = 1.0
        b[v, j] = -1.0
    return b


def main() -> None:
    paths = sorted(glob.glob(f"{CERT_DIR}/*.npz"))
    rows = []
    worst_cons = 0.0
    worst_norm = 0.0
    n_constructive = 0
    n_numerical = 0
    failures = []
    for path in paths:
        data = np.load(path, allow_pickle=True)
        graph6 = str(data["graph6"][0])
        graph = nx.from_graph6_bytes(graph6.encode("ascii"))
        x = np.asarray(data["X"], dtype=float)
        stored_edges = [tuple(int(a) for a in e) for e in data["edges"].tolist()]

        cubic = all(d == 3 for _, d in graph.degree())
        connected = nx.is_connected(graph)
        bridgeless = len(list(nx.bridges(graph))) == 0
        simple = not graph.number_of_selfloops() if hasattr(graph, "number_of_selfloops") else nx.number_of_selfloops(graph) == 0
        edge_set_ok = {frozenset(e) for e in stored_edges} == {frozenset(e) for e in graph.edges()}

        b = oriented_incidence_from_edges(graph.number_of_nodes(), stored_edges)
        cons = float(np.max(np.abs(b @ x))) if x.size else float("inf")
        norms = np.linalg.norm(x, axis=1)
        norm_res = float(np.max(np.abs(norms - 1.0)))
        q = x @ x.T
        eigs = np.linalg.eigvalsh(q)
        gram_rank = int(np.sum(eigs > 1e-9 * max(1.0, float(eigs[-1]))))
        min_eig = float(eigs[0])

        inv_sqrt2 = 1.0 / math.sqrt(2.0)
        allowed = np.array([0.0, inv_sqrt2, -inv_sqrt2])
        is_constructive = bool(
            np.all(np.min(np.abs(x[:, :, None] - allowed[None, None, :]), axis=2) < 1e-12)
        )
        if is_constructive:
            n_constructive += 1
        else:
            n_numerical += 1

        ok = (
            cubic
            and connected
            and bridgeless
            and edge_set_ok
            and cons <= TOL_NUMERICAL
            and norm_res <= TOL_NUMERICAL
            and gram_rank <= 3
            and min_eig >= -1e-9
        )
        if not ok:
            failures.append(
                {
                    "file": path.rsplit("/", 1)[-1],
                    "cubic": cubic,
                    "connected": connected,
                    "bridgeless": bridgeless,
                    "edge_set_ok": edge_set_ok,
                    "conservation": cons,
                    "norm_residual": norm_res,
                    "gram_rank": gram_rank,
                }
            )
        worst_cons = max(worst_cons, cons)
        worst_norm = max(worst_norm, norm_res)
        rows.append((path.rsplit("/", 1)[-1], graph.number_of_nodes(), cons, norm_res, gram_rank, is_constructive))

    summary = {
        "total_certificates": len(paths),
        "valid": len(paths) - len(failures),
        "failures": failures,
        "constructive_certificates": n_constructive,
        "numerical_certificates": n_numerical,
        "max_conservation_residual": worst_cons,
        "max_unit_norm_residual": worst_norm,
    }
    print(json.dumps(summary, indent=2))
    with open("/home/claude/work/independent_check_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    # Detail for the eight numerical certificates.
    print("\nNumerical (non-constructive) certificates:")
    for name, n, cons, norm_res, rank, constructive in rows:
        if not constructive:
            print(f"  {name}: n={n}, conservation={cons:.3e}, norm_res={norm_res:.3e}, gram_rank={rank}")


if __name__ == "__main__":
    main()
