"""Shared graph, symmetry, and linear-algebra utilities for flower snarks."""

from __future__ import annotations

from dataclasses import dataclass
from math import gcd
from typing import Dict, Iterable, List, Mapping, Sequence, Tuple

import networkx as nx
import numpy as np

Vertex = tuple[str, int]
Edge = tuple[int, int]


def canonical_flower(n: int) -> tuple[nx.Graph, dict[Vertex, Vertex]]:
    """Return the canonical flower snark J_n and the order-2n block shift.

    The definition is valid for odd n >= 5.  The graph has hubs c_i, outer
    vertices t_i, and a single 2n-cycle w_j representing the two strands and
    their Moebius seam.
    """
    if n < 5 or n % 2 == 0:
        raise ValueError("Flower snarks require odd n >= 5")
    graph = nx.Graph()
    for i in range(n):
        graph.add_edge(("c", i), ("t", i))
        graph.add_edge(("c", i), ("w", i))
        graph.add_edge(("c", i), ("w", n + i))
        graph.add_edge(("t", i), ("t", (i + 1) % n))
    for j in range(2 * n):
        graph.add_edge(("w", j), ("w", (j + 1) % (2 * n)))

    sigma: dict[Vertex, Vertex] = {}
    for i in range(n):
        sigma[("c", i)] = ("c", (i + 1) % n)
        sigma[("t", i)] = ("t", (i + 1) % n)
    for j in range(2 * n):
        sigma[("w", j)] = ("w", (j + 1) % (2 * n))
    return graph, sigma


def canonical_relabelled(n: int) -> tuple[nx.Graph, list[Edge], dict[int, int]]:
    """Return J_n with stable integer labels, sorted edges, and the shift."""
    graph, sigma = canonical_flower(n)
    nodes = sorted(graph.nodes(), key=lambda v: (v[0], v[1]))
    relabel = {vertex: index for index, vertex in enumerate(nodes)}
    relabelled = nx.Graph()
    relabelled.add_nodes_from(range(len(nodes)))
    relabelled.add_edges_from((relabel[u], relabel[v]) for u, v in graph.edges())
    edges = sorted((min(u, v), max(u, v)) for u, v in relabelled.edges())
    tau = {relabel[v]: relabel[sigma[v]] for v in nodes}
    return relabelled, edges, tau


def stable_graph6(graph: nx.Graph) -> str:
    """Serialize a graph6 string with a deterministic numeric node order."""
    nodes = sorted(graph.nodes())
    mapping = {v: i for i, v in enumerate(nodes)}
    stable = nx.Graph()
    stable.add_nodes_from(range(len(nodes)))
    stable.add_edges_from((mapping[u], mapping[v]) for u, v in graph.edges())
    return nx.to_graph6_bytes(stable, header=False).decode("ascii").strip()


def permutation_power(perm: Mapping, exponent: int) -> dict:
    """Return perm**exponent for a finite permutation represented by a dict."""
    if exponent < 0:
        inverse = {value: key for key, value in perm.items()}
        return permutation_power(inverse, -exponent)
    result = {key: key for key in perm}
    base = dict(perm)
    k = exponent
    while k:
        if k & 1:
            result = {key: base[result[key]] for key in result}
        base = {key: base[base[key]] for key in base}
        k >>= 1
    return result


def mapping_order(perm: Mapping) -> int:
    """Compute the exact order of a finite permutation."""
    identity = {key: key for key in perm}
    current = dict(identity)
    for order in range(1, 100000):
        current = {key: perm[current[key]] for key in current}
        if current == identity:
            return order
    raise RuntimeError("Permutation order exceeded the safety limit")


def edge_action(edges: Sequence[Edge], vertex_perm: Mapping[int, int]) -> tuple[np.ndarray, np.ndarray]:
    """Lift a vertex automorphism to an oriented edge permutation and signs."""
    index = {edge: idx for idx, edge in enumerate(edges)}
    pi = np.empty(len(edges), dtype=np.int64)
    signs = np.empty(len(edges), dtype=np.int8)
    for idx, (u, v) in enumerate(edges):
        image = (vertex_perm[u], vertex_perm[v])
        if image in index:
            pi[idx] = index[image]
            signs[idx] = 1
        elif (image[1], image[0]) in index:
            pi[idx] = index[(image[1], image[0])]
            signs[idx] = -1
        else:
            raise ValueError(f"Automorphism does not preserve edge {(u, v)}")
    return pi, signs


def edge_orbits(edges: Sequence[Edge], pi: np.ndarray, signs: np.ndarray) -> list[list[tuple[int, int, int]]]:
    """Decompose an oriented edge action into signed cyclic orbits."""
    seen = np.zeros(len(edges), dtype=bool)
    orbits: list[list[tuple[int, int, int]]] = []
    for representative in range(len(edges)):
        if seen[representative]:
            continue
        orbit: list[tuple[int, int, int]] = []
        current = representative
        cumulative_sign = 1
        power = 0
        while not seen[current]:
            seen[current] = True
            orbit.append((current, power, cumulative_sign))
            cumulative_sign *= int(signs[current])
            current = int(pi[current])
            power += 1
        if current != representative or cumulative_sign != 1:
            raise ValueError("Inconsistent signed edge orbit")
        orbits.append(orbit)
    return orbits


def incidence_matrix(node_count: int, edges: Sequence[Edge]) -> np.ndarray:
    """Return the oriented incidence matrix using +1 at tail and -1 at head."""
    matrix = np.zeros((node_count, len(edges)), dtype=np.int64)
    for index, (u, v) in enumerate(edges):
        matrix[u, index] = 1
        matrix[v, index] = -1
    return matrix


def proper_procrustes(source: np.ndarray, target: np.ndarray) -> np.ndarray:
    """Return the best proper rotation R with target approximately R*source."""
    covariance = target.T @ source
    left, _, right_t = np.linalg.svd(covariance)
    correction = np.eye(3)
    correction[-1, -1] = np.sign(np.linalg.det(left @ right_t))
    return left @ correction @ right_t


def all_cyclic_generators(order: int) -> list[int]:
    """Return all exponents generating a cyclic group of the given order."""
    return [power for power in range(1, order) if gcd(power, order) == 1]


def rotation_z(theta: float) -> np.ndarray:
    """Return the right-handed rotation about the z-axis."""
    cosine = float(np.cos(theta))
    sine = float(np.sin(theta))
    return np.array(
        [[cosine, -sine, 0.0], [sine, cosine, 0.0], [0.0, 0.0, 1.0]],
        dtype=float,
    )
