#!/usr/bin/env python3
"""
Reproducible computational laboratory for the S^2-flow conjecture.

The conjecture states that every bridgeless cubic graph admits an assignment of
unit vectors in R^3 to oriented edges such that the vector-valued Kirchhoff law
holds at every vertex.

This script does NOT prove the conjecture. It provides reproducible numerical
and algebraic checks for finite graph instances:

1. Graph validation: connected, cubic, bridgeless, girth, edge connectivity.
2. Exact 3-edge-colorability search for small graphs.
3. Cycle-space formulation X = ZY with exact conservation BX = 0.
4. Direct product-of-spheres formulation with exact unit norms.
5. Rank-3 Gram/PSD verification for every numerical candidate.
6. Jacobian regularity checks and the three global rotation null directions.
7. Optional SDP relaxation in cycle-space coordinates through CVXPY.
8. Cycle-cone LP construction of a feasible high-rank PSD matrix.
9. Exact real-linear obstruction to a universal seven-vector F_2^3 palette.
10. Dimension sweeps and deterministic random cubic graph experiments.

Core dependencies:
    numpy, scipy, networkx

Optional dependencies:
    matplotlib  - plots
    cvxpy      - SDP relaxation

Recommended commands:

    python s2_flow_repro.py --suite core --run-direct --run-edge-coloring \
        --run-cycle-cone --plot

    python s2_flow_repro.py --suite reproduce --dimensions 2 3 4 7 \
        --cycle-restarts 27 --run-direct --run-edge-coloring \
        --run-cycle-cone --plot --output-dir s2_flow_results

    python s2_flow_repro.py --suite none --graphs petersen flower:5 \
        gpg:9:2 random:20:1 --dimensions 3 --run-direct

The output directory contains JSON reports, NPZ numerical certificates,
graph6 files, CSV summaries, restart histories, and optional plots.

References encoded by the experiments:
    - The S^2-flow equations: BX = 0 and ||X_e||_2 = 1.
    - Rank-3 PSD equivalence: Q = XX^T, Q >= 0, rank(Q) <= 3,
      diag(Q) = 1, and BQ = 0.
    - Cycle-space form: X = ZY and ||z_e^T Y||_2 = 1.
    - Flower snark construction: n claws, one n-cycle, and one 2n-cycle.

All numerical results are finite-instance evidence only. Failure of a local
optimizer is inconclusive; success produces a directly checkable numerical
candidate, not a universal proof.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib
import json
import math
import os
import platform
import re
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable, Iterator, Sequence

import networkx as nx
import numpy as np
import scipy
from numpy.typing import NDArray
from scipy.linalg import null_space
from scipy.optimize import least_squares, linprog

FloatArray = NDArray[np.float64]
IntArray = NDArray[np.int64]


@dataclass(frozen=True)
class SolverConfig:
    """Numerical solver configuration."""

    ambient_dim: int = 3
    restarts: int = 27
    max_nfev: int = 20_000
    tolerance: float = 1e-8
    seed: int = 20260717
    verbose: int = 0


@dataclass
class GraphDiagnostics:
    """Structural graph diagnostics."""

    name: str
    vertices: int
    edges: int
    connected: bool
    simple: bool
    cubic: bool
    bridgeless: bool
    bridges: list[list[int]]
    edge_connectivity: int | None
    girth: int | None
    cycle_rank: int
    perfect_matching_size: int | None
    perfect_matching_is_perfect: bool | None
    two_factor_cycle_lengths: list[int]
    graph_sha256: str


@dataclass
class EdgeColoringResult:
    """Exact three-edge-colorability search result."""

    status: str
    colorable: bool | None
    elapsed_seconds: float
    explored_nodes: int
    coloring: list[int] | None


@dataclass
class FlowMetrics:
    """Numerical and algebraic checks for a flow candidate."""

    found: bool
    ambient_dim: int
    max_conservation_residual: float
    l2_conservation_residual: float
    max_unit_norm_residual: float
    l2_unit_norm_residual: float
    max_local_dot_residual: float | None
    gram_min_eigenvalue: float
    gram_numerical_rank: int
    gram_rank_tolerance: float
    max_gram_diagonal_residual: float
    max_bq_residual: float
    cycle_jacobian_rank: int | None
    cycle_jacobian_rows: int | None
    cycle_jacobian_columns: int | None
    cycle_jacobian_smallest_singular_value: float | None
    tangent_balance_rank: int | None
    tangent_balance_rows: int | None
    tangent_balance_columns: int | None
    tangent_balance_smallest_singular_value: float | None
    global_rotation_null_residual: float | None


@dataclass
class FlowSolution:
    """A numerical flow candidate and its solver metadata."""

    method: str
    graph_name: str
    ambient_dim: int
    X: FloatArray
    Y: FloatArray | None
    metrics: FlowMetrics
    elapsed_seconds: float
    best_cost: float
    best_optimality: float
    best_status: int
    best_message: str
    best_nfev: int
    restart_costs: list[float] = field(default_factory=list)
    successful_restarts: int = 0


@dataclass
class CycleConeResult:
    """Cycle-cone LP result and high-rank PSD certificate."""

    attempted: bool
    success: bool
    truncated_cycle_enumeration: bool
    cycle_count: int
    active_cycle_count: int
    elapsed_seconds: float
    max_coverage_residual: float | None
    max_bq_residual: float | None
    min_q_eigenvalue: float | None
    q_numerical_rank: int | None
    message: str
    Q: FloatArray | None = None
    weights: FloatArray | None = None
    cycles: list[list[int]] | None = None


@dataclass
class SDPResult:
    """Optional CVXPY SDP relaxation result."""

    attempted: bool
    available: bool
    success: bool
    status: str
    solver: str | None
    elapsed_seconds: float
    objective_value: float | None
    max_measurement_residual: float | None
    min_eigenvalue: float | None
    numerical_rank: int | None
    eigenvalues_descending: list[float]
    H: FloatArray | None = None
    rank_d_seed: FloatArray | None = None


class ColoringTimeout(RuntimeError):
    """Raised when exact edge-coloring exceeds the configured timeout."""


class CycleEnumerationLimit(RuntimeError):
    """Raised internally when the requested cycle cap is reached."""


def json_default(value: Any) -> Any:
    """Convert NumPy and pathlib values to JSON-compatible objects."""

    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, set):
        return sorted(value)
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def write_json(path: Path, payload: Any) -> None:
    """Write deterministic, human-readable JSON."""

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as stream:
        json.dump(payload, stream, ensure_ascii=False, indent=2, sort_keys=True, default=json_default)
        stream.write("\n")
    temporary.replace(path)


def safe_name(value: str) -> str:
    """Create a filesystem-safe identifier."""

    normalized = re.sub(r"[^A-Za-z0-9_.-]+", "_", value.strip())
    return normalized.strip("._") or "graph"


def package_version(package_name: str) -> str | None:
    """Return an installed package version without importing optional packages."""

    try:
        module = importlib.import_module(package_name)
    except Exception:
        return None
    return str(getattr(module, "__version__", "unknown"))


def environment_report() -> dict[str, Any]:
    """Capture the environment required for reproducibility."""

    return {
        "python": sys.version,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "networkx": nx.__version__,
        "matplotlib": package_version("matplotlib"),
        "cvxpy": package_version("cvxpy"),
        "command": sys.argv,
    }


def relabel_graph_to_integers(graph: nx.Graph) -> tuple[nx.Graph, dict[int, Any]]:
    """Relabel an undirected simple graph deterministically to 0..n-1."""

    if graph.is_directed():
        raise ValueError("Only undirected graphs are supported")
    if isinstance(graph, (nx.MultiGraph, nx.MultiDiGraph)):
        raise ValueError("This implementation currently supports simple graphs only")

    ordered_nodes = sorted(graph.nodes(), key=lambda node: (type(node).__name__, repr(node)))
    forward = {node: index for index, node in enumerate(ordered_nodes)}
    reverse = {index: node for node, index in forward.items()}
    relabeled = nx.relabel_nodes(graph, forward, copy=True)
    relabeled = nx.Graph(relabeled)
    relabeled.remove_edges_from(nx.selfloop_edges(relabeled))
    return relabeled, reverse


def flower_snark(order: int) -> nx.Graph:
    """Construct the Isaacs flower snark J_order for odd order >= 5."""

    if order < 5 or order % 2 == 0:
        raise ValueError("Flower snark order must be odd and at least 5")

    graph = nx.Graph()
    for index in range(order):
        center = ("a", index)
        leaves = [("b", index), ("c", index), ("d", index)]
        graph.add_edges_from((center, leaf) for leaf in leaves)

    for index in range(order):
        graph.add_edge(("b", index), ("b", (index + 1) % order))

    long_cycle: list[tuple[str, int]] = [
        *(('c', index) for index in range(order)),
        *(('d', index) for index in range(order)),
    ]
    for index, node in enumerate(long_cycle):
        graph.add_edge(node, long_cycle[(index + 1) % len(long_cycle)])

    relabeled, _ = relabel_graph_to_integers(graph)
    return relabeled


def deterministic_random_cubic_graph(
    vertex_count: int,
    seed: int,
    max_attempts: int = 10_000,
) -> nx.Graph:
    """Generate a connected bridgeless simple cubic graph deterministically."""

    if vertex_count < 4 or vertex_count % 2 != 0:
        raise ValueError("A cubic graph requires an even vertex count of at least 4")

    random_generator = np.random.default_rng(seed)
    for _ in range(max_attempts):
        graph_seed = int(random_generator.integers(0, 2**31 - 1))
        graph = nx.random_regular_graph(3, vertex_count, seed=graph_seed)
        if nx.is_connected(graph) and not list(nx.bridges(graph)):
            relabeled, _ = relabel_graph_to_integers(graph)
            return relabeled
    raise RuntimeError(
        f"Could not generate a connected bridgeless cubic graph with {vertex_count} vertices"
    )


def load_graph_spec(specification: str, global_seed: int) -> tuple[str, nx.Graph]:
    """Load or generate a graph from a compact command-line specification."""

    normalized = specification.strip()
    lowered = normalized.lower()

    if lowered == "petersen":
        return "petersen", nx.petersen_graph()
    if lowered == "k4":
        return "k4", nx.complete_graph(4)
    if lowered in {"k33", "k3,3"}:
        return "k3_3", nx.complete_bipartite_graph(3, 3)
    if lowered == "tutte":
        return "tutte", nx.tutte_graph()
    if lowered.startswith("flower:"):
        order = int(lowered.split(":", maxsplit=1)[1])
        return f"flower_j{order}", flower_snark(order)
    if lowered.startswith("gpg:"):
        parts = lowered.split(":")
        if len(parts) != 3:
            raise ValueError("Generalized Petersen syntax is gpg:n:k")
        n_value, k_value = int(parts[1]), int(parts[2])
        return f"gpg_{n_value}_{k_value}", nx.generalized_petersen_graph(n_value, k_value)
    if lowered.startswith("random:"):
        parts = lowered.split(":")
        if len(parts) not in {2, 3}:
            raise ValueError("Random graph syntax is random:vertices[:instance]")
        vertices = int(parts[1])
        instance = int(parts[2]) if len(parts) == 3 else 0
        seed = global_seed + 1_000_003 * vertices + 9_973 * instance
        graph = deterministic_random_cubic_graph(vertices, seed)
        return f"random_cubic_n{vertices}_i{instance}", graph
    if lowered.startswith("g6:"):
        path = Path(normalized[3:]).expanduser().resolve()
        graph = nx.read_graph6(path)
        relabeled, _ = relabel_graph_to_integers(graph)
        return safe_name(path.stem), relabeled
    if lowered.startswith("edgelist:"):
        path = Path(normalized[len("edgelist:"):]).expanduser().resolve()
        graph = nx.read_edgelist(path, nodetype=str)
        relabeled, _ = relabel_graph_to_integers(graph)
        return safe_name(path.stem), relabeled
    if lowered.startswith("graphml:"):
        path = Path(normalized[len("graphml:"):]).expanduser().resolve()
        graph = nx.read_graphml(path)
        relabeled, _ = relabel_graph_to_integers(graph)
        return safe_name(path.stem), relabeled

    raise ValueError(f"Unknown graph specification: {specification}")


def graph_suite(name: str, seed: int) -> list[tuple[str, nx.Graph]]:
    """Build a deterministic graph suite."""

    if name == "none":
        return []
    if name == "core":
        specifications = [
            "k4",
            "k33",
            "petersen",
            "flower:5",
            "random:10:0",
            "random:16:0",
        ]
    elif name == "reproduce":
        specifications = ["petersen"]
        for vertex_count in (10, 16, 20, 24):
            for instance in range(3):
                specifications.append(f"random:{vertex_count}:{instance}")
    else:
        raise ValueError(f"Unknown suite: {name}")

    return [load_graph_spec(specification, seed) for specification in specifications]


def graph6_sha256(graph: nx.Graph) -> str:
    """Hash a canonical graph6 representation."""

    payload = nx.to_graph6_bytes(graph, header=False)
    return hashlib.sha256(payload).hexdigest()


def shortest_cycle_length(graph: nx.Graph) -> int | None:
    """Compute the girth of a simple undirected graph."""

    best = math.inf
    for source in graph.nodes():
        distances = {source: 0}
        parent = {source: None}
        queue = [source]
        cursor = 0
        while cursor < len(queue):
            vertex = queue[cursor]
            cursor += 1
            for neighbor in graph.neighbors(vertex):
                if neighbor not in distances:
                    distances[neighbor] = distances[vertex] + 1
                    parent[neighbor] = vertex
                    queue.append(neighbor)
                elif parent[vertex] != neighbor:
                    cycle_length = distances[vertex] + distances[neighbor] + 1
                    best = min(best, cycle_length)
    return None if math.isinf(best) else int(best)


def perfect_matching_diagnostics(graph: nx.Graph) -> tuple[int | None, bool | None, list[int]]:
    """Find one maximum matching and inspect the complementary 2-factor."""

    if graph.number_of_nodes() == 0:
        return 0, True, []
    matching = nx.max_weight_matching(graph, maxcardinality=True)
    matching_size = len(matching)
    is_perfect = matching_size * 2 == graph.number_of_nodes()
    cycle_lengths: list[int] = []
    if is_perfect and all(degree == 3 for _, degree in graph.degree()):
        complement = graph.copy()
        complement.remove_edges_from(matching)
        if all(degree == 2 for _, degree in complement.degree()):
            cycle_lengths = sorted(len(component) for component in nx.connected_components(complement))
    return matching_size, is_perfect, cycle_lengths


def diagnose_graph(name: str, graph: nx.Graph) -> GraphDiagnostics:
    """Compute structural properties relevant to the conjecture."""

    relabeled, _ = relabel_graph_to_integers(graph)
    connected = nx.is_connected(relabeled) if relabeled.number_of_nodes() else False
    bridges = sorted([sorted(edge) for edge in nx.bridges(relabeled)]) if connected else []
    cubic = all(degree == 3 for _, degree in relabeled.degree())
    matching_size, matching_is_perfect, cycle_lengths = perfect_matching_diagnostics(relabeled)
    edge_connectivity = nx.edge_connectivity(relabeled) if connected and relabeled.number_of_nodes() > 1 else None
    cycle_rank = (
        relabeled.number_of_edges()
        - relabeled.number_of_nodes()
        + nx.number_connected_components(relabeled)
    )
    return GraphDiagnostics(
        name=name,
        vertices=relabeled.number_of_nodes(),
        edges=relabeled.number_of_edges(),
        connected=connected,
        simple=not relabeled.is_multigraph() and nx.number_of_selfloops(relabeled) == 0,
        cubic=cubic,
        bridgeless=connected and not bridges,
        bridges=bridges,
        edge_connectivity=edge_connectivity,
        girth=shortest_cycle_length(relabeled),
        cycle_rank=cycle_rank,
        perfect_matching_size=matching_size,
        perfect_matching_is_perfect=matching_is_perfect,
        two_factor_cycle_lengths=cycle_lengths,
        graph_sha256=graph6_sha256(relabeled),
    )


def oriented_incidence_matrix(graph: nx.Graph) -> tuple[FloatArray, list[tuple[int, int]]]:
    """Build a deterministic oriented incidence matrix with -1 at tail and +1 at head."""

    nodes = sorted(graph.nodes())
    if nodes != list(range(len(nodes))):
        raise ValueError("Graph nodes must be relabeled to consecutive integers")

    edges = sorted((min(u, v), max(u, v)) for u, v in graph.edges())
    incidence = np.zeros((graph.number_of_nodes(), len(edges)), dtype=np.float64)
    for edge_index, (tail, head) in enumerate(edges):
        incidence[tail, edge_index] = -1.0
        incidence[head, edge_index] = 1.0
    return incidence, edges


def matrix_numerical_rank(matrix: FloatArray, relative_tolerance: float = 1e-9) -> tuple[int, float, FloatArray]:
    """Compute numerical rank, absolute tolerance, and singular values."""

    singular_values = np.linalg.svd(matrix, compute_uv=False)
    if singular_values.size == 0:
        return 0, 0.0, singular_values
    absolute_tolerance = relative_tolerance * max(matrix.shape) * singular_values[0]
    rank = int(np.count_nonzero(singular_values > absolute_tolerance))
    return rank, float(absolute_tolerance), singular_values


def cycle_space_basis(incidence: FloatArray) -> FloatArray:
    """Return an orthonormal basis Z for ker(B), stored as columns."""

    basis = null_space(incidence, rcond=1e-12)
    expected_dimension = incidence.shape[1] - np.linalg.matrix_rank(incidence)
    if basis.shape[1] != expected_dimension:
        raise RuntimeError(
            f"Unexpected cycle-space dimension {basis.shape[1]}, expected {expected_dimension}"
        )
    if basis.size and np.max(np.abs(incidence @ basis)) > 1e-9:
        raise RuntimeError("Computed cycle basis does not satisfy BZ = 0")
    return np.asarray(basis, dtype=np.float64)


def cycle_norm_residual(flat_y: FloatArray, basis: FloatArray, ambient_dim: int) -> FloatArray:
    """Residual ||z_e^T Y||^2 - 1 in cycle-space coordinates."""

    y_matrix = flat_y.reshape(basis.shape[1], ambient_dim)
    edge_vectors = basis @ y_matrix
    return np.einsum("ij,ij->i", edge_vectors, edge_vectors) - 1.0


def cycle_norm_jacobian(flat_y: FloatArray, basis: FloatArray, ambient_dim: int) -> FloatArray:
    """Analytic Jacobian of the cycle-space unit-norm equations."""

    y_matrix = flat_y.reshape(basis.shape[1], ambient_dim)
    edge_vectors = basis @ y_matrix
    jacobian_tensor = 2.0 * basis[:, :, None] * edge_vectors[:, None, :]
    return jacobian_tensor.reshape(basis.shape[0], basis.shape[1] * ambient_dim)


def random_cycle_initialization(
    basis: FloatArray,
    ambient_dim: int,
    random_generator: np.random.Generator,
) -> FloatArray:
    """Generate a scaled random cycle-space initialization."""

    y_matrix = random_generator.normal(size=(basis.shape[1], ambient_dim))
    edge_vectors = basis @ y_matrix
    mean_squared_norm = float(np.mean(np.einsum("ij,ij->i", edge_vectors, edge_vectors)))
    if mean_squared_norm <= 1e-15:
        y_matrix[0, 0] = 1.0
        edge_vectors = basis @ y_matrix
        mean_squared_norm = float(np.mean(np.einsum("ij,ij->i", edge_vectors, edge_vectors)))
    y_matrix /= math.sqrt(mean_squared_norm)
    return y_matrix


def normalize_rows(matrix: FloatArray, epsilon: float = 1e-14) -> FloatArray:
    """Normalize each row and reject numerically zero rows."""

    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    if np.any(norms < epsilon):
        adjusted = matrix.copy()
        zero_rows = np.flatnonzero(norms[:, 0] < epsilon)
        adjusted[zero_rows, 0] = 1.0
        norms = np.linalg.norm(adjusted, axis=1, keepdims=True)
        return adjusted / norms
    return matrix / norms


def direct_balance_residual(flat_w: FloatArray, reduced_incidence: FloatArray, ambient_dim: int) -> FloatArray:
    """Kirchhoff residual for row-normalized unconstrained edge variables."""

    w_matrix = flat_w.reshape(reduced_incidence.shape[1], ambient_dim)
    edge_vectors = normalize_rows(w_matrix)
    return (reduced_incidence @ edge_vectors).ravel()


def direct_balance_jacobian(flat_w: FloatArray, reduced_incidence: FloatArray, ambient_dim: int) -> FloatArray:
    """Analytic Jacobian for the direct product-of-spheres parameterization."""

    edge_count = reduced_incidence.shape[1]
    vertex_rows = reduced_incidence.shape[0]
    w_matrix = flat_w.reshape(edge_count, ambient_dim)
    norms = np.linalg.norm(w_matrix, axis=1)
    norms = np.maximum(norms, 1e-14)
    edge_vectors = w_matrix / norms[:, None]

    jacobian = np.zeros((vertex_rows * ambient_dim, edge_count * ambient_dim), dtype=np.float64)
    identity = np.eye(ambient_dim)
    for edge_index in range(edge_count):
        projector = (identity - np.outer(edge_vectors[edge_index], edge_vectors[edge_index])) / norms[edge_index]
        incident_rows = np.flatnonzero(reduced_incidence[:, edge_index])
        for vertex_row in incident_rows:
            coefficient = reduced_incidence[vertex_row, edge_index]
            row_slice = slice(vertex_row * ambient_dim, (vertex_row + 1) * ambient_dim)
            column_slice = slice(edge_index * ambient_dim, (edge_index + 1) * ambient_dim)
            jacobian[row_slice, column_slice] = coefficient * projector
    return jacobian


def tangent_basis(unit_vector: FloatArray) -> FloatArray:
    """Construct an orthonormal basis of the tangent space at a unit vector."""

    return null_space(unit_vector.reshape(1, -1), rcond=1e-12)


def tangent_balance_jacobian(reduced_incidence: FloatArray, edge_vectors: FloatArray) -> FloatArray:
    """Jacobian of the balance map restricted to tangent directions on spheres."""

    vertex_rows = reduced_incidence.shape[0]
    edge_count, ambient_dim = edge_vectors.shape
    tangent_dim = ambient_dim - 1
    jacobian = np.zeros(
        (vertex_rows * ambient_dim, edge_count * tangent_dim),
        dtype=np.float64,
    )
    for edge_index in range(edge_count):
        tangent = tangent_basis(edge_vectors[edge_index])
        incident_rows = np.flatnonzero(reduced_incidence[:, edge_index])
        for vertex_row in incident_rows:
            coefficient = reduced_incidence[vertex_row, edge_index]
            row_slice = slice(vertex_row * ambient_dim, (vertex_row + 1) * ambient_dim)
            column_slice = slice(edge_index * tangent_dim, (edge_index + 1) * tangent_dim)
            jacobian[row_slice, column_slice] = coefficient * tangent
    return jacobian


def local_dot_residual(incidence: FloatArray, edge_vectors: FloatArray) -> float | None:
    """Check the local 120-degree condition for cubic vertices in R^3."""

    if edge_vectors.shape[1] != 3:
        return None
    maximum = 0.0
    for vertex in range(incidence.shape[0]):
        incident_edges = np.flatnonzero(incidence[vertex])
        if incident_edges.size != 3:
            return None
        signed_vectors = incidence[vertex, incident_edges, None] * edge_vectors[incident_edges]
        for first in range(3):
            for second in range(first + 1, 3):
                dot_value = float(np.dot(signed_vectors[first], signed_vectors[second]))
                maximum = max(maximum, abs(dot_value + 0.5))
    return maximum


def global_rotation_null_residual(
    basis: FloatArray,
    y_matrix: FloatArray,
    jacobian: FloatArray,
) -> float | None:
    """Check the three infinitesimal global rotations in ambient dimension three."""

    if y_matrix.shape[1] != 3:
        return None
    generators = [
        np.array([[0.0, -1.0, 0.0], [1.0, 0.0, 0.0], [0.0, 0.0, 0.0]]),
        np.array([[0.0, 0.0, -1.0], [0.0, 0.0, 0.0], [1.0, 0.0, 0.0]]),
        np.array([[0.0, 0.0, 0.0], [0.0, 0.0, -1.0], [0.0, 1.0, 0.0]]),
    ]
    residuals = []
    for generator in generators:
        direction = (y_matrix @ generator).ravel()
        residuals.append(float(np.linalg.norm(jacobian @ direction)))
    return max(residuals)


def evaluate_flow(
    incidence: FloatArray,
    basis: FloatArray,
    edge_vectors: FloatArray,
    y_matrix: FloatArray | None,
    tolerance: float,
) -> FlowMetrics:
    """Evaluate every directly checkable condition for a flow candidate."""

    conservation = incidence @ edge_vectors
    norm_residual = np.einsum("ij,ij->i", edge_vectors, edge_vectors) - 1.0
    gram = edge_vectors @ edge_vectors.T
    gram_eigenvalues = np.linalg.eigvalsh((gram + gram.T) / 2.0)
    gram_tolerance = max(gram.shape) * max(float(np.max(np.abs(gram_eigenvalues))), 1.0) * 1e-9
    gram_rank = int(np.count_nonzero(gram_eigenvalues > gram_tolerance))
    bq = incidence @ gram

    cycle_rank = None
    cycle_rows = None
    cycle_columns = None
    cycle_smallest = None
    rotation_residual = None
    if y_matrix is not None:
        flat_y = y_matrix.ravel()
        cycle_jacobian = cycle_norm_jacobian(flat_y, basis, edge_vectors.shape[1])
        cycle_rank, _, cycle_singular_values = matrix_numerical_rank(cycle_jacobian)
        cycle_rows, cycle_columns = cycle_jacobian.shape
        cycle_smallest = (
            float(cycle_singular_values[min(cycle_jacobian.shape) - 1])
            if cycle_singular_values.size
            else None
        )
        rotation_residual = global_rotation_null_residual(basis, y_matrix, cycle_jacobian)

    reduced_incidence = incidence[:-1, :]
    tangent_jacobian = tangent_balance_jacobian(reduced_incidence, edge_vectors)
    tangent_rank, _, tangent_singular_values = matrix_numerical_rank(tangent_jacobian)
    tangent_smallest = (
        float(tangent_singular_values[min(tangent_jacobian.shape) - 1])
        if tangent_singular_values.size
        else None
    )

    max_conservation = float(np.max(np.abs(conservation)))
    max_norm = float(np.max(np.abs(norm_residual)))
    found = max_conservation <= tolerance and max_norm <= tolerance

    return FlowMetrics(
        found=found,
        ambient_dim=edge_vectors.shape[1],
        max_conservation_residual=max_conservation,
        l2_conservation_residual=float(np.linalg.norm(conservation)),
        max_unit_norm_residual=max_norm,
        l2_unit_norm_residual=float(np.linalg.norm(norm_residual)),
        max_local_dot_residual=local_dot_residual(incidence, edge_vectors),
        gram_min_eigenvalue=float(np.min(gram_eigenvalues)),
        gram_numerical_rank=gram_rank,
        gram_rank_tolerance=float(gram_tolerance),
        max_gram_diagonal_residual=float(np.max(np.abs(np.diag(gram) - 1.0))),
        max_bq_residual=float(np.max(np.abs(bq))),
        cycle_jacobian_rank=cycle_rank,
        cycle_jacobian_rows=cycle_rows,
        cycle_jacobian_columns=cycle_columns,
        cycle_jacobian_smallest_singular_value=cycle_smallest,
        tangent_balance_rank=tangent_rank,
        tangent_balance_rows=tangent_jacobian.shape[0],
        tangent_balance_columns=tangent_jacobian.shape[1],
        tangent_balance_smallest_singular_value=tangent_smallest,
        global_rotation_null_residual=rotation_residual,
    )


def solve_cycle_space(
    graph_name: str,
    incidence: FloatArray,
    basis: FloatArray,
    config: SolverConfig,
    initial_y: FloatArray | None = None,
) -> FlowSolution:
    """Solve the unit-norm equations in cycle-space coordinates."""

    start_time = time.perf_counter()
    random_generator = np.random.default_rng(config.seed)
    best_result = None
    best_y = None
    restart_costs: list[float] = []
    successful_restarts = 0

    for restart_index in range(config.restarts):
        if restart_index == 0 and initial_y is not None:
            y0 = np.asarray(initial_y, dtype=np.float64)
            if y0.shape != (basis.shape[1], config.ambient_dim):
                raise ValueError(
                    f"Initial Y has shape {y0.shape}, expected {(basis.shape[1], config.ambient_dim)}"
                )
        else:
            y0 = random_cycle_initialization(basis, config.ambient_dim, random_generator)

        result = least_squares(
            cycle_norm_residual,
            y0.ravel(),
            jac=cycle_norm_jacobian,
            args=(basis, config.ambient_dim),
            method="trf",
            x_scale="jac",
            ftol=1e-13,
            xtol=1e-13,
            gtol=1e-13,
            max_nfev=config.max_nfev,
            verbose=config.verbose,
        )
        y_matrix = result.x.reshape(basis.shape[1], config.ambient_dim)
        edge_vectors = basis @ y_matrix
        residual = cycle_norm_residual(result.x, basis, config.ambient_dim)
        cost = float(np.linalg.norm(residual))
        restart_costs.append(cost)
        if float(np.max(np.abs(residual))) <= config.tolerance:
            successful_restarts += 1
        if best_result is None or cost < float(np.linalg.norm(best_result.fun)):
            best_result = result
            best_y = y_matrix

    if best_result is None or best_y is None:
        raise RuntimeError("Cycle-space solver did not execute")

    best_x = basis @ best_y
    metrics = evaluate_flow(incidence, basis, best_x, best_y, config.tolerance)
    return FlowSolution(
        method="cycle_space_least_squares",
        graph_name=graph_name,
        ambient_dim=config.ambient_dim,
        X=best_x,
        Y=best_y,
        metrics=metrics,
        elapsed_seconds=time.perf_counter() - start_time,
        best_cost=float(np.linalg.norm(best_result.fun)),
        best_optimality=float(best_result.optimality),
        best_status=int(best_result.status),
        best_message=str(best_result.message),
        best_nfev=int(best_result.nfev),
        restart_costs=restart_costs,
        successful_restarts=successful_restarts,
    )


def solve_direct_spheres(
    graph_name: str,
    incidence: FloatArray,
    basis: FloatArray,
    config: SolverConfig,
    initial_x: FloatArray | None = None,
) -> FlowSolution:
    """Solve Kirchhoff equations directly on a product of unit spheres."""

    start_time = time.perf_counter()
    random_generator = np.random.default_rng(config.seed + 31_337)
    reduced_incidence = incidence[:-1, :]
    edge_count = incidence.shape[1]
    best_result = None
    best_x = None
    restart_costs: list[float] = []
    successful_restarts = 0

    for restart_index in range(config.restarts):
        if restart_index == 0 and initial_x is not None:
            w0 = np.asarray(initial_x, dtype=np.float64).copy()
            if w0.shape != (edge_count, config.ambient_dim):
                raise ValueError(
                    f"Initial X has shape {w0.shape}, expected {(edge_count, config.ambient_dim)}"
                )
            w0 += 1e-4 * random_generator.normal(size=w0.shape)
        else:
            w0 = normalize_rows(random_generator.normal(size=(edge_count, config.ambient_dim)))

        result = least_squares(
            direct_balance_residual,
            w0.ravel(),
            jac=direct_balance_jacobian,
            args=(reduced_incidence, config.ambient_dim),
            method="trf",
            x_scale="jac",
            ftol=1e-13,
            xtol=1e-13,
            gtol=1e-13,
            max_nfev=config.max_nfev,
            verbose=config.verbose,
        )
        w_matrix = result.x.reshape(edge_count, config.ambient_dim)
        edge_vectors = normalize_rows(w_matrix)
        residual = reduced_incidence @ edge_vectors
        cost = float(np.linalg.norm(residual))
        restart_costs.append(cost)
        if float(np.max(np.abs(residual))) <= config.tolerance:
            successful_restarts += 1
        if best_result is None or cost < float(np.linalg.norm(best_result.fun)):
            best_result = result
            best_x = edge_vectors
        if cost <= config.tolerance * 0.1 and successful_restarts >= min(2, config.restarts):
            break

    if best_result is None or best_x is None:
        raise RuntimeError("Direct sphere solver did not execute")

    metrics = evaluate_flow(incidence, basis, best_x, None, config.tolerance)
    return FlowSolution(
        method="direct_product_of_spheres",
        graph_name=graph_name,
        ambient_dim=config.ambient_dim,
        X=best_x,
        Y=None,
        metrics=metrics,
        elapsed_seconds=time.perf_counter() - start_time,
        best_cost=float(np.linalg.norm(best_result.fun)),
        best_optimality=float(best_result.optimality),
        best_status=int(best_result.status),
        best_message=str(best_result.message),
        best_nfev=int(best_result.nfev),
        restart_costs=restart_costs,
        successful_restarts=successful_restarts,
    )


def exact_three_edge_coloring(
    graph: nx.Graph,
    timeout_seconds: float,
) -> EdgeColoringResult:
    """Decide three-edge-colorability by exact backtracking for a small cubic graph."""

    start_time = time.perf_counter()
    if not all(degree == 3 for _, degree in graph.degree()):
        return EdgeColoringResult(
            status="not_cubic",
            colorable=None,
            elapsed_seconds=0.0,
            explored_nodes=0,
            coloring=None,
        )

    edges = sorted((min(u, v), max(u, v)) for u, v in graph.edges())
    edge_count = len(edges)
    colors = [-1] * edge_count
    used_masks = [0] * graph.number_of_nodes()
    explored_nodes = 0

    incident_edge_indices: list[list[int]] = [[] for _ in graph.nodes()]
    for edge_index, (u, v) in enumerate(edges):
        incident_edge_indices[u].append(edge_index)
        incident_edge_indices[v].append(edge_index)

    deadline = start_time + timeout_seconds

    def choose_edge() -> tuple[int, int]:
        selected = -1
        selected_allowed = 0
        best_key = (4, -1, -1)
        for edge_index, (u, v) in enumerate(edges):
            if colors[edge_index] != -1:
                continue
            allowed = 0b111 & ~(used_masks[u] | used_masks[v])
            allowed_count = allowed.bit_count()
            saturation = used_masks[u].bit_count() + used_masks[v].bit_count()
            colored_neighbors = sum(
                colors[index] != -1
                for index in set(incident_edge_indices[u] + incident_edge_indices[v])
            )
            key = (allowed_count, -saturation, -colored_neighbors)
            if key < best_key:
                best_key = key
                selected = edge_index
                selected_allowed = allowed
                if allowed_count == 0:
                    break
        return selected, selected_allowed

    def search(colored_count: int) -> bool:
        nonlocal explored_nodes
        explored_nodes += 1
        if explored_nodes % 1024 == 0 and time.perf_counter() > deadline:
            raise ColoringTimeout
        if colored_count == edge_count:
            return True

        edge_index, allowed = choose_edge()
        if edge_index < 0:
            return True
        if allowed == 0:
            return False

        u, v = edges[edge_index]
        while allowed:
            bit = allowed & -allowed
            allowed ^= bit
            color = bit.bit_length() - 1
            colors[edge_index] = color
            used_masks[u] |= bit
            used_masks[v] |= bit
            if search(colored_count + 1):
                return True
            used_masks[u] ^= bit
            used_masks[v] ^= bit
            colors[edge_index] = -1
        return False

    try:
        first_u, first_v = edges[0]
        colors[0] = 0
        used_masks[first_u] |= 1
        used_masks[first_v] |= 1
        colorable = search(1)
        status = "colorable" if colorable else "not_colorable"
        coloring = colors.copy() if colorable else None
    except ColoringTimeout:
        colorable = None
        status = "timeout"
        coloring = None

    return EdgeColoringResult(
        status=status,
        colorable=colorable,
        elapsed_seconds=time.perf_counter() - start_time,
        explored_nodes=explored_nodes,
        coloring=coloring,
    )


def canonical_undirected_cycle(cycle: Sequence[int]) -> tuple[int, ...]:
    """Canonicalize an undirected simple cycle up to rotation and reversal."""

    values = list(cycle)
    if len(values) < 3:
        raise ValueError("A simple graph cycle must contain at least three vertices")
    rotations = []
    for orientation in (values, list(reversed(values))):
        minimum = min(orientation)
        for index, value in enumerate(orientation):
            if value == minimum:
                rotations.append(tuple(orientation[index:] + orientation[:index]))
    return min(rotations)


def enumerate_simple_cycles_limited(
    graph: nx.Graph,
    maximum_cycles: int,
    length_bound: int | None = None,
) -> tuple[list[list[int]], bool]:
    """Enumerate unique undirected cycles with an explicit safety cap."""

    unique: dict[tuple[int, ...], list[int]] = {}
    truncated = False
    try:
        generator = nx.simple_cycles(graph, length_bound=length_bound)
        for cycle in generator:
            if len(cycle) < 3:
                continue
            canonical = canonical_undirected_cycle(cycle)
            unique.setdefault(canonical, list(canonical))
            if len(unique) >= maximum_cycles:
                truncated = True
                break
    except TypeError:
        generator = nx.simple_cycles(graph)
        for cycle in generator:
            if length_bound is not None and len(cycle) > length_bound:
                continue
            if len(cycle) < 3:
                continue
            canonical = canonical_undirected_cycle(cycle)
            unique.setdefault(canonical, list(canonical))
            if len(unique) >= maximum_cycles:
                truncated = True
                break
    return list(unique.values()), truncated


def signed_cycle_vector(
    cycle: Sequence[int],
    edge_index: dict[tuple[int, int], int],
    edge_count: int,
) -> FloatArray:
    """Convert an oriented cycle into a signed circulation vector."""

    vector = np.zeros(edge_count, dtype=np.float64)
    for position, source in enumerate(cycle):
        target = cycle[(position + 1) % len(cycle)]
        key = (min(source, target), max(source, target))
        index = edge_index[key]
        vector[index] = 1.0 if source < target else -1.0
    return vector


def cycle_cone_psd(
    graph: nx.Graph,
    incidence: FloatArray,
    edges: list[tuple[int, int]],
    maximum_cycles: int,
    length_bound: int | None,
) -> CycleConeResult:
    """Construct a high-rank PSD solution from a fractional cycle cover LP."""

    start_time = time.perf_counter()
    cycles, truncated = enumerate_simple_cycles_limited(graph, maximum_cycles, length_bound)
    if not cycles:
        return CycleConeResult(
            attempted=True,
            success=False,
            truncated_cycle_enumeration=truncated,
            cycle_count=0,
            active_cycle_count=0,
            elapsed_seconds=time.perf_counter() - start_time,
            max_coverage_residual=None,
            max_bq_residual=None,
            min_q_eigenvalue=None,
            q_numerical_rank=None,
            message="No cycles were enumerated",
        )

    edge_lookup = {edge: index for index, edge in enumerate(edges)}
    cycle_vectors = np.column_stack(
        [signed_cycle_vector(cycle, edge_lookup, len(edges)) for cycle in cycles]
    )
    coverage = np.abs(cycle_vectors)
    result = linprog(
        c=np.zeros(len(cycles), dtype=np.float64),
        A_eq=coverage,
        b_eq=np.ones(len(edges), dtype=np.float64),
        bounds=(0.0, None),
        method="highs",
    )
    if not result.success or result.x is None:
        message = str(result.message)
        if truncated:
            message += "; cycle enumeration was truncated, so failure is inconclusive"
        return CycleConeResult(
            attempted=True,
            success=False,
            truncated_cycle_enumeration=truncated,
            cycle_count=len(cycles),
            active_cycle_count=0,
            elapsed_seconds=time.perf_counter() - start_time,
            max_coverage_residual=None,
            max_bq_residual=None,
            min_q_eigenvalue=None,
            q_numerical_rank=None,
            message=message,
        )

    weights = np.asarray(result.x, dtype=np.float64)
    active = weights > 1e-10
    weighted_vectors = cycle_vectors[:, active] * np.sqrt(weights[active])[None, :]
    q_matrix = weighted_vectors @ weighted_vectors.T
    coverage_residual = coverage @ weights - 1.0
    eigenvalues = np.linalg.eigvalsh((q_matrix + q_matrix.T) / 2.0)
    rank_tolerance = max(q_matrix.shape) * max(float(np.max(np.abs(eigenvalues))), 1.0) * 1e-9
    numerical_rank = int(np.count_nonzero(eigenvalues > rank_tolerance))

    return CycleConeResult(
        attempted=True,
        success=True,
        truncated_cycle_enumeration=truncated,
        cycle_count=len(cycles),
        active_cycle_count=int(np.count_nonzero(active)),
        elapsed_seconds=time.perf_counter() - start_time,
        max_coverage_residual=float(np.max(np.abs(coverage_residual))),
        max_bq_residual=float(np.max(np.abs(incidence @ q_matrix))),
        min_q_eigenvalue=float(np.min(eigenvalues)),
        q_numerical_rank=numerical_rank,
        message="Feasible fractional cycle cover and PSD matrix found",
        Q=q_matrix,
        weights=weights,
        cycles=cycles,
    )


def solve_sdp_relaxation(
    basis: FloatArray,
    target_rank: int,
    tolerance: float,
    maximum_iterations: int,
) -> SDPResult:
    """Solve the convex PSD relaxation and return a rank-d truncation seed."""

    start_time = time.perf_counter()
    try:
        import cvxpy as cp
    except Exception:
        return SDPResult(
            attempted=True,
            available=False,
            success=False,
            status="cvxpy_not_installed",
            solver=None,
            elapsed_seconds=time.perf_counter() - start_time,
            objective_value=None,
            max_measurement_residual=None,
            min_eigenvalue=None,
            numerical_rank=None,
            eigenvalues_descending=[],
        )

    cycle_dimension = basis.shape[1]
    h_matrix = cp.Variable((cycle_dimension, cycle_dimension), PSD=True)
    measurements = cp.sum(cp.multiply(basis @ h_matrix, basis), axis=1)
    constraints = [measurements == 1.0]
    problem = cp.Problem(cp.Minimize(cp.trace(h_matrix)), constraints)

    installed_solvers = set(cp.installed_solvers())
    solver = None
    solve_kwargs: dict[str, Any] = {"verbose": False}
    if "CLARABEL" in installed_solvers:
        solver = "CLARABEL"
    elif "SCS" in installed_solvers:
        solver = "SCS"
        solve_kwargs.update({"eps": max(tolerance * 0.1, 1e-9), "max_iters": maximum_iterations})
    elif "CVXOPT" in installed_solvers:
        solver = "CVXOPT"
    else:
        return SDPResult(
            attempted=True,
            available=True,
            success=False,
            status="no_psd_capable_solver_found",
            solver=None,
            elapsed_seconds=time.perf_counter() - start_time,
            objective_value=None,
            max_measurement_residual=None,
            min_eigenvalue=None,
            numerical_rank=None,
            eigenvalues_descending=[],
        )

    try:
        problem.solve(solver=solver, **solve_kwargs)
    except Exception as error:
        return SDPResult(
            attempted=True,
            available=True,
            success=False,
            status=f"solver_error: {error}",
            solver=solver,
            elapsed_seconds=time.perf_counter() - start_time,
            objective_value=None,
            max_measurement_residual=None,
            min_eigenvalue=None,
            numerical_rank=None,
            eigenvalues_descending=[],
        )

    if h_matrix.value is None or problem.status not in {cp.OPTIMAL, cp.OPTIMAL_INACCURATE}:
        return SDPResult(
            attempted=True,
            available=True,
            success=False,
            status=str(problem.status),
            solver=solver,
            elapsed_seconds=time.perf_counter() - start_time,
            objective_value=float(problem.value) if problem.value is not None else None,
            max_measurement_residual=None,
            min_eigenvalue=None,
            numerical_rank=None,
            eigenvalues_descending=[],
        )

    h_value = np.asarray(h_matrix.value, dtype=np.float64)
    h_value = (h_value + h_value.T) / 2.0
    eigenvalues, eigenvectors = np.linalg.eigh(h_value)
    descending = np.argsort(eigenvalues)[::-1]
    eigenvalues = eigenvalues[descending]
    eigenvectors = eigenvectors[:, descending]
    rank_tolerance = max(h_value.shape) * max(float(np.max(np.abs(eigenvalues))), 1.0) * 1e-8
    numerical_rank = int(np.count_nonzero(eigenvalues > rank_tolerance))
    positive = np.maximum(eigenvalues[:target_rank], 0.0)
    rank_d_seed = eigenvectors[:, :target_rank] * np.sqrt(positive)[None, :]
    measurement_values = np.einsum("ij,jk,ik->i", basis, h_value, basis)

    return SDPResult(
        attempted=True,
        available=True,
        success=True,
        status=str(problem.status),
        solver=solver,
        elapsed_seconds=time.perf_counter() - start_time,
        objective_value=float(problem.value),
        max_measurement_residual=float(np.max(np.abs(measurement_values - 1.0))),
        min_eigenvalue=float(np.min(eigenvalues)),
        numerical_rank=numerical_rank,
        eigenvalues_descending=eigenvalues.tolist(),
        H=h_value,
        rank_d_seed=rank_d_seed,
    )


def bareiss_determinant(integer_matrix: Sequence[Sequence[int]]) -> int:
    """Compute an exact integer determinant with the fraction-free Bareiss algorithm."""

    matrix = [list(map(int, row)) for row in integer_matrix]
    size = len(matrix)
    if size == 0:
        return 1
    sign = 1
    previous_pivot = 1
    for pivot_index in range(size - 1):
        if matrix[pivot_index][pivot_index] == 0:
            swap_index = next(
                (index for index in range(pivot_index + 1, size) if matrix[index][pivot_index] != 0),
                None,
            )
            if swap_index is None:
                return 0
            matrix[pivot_index], matrix[swap_index] = matrix[swap_index], matrix[pivot_index]
            sign *= -1
        pivot = matrix[pivot_index][pivot_index]
        for row in range(pivot_index + 1, size):
            for column in range(pivot_index + 1, size):
                numerator = matrix[row][column] * pivot - matrix[row][pivot_index] * matrix[pivot_index][column]
                matrix[row][column] = numerator // previous_pivot
        previous_pivot = pivot
        for row in range(pivot_index + 1, size):
            matrix[row][pivot_index] = 0
    return sign * matrix[-1][-1]


def fano_palette_obstruction() -> dict[str, Any]:
    """Prove the fixed seven-vector F_2^3 palette equations have only the zero solution."""

    points = list(range(1, 8))
    lines_set: set[tuple[int, int, int]] = set()
    for first in points:
        for second in points:
            if first >= second:
                continue
            third = first ^ second
            if third == 0 or third in {first, second}:
                continue
            lines_set.add(tuple(sorted((first, second, third))))
    lines = sorted(lines_set)
    incidence = np.zeros((len(lines), len(points)), dtype=np.int64)
    for line_index, line in enumerate(lines):
        for point in line:
            incidence[line_index, point - 1] = 1

    determinant = bareiss_determinant(incidence.tolist())
    gram = incidence @ incidence.T
    expected_gram = 2 * np.eye(7, dtype=np.int64) + np.ones((7, 7), dtype=np.int64)
    return {
        "points": points,
        "lines": [list(line) for line in lines],
        "incidence_matrix": incidence,
        "exact_determinant": determinant,
        "full_real_rank": determinant != 0,
        "incidence_times_transpose": gram,
        "equals_2I_plus_J": bool(np.array_equal(gram, expected_gram)),
        "conclusion": (
            "The real system A P = 0 has only P = 0. Therefore no fixed assignment "
            "of seven unit vectors can satisfy p_a + p_b + p_{a xor b} = 0 for all Fano lines."
        ),
    }


def enumerate_small_edge_cuts(
    graph: nx.Graph,
    sizes: Sequence[int] = (2, 3),
    maximum_examples_per_size: int = 20,
) -> dict[str, Any]:
    """Enumerate small edge cuts for moderate graph sizes."""

    from itertools import combinations

    edges = sorted((min(u, v), max(u, v)) for u, v in graph.edges())
    result: dict[str, Any] = {}
    for cut_size in sizes:
        count = 0
        examples: list[list[list[int]]] = []
        for candidate in combinations(edges, cut_size):
            reduced = graph.copy()
            reduced.remove_edges_from(candidate)
            if not nx.is_connected(reduced):
                count += 1
                if len(examples) < maximum_examples_per_size:
                    examples.append([list(edge) for edge in candidate])
        result[str(cut_size)] = {"count": count, "examples": examples}
    return result


def save_flow_solution(
    output_directory: Path,
    solution: FlowSolution,
    incidence: FloatArray,
    basis: FloatArray,
    edges: list[tuple[int, int]],
) -> tuple[Path, Path]:
    """Save a flow candidate as NPZ and JSON."""

    stem = f"{safe_name(solution.graph_name)}_d{solution.ambient_dim}_{safe_name(solution.method)}"
    npz_path = output_directory / "solutions" / f"{stem}.npz"
    json_path = output_directory / "reports" / f"{stem}.json"
    npz_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        npz_path,
        X=solution.X,
        Y=np.array([]) if solution.Y is None else solution.Y,
        Q=solution.X @ solution.X.T,
        B=incidence,
        Z=basis,
        edges=np.asarray(edges, dtype=np.int64),
        restart_costs=np.asarray(solution.restart_costs, dtype=np.float64),
    )
    report = {
        "method": solution.method,
        "graph_name": solution.graph_name,
        "ambient_dim": solution.ambient_dim,
        "elapsed_seconds": solution.elapsed_seconds,
        "best_cost": solution.best_cost,
        "best_optimality": solution.best_optimality,
        "best_status": solution.best_status,
        "best_message": solution.best_message,
        "best_nfev": solution.best_nfev,
        "successful_restarts": solution.successful_restarts,
        "restart_costs": solution.restart_costs,
        "metrics": asdict(solution.metrics),
        "npz_certificate": str(npz_path),
        "interpretation": (
            "A found=true record is a finite-precision numerical candidate. "
            "A found=false record does not disprove existence."
        ),
    }
    write_json(json_path, report)
    return npz_path, json_path


def solution_summary_row(
    diagnostics: GraphDiagnostics,
    coloring: EdgeColoringResult | None,
    solution: FlowSolution,
    sdp_result: SDPResult | None,
    cycle_cone_result: CycleConeResult | None,
) -> dict[str, Any]:
    """Flatten the main result fields for CSV export."""

    metrics = solution.metrics
    return {
        "graph": diagnostics.name,
        "vertices": diagnostics.vertices,
        "edges": diagnostics.edges,
        "girth": diagnostics.girth,
        "edge_connectivity": diagnostics.edge_connectivity,
        "cubic": diagnostics.cubic,
        "bridgeless": diagnostics.bridgeless,
        "three_edge_colorable": None if coloring is None else coloring.colorable,
        "edge_coloring_status": None if coloring is None else coloring.status,
        "method": solution.method,
        "ambient_dim": solution.ambient_dim,
        "found": metrics.found,
        "max_conservation_residual": metrics.max_conservation_residual,
        "max_unit_norm_residual": metrics.max_unit_norm_residual,
        "max_local_dot_residual": metrics.max_local_dot_residual,
        "gram_rank": metrics.gram_numerical_rank,
        "max_bq_residual": metrics.max_bq_residual,
        "cycle_jacobian_rank": metrics.cycle_jacobian_rank,
        "cycle_jacobian_rows": metrics.cycle_jacobian_rows,
        "cycle_jacobian_columns": metrics.cycle_jacobian_columns,
        "tangent_balance_rank": metrics.tangent_balance_rank,
        "tangent_balance_rows": metrics.tangent_balance_rows,
        "tangent_balance_columns": metrics.tangent_balance_columns,
        "global_rotation_null_residual": metrics.global_rotation_null_residual,
        "successful_restarts": solution.successful_restarts,
        "attempted_restarts": len(solution.restart_costs),
        "elapsed_seconds": solution.elapsed_seconds,
        "sdp_success": None if sdp_result is None else sdp_result.success,
        "sdp_rank": None if sdp_result is None else sdp_result.numerical_rank,
        "cycle_cone_success": None if cycle_cone_result is None else cycle_cone_result.success,
        "cycle_cone_rank": None if cycle_cone_result is None else cycle_cone_result.q_numerical_rank,
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    """Write a list of dictionaries as CSV."""

    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def plot_summary(rows: list[dict[str, Any]], output_directory: Path) -> list[Path]:
    """Create separate residual and success plots using Matplotlib defaults."""

    try:
        import matplotlib.pyplot as plt
    except Exception:
        return []

    cycle_rows = [row for row in rows if row["method"] == "cycle_space_least_squares"]
    if not cycle_rows:
        return []

    labels = [f"{row['graph']} d={row['ambient_dim']}" for row in cycle_rows]
    residuals = [
        max(float(row["max_unit_norm_residual"]), float(row["max_conservation_residual"]), 1e-18)
        for row in cycle_rows
    ]
    x_values = np.arange(len(labels))

    paths: list[Path] = []
    figure = plt.figure(figsize=(max(10.0, len(labels) * 0.55), 6.0))
    axis = figure.add_subplot(111)
    axis.bar(x_values, np.log10(residuals))
    axis.axhline(math.log10(1e-8), linestyle="--", linewidth=1.0)
    axis.set_ylabel("log10 maximum residual")
    axis.set_title("S^2-flow numerical residuals")
    axis.set_xticks(x_values)
    axis.set_xticklabels(labels, rotation=70, ha="right")
    axis.grid(axis="y", alpha=0.25)
    figure.tight_layout()
    path = output_directory / "plots" / "residuals.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=180)
    plt.close(figure)
    paths.append(path)

    dimensions = sorted({int(row["ambient_dim"]) for row in cycle_rows})
    success_rates = []
    for dimension in dimensions:
        subset = [row for row in cycle_rows if int(row["ambient_dim"]) == dimension]
        success_rates.append(100.0 * sum(bool(row["found"]) for row in subset) / len(subset))

    figure = plt.figure(figsize=(8.0, 5.0))
    axis = figure.add_subplot(111)
    axis.plot(dimensions, success_rates, marker="o")
    axis.set_xlabel("Ambient dimension")
    axis.set_ylabel("Numerical success rate (%)")
    axis.set_title("Finite-suite success by ambient dimension")
    axis.set_ylim(-5.0, 105.0)
    axis.grid(alpha=0.25)
    figure.tight_layout()
    path = output_directory / "plots" / "dimension_success.png"
    figure.savefig(path, dpi=180)
    plt.close(figure)
    paths.append(path)

    return paths


def print_graph_header(name: str, diagnostics: GraphDiagnostics) -> None:
    """Print a compact graph status line."""

    print(
        f"\n[{name}] n={diagnostics.vertices}, m={diagnostics.edges}, "
        f"cubic={diagnostics.cubic}, bridgeless={diagnostics.bridgeless}, "
        f"girth={diagnostics.girth}, cycle_rank={diagnostics.cycle_rank}"
    )


def run_experiment(arguments: argparse.Namespace) -> int:
    """Execute the complete reproducibility workflow."""

    output_directory = Path(arguments.output_dir).expanduser().resolve()
    output_directory.mkdir(parents=True, exist_ok=True)
    write_json(output_directory / "environment.json", environment_report())
    write_json(output_directory / "fano_palette_obstruction.json", fano_palette_obstruction())

    graphs = graph_suite(arguments.suite, arguments.seed)
    for specification in arguments.graphs:
        graphs.append(load_graph_spec(specification, arguments.seed))

    deduplicated: dict[str, nx.Graph] = {}
    for name, graph in graphs:
        candidate_name = safe_name(name)
        if candidate_name in deduplicated:
            suffix = 2
            while f"{candidate_name}_{suffix}" in deduplicated:
                suffix += 1
            candidate_name = f"{candidate_name}_{suffix}"
        relabeled, _ = relabel_graph_to_integers(graph)
        deduplicated[candidate_name] = relabeled

    if not deduplicated:
        raise ValueError("No graphs selected. Use --suite or --graphs")

    summary_rows: list[dict[str, Any]] = []
    graph_reports: dict[str, Any] = {}
    strict_failures: list[str] = []

    for graph_index, (name, graph) in enumerate(deduplicated.items()):
        diagnostics = diagnose_graph(name, graph)
        print_graph_header(name, diagnostics)

        graph_path = output_directory / "graphs" / f"{safe_name(name)}.g6"
        graph_path.parent.mkdir(parents=True, exist_ok=True)
        nx.write_graph6(graph, graph_path, header=False)

        incidence, edges = oriented_incidence_matrix(graph)
        basis = cycle_space_basis(incidence)

        coloring_result = None
        if arguments.run_edge_coloring:
            coloring_result = exact_three_edge_coloring(graph, arguments.edge_coloring_timeout)
            print(
                f"  3-edge-coloring: {coloring_result.status} "
                f"({coloring_result.elapsed_seconds:.3f}s, nodes={coloring_result.explored_nodes})"
            )

        small_cuts = None
        if arguments.run_small_cuts and graph.number_of_edges() <= arguments.small_cut_edge_limit:
            small_cuts = enumerate_small_edge_cuts(graph)

        cycle_cone_result = None
        if arguments.run_cycle_cone:
            cycle_cone_result = cycle_cone_psd(
                graph,
                incidence,
                edges,
                maximum_cycles=arguments.maximum_cycles,
                length_bound=arguments.cycle_length_bound,
            )
            print(
                f"  Cycle-cone PSD: success={cycle_cone_result.success}, "
                f"cycles={cycle_cone_result.cycle_count}, rank={cycle_cone_result.q_numerical_rank}"
            )
            if cycle_cone_result.Q is not None:
                (output_directory / "solutions").mkdir(parents=True, exist_ok=True)
                np.savez_compressed(
                    output_directory / "solutions" / f"{safe_name(name)}_cycle_cone_psd.npz",
                    Q=cycle_cone_result.Q,
                    weights=cycle_cone_result.weights,
                    B=incidence,
                    edges=np.asarray(edges, dtype=np.int64),
                )

        per_graph_report: dict[str, Any] = {
            "diagnostics": asdict(diagnostics),
            "edge_coloring": None if coloring_result is None else asdict(coloring_result),
            "small_edge_cuts": small_cuts,
            "cycle_cone": None,
            "dimensions": {},
        }
        if cycle_cone_result is not None:
            per_graph_report["cycle_cone"] = {
                key: value
                for key, value in asdict(cycle_cone_result).items()
                if key not in {"Q", "weights", "cycles"}
            }

        for ambient_dim in arguments.dimensions:
            print(f"  Ambient dimension d={ambient_dim}")
            sdp_result = None
            sdp_seed = None
            if arguments.run_sdp:
                sdp_result = solve_sdp_relaxation(
                    basis,
                    target_rank=ambient_dim,
                    tolerance=arguments.tolerance,
                    maximum_iterations=arguments.sdp_max_iterations,
                )
                sdp_seed = sdp_result.rank_d_seed if sdp_result.success else None
                print(
                    f"    SDP: available={sdp_result.available}, success={sdp_result.success}, "
                    f"status={sdp_result.status}, rank={sdp_result.numerical_rank}"
                )
                if sdp_result.H is not None:
                    (output_directory / "solutions").mkdir(parents=True, exist_ok=True)
                    np.savez_compressed(
                        output_directory / "solutions" / f"{safe_name(name)}_d{ambient_dim}_sdp.npz",
                        H=sdp_result.H,
                        eigenvalues=np.asarray(sdp_result.eigenvalues_descending),
                        rank_d_seed=sdp_result.rank_d_seed,
                        Z=basis,
                    )

            cycle_config = SolverConfig(
                ambient_dim=ambient_dim,
                restarts=arguments.cycle_restarts,
                max_nfev=arguments.max_nfev,
                tolerance=arguments.tolerance,
                seed=arguments.seed + graph_index * 100_003 + ambient_dim * 1_009,
                verbose=arguments.solver_verbose,
            )
            cycle_solution = solve_cycle_space(
                name,
                incidence,
                basis,
                cycle_config,
                initial_y=sdp_seed,
            )
            save_flow_solution(output_directory, cycle_solution, incidence, basis, edges)
            summary_rows.append(
                solution_summary_row(
                    diagnostics,
                    coloring_result,
                    cycle_solution,
                    sdp_result,
                    cycle_cone_result,
                )
            )
            print(
                f"    Cycle-space: found={cycle_solution.metrics.found}, "
                f"unit={cycle_solution.metrics.max_unit_norm_residual:.3e}, "
                f"balance={cycle_solution.metrics.max_conservation_residual:.3e}, "
                f"successful_restarts={cycle_solution.successful_restarts}/"
                f"{len(cycle_solution.restart_costs)}"
            )

            direct_solution = None
            if arguments.run_direct:
                direct_config = SolverConfig(
                    ambient_dim=ambient_dim,
                    restarts=arguments.direct_restarts,
                    max_nfev=arguments.direct_max_nfev,
                    tolerance=arguments.tolerance,
                    seed=arguments.seed + graph_index * 200_003 + ambient_dim * 2_003,
                    verbose=arguments.solver_verbose,
                )
                direct_solution = solve_direct_spheres(
                    name,
                    incidence,
                    basis,
                    direct_config,
                    initial_x=cycle_solution.X if cycle_solution.metrics.found else None,
                )
                save_flow_solution(output_directory, direct_solution, incidence, basis, edges)
                summary_rows.append(
                    solution_summary_row(
                        diagnostics,
                        coloring_result,
                        direct_solution,
                        sdp_result,
                        cycle_cone_result,
                    )
                )
                print(
                    f"    Direct spheres: found={direct_solution.metrics.found}, "
                    f"unit={direct_solution.metrics.max_unit_norm_residual:.3e}, "
                    f"balance={direct_solution.metrics.max_conservation_residual:.3e}"
                )

            per_graph_report["dimensions"][str(ambient_dim)] = {
                "cycle_space": {
                    "metrics": asdict(cycle_solution.metrics),
                    "elapsed_seconds": cycle_solution.elapsed_seconds,
                    "best_cost": cycle_solution.best_cost,
                    "successful_restarts": cycle_solution.successful_restarts,
                    "restart_costs": cycle_solution.restart_costs,
                },
                "direct_spheres": None
                if direct_solution is None
                else {
                    "metrics": asdict(direct_solution.metrics),
                    "elapsed_seconds": direct_solution.elapsed_seconds,
                    "best_cost": direct_solution.best_cost,
                    "successful_restarts": direct_solution.successful_restarts,
                    "restart_costs": direct_solution.restart_costs,
                },
                "sdp": None
                if sdp_result is None
                else {
                    key: value
                    for key, value in asdict(sdp_result).items()
                    if key not in {"H", "rank_d_seed"}
                },
            }

            if arguments.strict and ambient_dim == 3 and diagnostics.cubic and diagnostics.bridgeless:
                if not cycle_solution.metrics.found:
                    strict_failures.append(f"{name}: cycle-space solver did not find an S^2 candidate")
                if arguments.run_direct and direct_solution is not None and not direct_solution.metrics.found:
                    strict_failures.append(f"{name}: direct solver did not find an S^2 candidate")

        graph_reports[name] = per_graph_report
        write_json(output_directory / "reports" / f"{safe_name(name)}_graph_report.json", per_graph_report)

    write_csv(output_directory / "summary.csv", summary_rows)
    write_json(output_directory / "all_graph_reports.json", graph_reports)
    plot_paths = plot_summary(summary_rows, output_directory) if arguments.plot else []

    final_report = {
        "graphs": len(deduplicated),
        "summary_rows": len(summary_rows),
        "strict_failures": strict_failures,
        "plots": [str(path) for path in plot_paths],
        "output_directory": str(output_directory),
        "warning": (
            "This is finite-instance numerical evidence. Optimizer failure is inconclusive, "
            "and optimizer success is not a proof for all bridgeless cubic graphs."
        ),
    }
    write_json(output_directory / "run_summary.json", final_report)

    print(f"\nResults written to: {output_directory}")
    print(f"Summary CSV: {output_directory / 'summary.csv'}")
    print(f"Fano obstruction: {output_directory / 'fano_palette_obstruction.json'}")
    if strict_failures:
        print("Strict-mode failures:")
        for failure in strict_failures:
            print(f"  - {failure}")
        return 2
    return 0


def build_argument_parser() -> argparse.ArgumentParser:
    """Create the command-line interface."""

    parser = argparse.ArgumentParser(
        description="Reproducible computational laboratory for S^2-flows on cubic graphs.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--suite",
        choices=("core", "reproduce", "none"),
        default="core",
        help="Predefined deterministic graph suite.",
    )
    parser.add_argument(
        "--graphs",
        nargs="*",
        default=[],
        help=(
            "Additional graph specifications: petersen, k4, k33, tutte, flower:5, "
            "gpg:n:k, random:vertices:instance, g6:path, edgelist:path, graphml:path."
        ),
    )
    parser.add_argument(
        "--dimensions",
        nargs="+",
        type=int,
        default=[3],
        help="Ambient vector-space dimensions to test. S^2 corresponds to dimension 3.",
    )
    parser.add_argument("--cycle-restarts", type=int, default=27)
    parser.add_argument("--direct-restarts", type=int, default=2)
    parser.add_argument("--direct-max-nfev", type=int, default=3_000)
    parser.add_argument("--max-nfev", type=int, default=20_000)
    parser.add_argument("--tolerance", type=float, default=1e-8)
    parser.add_argument("--seed", type=int, default=20260717)
    parser.add_argument("--solver-verbose", type=int, choices=(0, 1, 2), default=0)
    parser.add_argument("--output-dir", default="s2_flow_results")
    parser.add_argument("--run-direct", action="store_true")
    parser.add_argument("--run-sdp", action="store_true")
    parser.add_argument("--sdp-max-iterations", type=int, default=100_000)
    parser.add_argument("--run-cycle-cone", action="store_true")
    parser.add_argument("--maximum-cycles", type=int, default=50_000)
    parser.add_argument(
        "--cycle-length-bound",
        type=int,
        default=None,
        help="Optional cycle length cap for cycle-cone enumeration.",
    )
    parser.add_argument("--run-edge-coloring", action="store_true")
    parser.add_argument("--edge-coloring-timeout", type=float, default=60.0)
    parser.add_argument("--run-small-cuts", action="store_true")
    parser.add_argument("--small-cut-edge-limit", type=int, default=50)
    parser.add_argument("--plot", action="store_true")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Return exit code 2 if either solver fails to find an R^3 candidate.",
    )
    return parser


def validate_arguments(arguments: argparse.Namespace) -> None:
    """Validate command-line values before running expensive computations."""

    if any(dimension < 2 for dimension in arguments.dimensions):
        raise ValueError("Every ambient dimension must be at least 2")
    if arguments.cycle_restarts < 1 or arguments.direct_restarts < 1:
        raise ValueError("Restart counts must be positive")
    if arguments.max_nfev < 1 or arguments.direct_max_nfev < 1:
        raise ValueError("max_nfev values must be positive")
    if arguments.tolerance <= 0.0:
        raise ValueError("tolerance must be positive")
    if arguments.maximum_cycles < 1:
        raise ValueError("maximum_cycles must be positive")


def main() -> int:
    """Command-line entry point."""

    parser = build_argument_parser()
    arguments = parser.parse_args()
    try:
        validate_arguments(arguments)
        return run_experiment(arguments)
    except KeyboardInterrupt:
        print("Interrupted by user", file=sys.stderr)
        return 130
    except Exception as error:
        print(f"ERROR: {error}", file=sys.stderr)
        if os.environ.get("S2_FLOW_DEBUG") == "1":
            raise
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
