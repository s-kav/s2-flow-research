"""Independent reduced and full-graph verification of Goldberg S^2-flows."""

from __future__ import annotations

from dataclasses import asdict, dataclass

import networkx as nx
import numpy as np

from .construction import build_templates, rotation_angle, rotation_matrix
from .graph import goldberg_graph, iter_oriented_edges, validate_k


@dataclass(frozen=True)
class VerificationResult:
    """Numerical verification metrics for one Goldberg graph."""

    k: int
    vertices: int
    edges: int
    cubic: bool
    connected: bool
    bridges: int
    max_kirchhoff_residual: float
    max_unit_norm_residual: float
    max_reduced_residual: float

    def to_dict(self) -> dict[str, int | bool | float]:
        """Serialize the result to a plain dictionary."""
        return asdict(self)


def reduced_residuals(k: int, templates: np.ndarray) -> np.ndarray:
    """Evaluate the eight representative Kirchhoff equations and twelve norms."""
    validate_k(k)
    array = np.asarray(templates, dtype=float)
    if array.shape != (12, 3):
        raise ValueError("templates must have shape (12, 3)")

    a, b, c, d, e, f, g, h, i, p, q, r = array
    inverse_rotation = rotation_matrix(-rotation_angle(k))

    kirchhoff = np.vstack(
        (
            a + b - inverse_rotation @ p,
            -a + c + p,
            d + e - inverse_rotation @ q,
            -d + f + q,
            g + r - inverse_rotation @ r,
            -g + h + i,
            b + f + h,
            c + e + i,
        )
    ).reshape(-1)
    norms = np.einsum("ij,ij->i", array, array) - 1.0
    return np.concatenate((kirchhoff, norms))


def verify_reduced_templates(k: int, templates: np.ndarray) -> tuple[float, float]:
    """Return maximum Kirchhoff and unit-norm residuals in the reduced system."""
    residual = reduced_residuals(k, templates)
    return (
        float(np.max(np.abs(residual[:24]))),
        float(np.max(np.abs(residual[24:]))),
    )


def expand_flow(k: int, templates: np.ndarray) -> dict[tuple[tuple[int, int], tuple[int, int]], np.ndarray]:
    """Expand the twelve templates to all oriented edges of G_k."""
    validate_k(k)
    array = np.asarray(templates, dtype=float)
    if array.shape != (12, 3):
        raise ValueError("templates must have shape (12, 3)")

    rotation = rotation_matrix(rotation_angle(k))
    powers = [np.linalg.matrix_power(rotation, shift) for shift in range(k)]
    flow: dict[tuple[tuple[int, int], tuple[int, int]], np.ndarray] = {}

    for orbit_index, source, target in iter_oriented_edges(k):
        shift = source[0]
        if orbit_index >= 9:
            shift = source[0]
        flow[(source, target)] = powers[shift] @ array[orbit_index]

    if len(flow) != 12 * k:
        raise RuntimeError("The expanded flow does not cover all Goldberg edges")
    return flow


def verify_full_flow(k: int, templates: np.ndarray | None = None) -> VerificationResult:
    """Verify graph structure, every vertex equation, and every edge norm."""
    validate_k(k)
    selected = build_templates(k) if templates is None else np.asarray(templates, dtype=float)
    graph = goldberg_graph(k)
    flow = expand_flow(k, selected)

    max_kirchhoff = 0.0
    for vertex in graph.nodes():
        balance = np.zeros(3)
        for neighbor in graph.neighbors(vertex):
            if (vertex, neighbor) in flow:
                balance += flow[(vertex, neighbor)]
            elif (neighbor, vertex) in flow:
                balance -= flow[(neighbor, vertex)]
            else:
                raise RuntimeError(f"Missing flow vector on edge {vertex}-{neighbor}")
        max_kirchhoff = max(max_kirchhoff, float(np.max(np.abs(balance))))

    max_norm = max(abs(float(np.dot(vector, vector)) - 1.0) for vector in flow.values())
    reduced = reduced_residuals(k, selected)

    return VerificationResult(
        k=k,
        vertices=graph.number_of_nodes(),
        edges=graph.number_of_edges(),
        cubic=all(degree == 3 for _, degree in graph.degree()),
        connected=nx.is_connected(graph),
        bridges=len(list(nx.bridges(graph))),
        max_kirchhoff_residual=max_kirchhoff,
        max_unit_norm_residual=max_norm,
        max_reduced_residual=float(np.max(np.abs(reduced))),
    )
