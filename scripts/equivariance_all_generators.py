"""Test every generator of the order-2n cyclic symmetry on stored certificates.

The implementation corrects two reproducibility gaps in the earlier script:
1. every exponent coprime to 2n is evaluated, not only the one-block shift;
2. cyclic averaging uses the correct row-vector pullback by R**k.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

import networkx as nx
import numpy as np
from networkx.algorithms.isomorphism import GraphMatcher

from flower_common import (
    all_cyclic_generators,
    canonical_flower,
    edge_action,
    edge_orbits,
    incidence_matrix,
    mapping_order,
    permutation_power,
    proper_procrustes,
    rotation_z,
)


def load_certificate(path: Path) -> tuple[nx.Graph, list[tuple[int, int]], np.ndarray]:
    """Load a certificate and reconstruct the graph from its edge list."""
    data = np.load(path, allow_pickle=True)
    edges = [tuple(int(value) for value in edge) for edge in data["edges"].tolist()]
    graph = nx.Graph()
    graph.add_edges_from(edges)
    flow = np.asarray(data["X"], dtype=float)
    if flow.shape != (len(edges), 3):
        raise ValueError(f"Unexpected flow shape in {path}: {flow.shape}")
    return graph, edges, flow


def locate_certificate(directory: Path, n: int) -> Path:
    matches = sorted(directory.glob(f"*flower_J{n}.npz"))
    if len(matches) != 1:
        raise FileNotFoundError(f"Expected one J_{n} certificate, found {matches}")
    return matches[0]


def transport_shift(graph: nx.Graph, n: int) -> dict[int, int]:
    canonical, sigma = canonical_flower(n)
    matcher = GraphMatcher(canonical, graph)
    if not matcher.is_isomorphic():
        raise ValueError(f"Stored graph is not isomorphic to flower snark J_{n}")
    phi = matcher.mapping
    return {phi[v]: phi[sigma[v]] for v in canonical.nodes()}


def cyclic_average(
    flow: np.ndarray,
    pi: np.ndarray,
    signs: np.ndarray,
    rotation: np.ndarray,
    order: int,
) -> np.ndarray:
    """Average the pullbacks R^{-k} tau^k(flow) in row-vector convention."""
    average = np.zeros_like(flow)
    current_pi = np.arange(len(flow), dtype=np.int64)
    current_sign = np.ones(len(flow), dtype=np.int8)
    rotation_power = np.eye(3)
    for _ in range(order):
        average += current_sign[:, None] * flow[current_pi] @ rotation_power
        current_sign = current_sign * signs[current_pi]
        current_pi = pi[current_pi]
        rotation_power = rotation_power @ rotation
    average /= float(order)
    if not np.array_equal(current_pi, np.arange(len(flow))):
        raise AssertionError("The requested averaging order is incorrect")
    return average


def analyse_generator(
    graph: nx.Graph,
    edges: list[tuple[int, int]],
    flow: np.ndarray,
    base_shift: dict[int, int],
    n: int,
    exponent: int,
) -> dict[str, Any]:
    tau = permutation_power(base_shift, exponent)
    order = mapping_order(tau)
    pi, signs = edge_action(edges, tau)
    image = signs[:, None] * flow[pi]
    rotation = proper_procrustes(flow, image)
    residuals = np.linalg.norm(image - flow @ rotation.T, axis=1)
    average = cyclic_average(flow, pi, signs, rotation, order)
    incidence = incidence_matrix(graph.number_of_nodes(), edges)
    angle = float(np.arccos(np.clip((np.trace(rotation) - 1.0) / 2.0, -1.0, 1.0)))
    return {
        "graph": f"flower_J{n}",
        "n": n,
        "generator_exponent": exponent,
        "group_order": order,
        "rotation_determinant": float(np.linalg.det(rotation)),
        "rotation_angle": angle,
        "equivariance_residual_max": float(np.max(residuals)),
        "equivariance_residual_rms": float(np.sqrt(np.mean(residuals**2))),
        "averaged_norm_min": float(np.min(np.linalg.norm(average, axis=1))),
        "averaged_norm_max": float(np.max(np.linalg.norm(average, axis=1))),
        "averaged_norm_deficit_max": float(
            np.max(np.abs(np.linalg.norm(average, axis=1) - 1.0))
        ),
        "averaged_kirchhoff_residual": float(np.max(np.abs(incidence @ average))),
        "distance_original_to_average_max": float(
            np.max(np.linalg.norm(flow - average, axis=1))
        ),
    }


def synthetic_validation(n: int) -> dict[str, float]:
    """Validate edge transport, Procrustes recovery, and averaging exactly."""
    canonical, sigma = canonical_flower(n)
    nodes = sorted(canonical.nodes(), key=lambda value: (value[0], value[1]))
    relabel = {value: index for index, value in enumerate(nodes)}
    graph = nx.relabel_nodes(canonical, relabel)
    edges = sorted((min(u, v), max(u, v)) for u, v in graph.edges())
    tau = {relabel[v]: relabel[sigma[v]] for v in nodes}
    pi, signs = edge_action(edges, tau)
    orbits = edge_orbits(edges, pi, signs)
    rotation = rotation_z(2.0 * np.pi / (2 * n))
    rng = np.random.default_rng(20260719 + n)
    flow = np.empty((len(edges), 3), dtype=float)
    for orbit_index, orbit in enumerate(orbits):
        if len(orbit) == n:
            template = np.array([0.0, 0.0, 1.0 if orbit_index % 2 == 0 else -1.0])
        else:
            template = rng.normal(size=3)
            template /= np.linalg.norm(template)
        power = np.eye(3)
        for edge_index, _, sign in orbit:
            flow[edge_index] = sign * power @ template
            power = rotation @ power
    worst_rotation_error = 0.0
    worst_residual = 0.0
    worst_average_error = 0.0
    for exponent in all_cyclic_generators(2 * n):
        tau_power = permutation_power(tau, exponent)
        pi_power, sign_power = edge_action(edges, tau_power)
        image = sign_power[:, None] * flow[pi_power]
        recovered = proper_procrustes(flow, image)
        expected = np.linalg.matrix_power(rotation, exponent)
        worst_rotation_error = max(worst_rotation_error, float(np.linalg.norm(recovered - expected)))
        worst_residual = max(
            worst_residual,
            float(np.max(np.linalg.norm(image - flow @ recovered.T, axis=1))),
        )
        average = cyclic_average(flow, pi_power, sign_power, recovered, 2 * n)
        worst_average_error = max(
            worst_average_error,
            float(np.max(np.linalg.norm(average - flow, axis=1))),
        )
    return {
        "rotation_error": worst_rotation_error,
        "equivariance_residual": worst_residual,
        "average_error": worst_average_error,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cert-dir", type=Path, default=Path("results/massive_run/certificates"))
    parser.add_argument("--output-json", type=Path, default=Path("results/equivariance_all_generators.json"))
    parser.add_argument("--output-csv", type=Path, default=Path("results/equivariance_all_generators.csv"))
    parser.add_argument("--n", type=int, nargs="*", default=[5, 7, 9, 11, 13])
    args = parser.parse_args()

    validation = {str(n): synthetic_validation(n) for n in args.n}
    for n, values in validation.items():
        if max(values.values()) > 1e-12:
            raise RuntimeError(f"Synthetic validation failed for J_{n}: {values}")

    results: list[dict[str, Any]] = []
    for n in args.n:
        graph, edges, flow = load_certificate(locate_certificate(args.cert_dir, n))
        shift = transport_shift(graph, n)
        for exponent in all_cyclic_generators(2 * n):
            results.append(analyse_generator(graph, edges, flow, shift, n, exponent))

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    with args.output_json.open("w", encoding="utf-8") as handle:
        json.dump({"synthetic_validation": validation, "results": results}, handle, indent=2)
    with args.output_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(results[0]))
        writer.writeheader()
        writer.writerows(results)

    print(f"Validated {sum(len(all_cyclic_generators(2*n)) for n in args.n)} generators")
    print(f"JSON: {args.output_json}")
    print(f"CSV:  {args.output_csv}")


if __name__ == "__main__":
    main()
