"""Solve the pure Z_n-equivariant six-template ansatz for flower snarks.

The script produces deterministic numerical candidates for every odd n in a
requested range.  It stores the graph through the explicit edge list and a
stable graph6 string, avoiding the node-order serialization defect present in
the earlier prototype.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import networkx as nx
import numpy as np
from scipy.optimize import least_squares

from flower_common import (
    canonical_relabelled,
    edge_action,
    edge_orbits,
    incidence_matrix,
    rotation_z,
    stable_graph6,
)


def make_system(n: int, theta: float):
    graph, edges, tau_one = canonical_relabelled(n)
    tau_two = {vertex: tau_one[tau_one[vertex]] for vertex in tau_one}
    pi, signs = edge_action(edges, tau_two)
    orbits = edge_orbits(edges, pi, signs)
    if sorted(len(orbit) for orbit in orbits) != [n] * 6:
        raise AssertionError("The pure Z_n action must have six length-n edge orbits")

    rotation = rotation_z(theta)
    powers = [np.linalg.matrix_power(rotation, power) for power in range(n)]
    incidence = incidence_matrix(graph.number_of_nodes(), edges).astype(float)

    def build_flow(template_vector: np.ndarray) -> np.ndarray:
        templates = template_vector.reshape(6, 3)
        flow = np.empty((len(edges), 3), dtype=float)
        for orbit_index, orbit in enumerate(orbits):
            for edge_index, power, sign in orbit:
                flow[edge_index] = sign * powers[power] @ templates[orbit_index]
        return flow

    def residual(template_vector: np.ndarray) -> np.ndarray:
        flow = build_flow(template_vector)
        conservation = (incidence @ flow).ravel()
        unit_norms = np.einsum("ij,ij->i", flow, flow) - 1.0
        return np.concatenate([conservation, unit_norms])

    return graph, edges, residual, build_flow, incidence


def solve_case(
    n: int,
    branch_k: int = 1,
    warm_start: np.ndarray | None = None,
    random_starts: int = 40,
    seed: int = 20260719,
) -> dict:
    theta = 2.0 * np.pi * branch_k / n
    graph, edges, residual, build_flow, incidence = make_system(n, theta)
    rng = np.random.default_rng(seed + 1009 * n + branch_k)
    initial_points: list[np.ndarray] = []
    if warm_start is not None:
        initial_points.append(np.asarray(warm_start, dtype=float))
    initial_points.extend(rng.normal(size=18) for _ in range(random_starts))

    best_residual = np.inf
    best_templates: np.ndarray | None = None
    for initial in initial_points:
        solution = least_squares(
            residual,
            initial,
            method="lm",
            xtol=1e-14,
            ftol=1e-14,
            gtol=1e-14,
            max_nfev=1200,
        )
        current = float(np.max(np.abs(solution.fun)))
        if current < best_residual:
            best_residual = current
            best_templates = solution.x.copy()
        if best_residual < 5e-14:
            break
    if best_templates is None:
        raise RuntimeError(f"No numerical candidate was produced for J_{n}")

    flow = build_flow(best_templates)
    return {
        "n": n,
        "branch_k": branch_k,
        "theta": theta,
        "graph": graph,
        "edges": edges,
        "templates": best_templates,
        "flow": flow,
        "max_system_residual": best_residual,
        "kirchhoff_residual": float(np.max(np.abs(incidence @ flow))),
        "unit_norm_residual": float(
            np.max(np.abs(np.linalg.norm(flow, axis=1) - 1.0))
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--min-n", type=int, default=5)
    parser.add_argument("--max-n", type=int, default=41)
    parser.add_argument("--branch-k", type=int, default=1)
    parser.add_argument("--random-starts", type=int, default=40)
    parser.add_argument("--output-dir", type=Path, default=Path("data/equivariant_flows"))
    parser.add_argument("--summary", type=Path, default=Path("results/zn_branch.json"))
    args = parser.parse_args()

    ns = [n for n in range(args.min_n, args.max_n + 1) if n >= 5 and n % 2 == 1]
    args.output_dir.mkdir(parents=True, exist_ok=True)
    results = []
    warm_start = None
    for n in ns:
        solved = solve_case(
            n,
            branch_k=args.branch_k,
            warm_start=warm_start,
            random_starts=args.random_starts,
        )
        graph = solved.pop("graph")
        edges = solved.pop("edges")
        templates = solved.pop("templates")
        flow = solved.pop("flow")
        output = args.output_dir / f"flower_J{n}_zn_k{args.branch_k}.npz"
        np.savez_compressed(
            output,
            graph6=np.array([stable_graph6(graph)]),
            node_order=np.array(sorted(graph.nodes()), dtype=np.int64),
            edges=np.asarray(edges, dtype=np.int64),
            X=flow,
            templates=templates,
            n=np.array([n], dtype=np.int64),
            branch_k=np.array([args.branch_k], dtype=np.int64),
        )
        solved["file"] = str(output)
        solved["solved"] = bool(solved["max_system_residual"] < 1e-10)
        results.append(solved)
        warm_start = templates
        print(
            f"J_{n}: residual={solved['max_system_residual']:.3e}, "
            f"Kirchhoff={solved['kirchhoff_residual']:.3e}, "
            f"norm={solved['unit_norm_residual']:.3e}"
        )

    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"Saved {args.summary}")


if __name__ == "__main__":
    main()
