"""Cut laws and canonical closures for 2- and 3-edge cuts.

These functions encode the exact factorisation lemmas proved in the report.
They are intended both for structural preprocessing and for certificate checks.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Hashable, Iterable

import networkx as nx
import numpy as np

Node = Hashable
Edge = tuple[Node, Node]


@dataclass(frozen=True)
class CutClosure:
    """Canonical closures of both shores of a 2- or 3-edge cut."""

    cut_edges: tuple[Edge, ...]
    shore_a: frozenset[Node]
    shore_b: frozenset[Node]
    closure_a: nx.Graph
    closure_b: nx.Graph
    boundary_a: tuple[Node, ...]
    boundary_b: tuple[Node, ...]
    apex_a: Node | None
    apex_b: Node | None


def _components_after_removal(graph: nx.Graph, cut_edges: Iterable[Edge]) -> list[set[Node]]:
    reduced = graph.copy()
    reduced.remove_edges_from(cut_edges)
    return [set(component) for component in nx.connected_components(reduced)]


def find_edge_cuts(
    graph: nx.Graph,
    size: int,
    *,
    nontrivial_only: bool = True,
    max_cuts: int | None = None,
) -> list[tuple[Edge, ...]]:
    """Enumerate edge cuts of size two or three for moderate finite graphs."""
    if size not in {2, 3}:
        raise ValueError("Only cut sizes two and three are supported.")
    found: list[tuple[Edge, ...]] = []
    edges = list(graph.edges())
    for candidate in combinations(edges, size):
        components = _components_after_removal(graph, candidate)
        if len(components) != 2:
            continue
        if nontrivial_only:
            if size == 3 and min(map(len, components)) <= 1:
                continue
            if size == 2 and min(map(len, components)) <= 1:
                continue
        found.append(tuple(candidate))
        if max_cuts is not None and len(found) >= max_cuts:
            break
    return found


def close_edge_cut(graph: nx.Graph, cut_edges: Iterable[Edge]) -> CutClosure:
    """Build the canonical cubic closures of a two- or three-edge cut."""
    cut = tuple(cut_edges)
    if len(cut) not in {2, 3}:
        raise ValueError("A canonical closure is defined here only for cuts of size two or three.")
    components = _components_after_removal(graph, cut)
    if len(components) != 2:
        raise ValueError("The supplied edges do not form a two-shore edge cut.")
    shore_a, shore_b = components

    boundary_a: list[Node] = []
    boundary_b: list[Node] = []
    ordered_cut: list[Edge] = []
    for u, v in cut:
        if u in shore_a and v in shore_b:
            a, b = u, v
        elif v in shore_a and u in shore_b:
            a, b = v, u
        else:
            raise ValueError("Every cut edge must join the two shores.")
        ordered_cut.append((a, b))
        boundary_a.append(a)
        boundary_b.append(b)

    closure_a = graph.subgraph(shore_a).copy()
    closure_b = graph.subgraph(shore_b).copy()
    apex_a = None
    apex_b = None

    if len(cut) == 2:
        if boundary_a[0] == boundary_a[1] or boundary_b[0] == boundary_b[1]:
            raise ValueError("Degenerate two-edge cuts are excluded in the simple cubic setting.")
        if closure_a.has_edge(boundary_a[0], boundary_a[1]):
            raise ValueError("Closure A would require a parallel edge; use a multigraph extension.")
        if closure_b.has_edge(boundary_b[0], boundary_b[1]):
            raise ValueError("Closure B would require a parallel edge; use a multigraph extension.")
        closure_a.add_edge(boundary_a[0], boundary_a[1], closure_edge=True)
        closure_b.add_edge(boundary_b[0], boundary_b[1], closure_edge=True)
    else:
        apex_a = ("__closure_apex_a__", id(graph), tuple(sorted(map(repr, shore_a))))
        apex_b = ("__closure_apex_b__", id(graph), tuple(sorted(map(repr, shore_b))))
        closure_a.add_node(apex_a, closure_apex=True)
        closure_b.add_node(apex_b, closure_apex=True)
        closure_a.add_edges_from((apex_a, vertex, {"closure_edge": True}) for vertex in boundary_a)
        closure_b.add_edges_from((apex_b, vertex, {"closure_edge": True}) for vertex in boundary_b)

    return CutClosure(
        cut_edges=tuple(ordered_cut),
        shore_a=frozenset(shore_a),
        shore_b=frozenset(shore_b),
        closure_a=closure_a,
        closure_b=closure_b,
        boundary_a=tuple(boundary_a),
        boundary_b=tuple(boundary_b),
        apex_a=apex_a,
        apex_b=apex_b,
    )


def cut_boundary_vectors(
    shore: set[Node] | frozenset[Node],
    edge_order: list[Edge],
    flow: np.ndarray,
) -> np.ndarray:
    """Return flow vectors signed outward from a vertex shore."""
    vectors: list[np.ndarray] = []
    for idx, (u, v) in enumerate(edge_order):
        if (u in shore) == (v in shore):
            continue
        vectors.append(flow[idx] if u in shore else -flow[idx])
    return np.asarray(vectors, dtype=float)


def verify_cut_law(
    shore: set[Node] | frozenset[Node],
    edge_order: list[Edge],
    flow: np.ndarray,
    *,
    tolerance: float = 1e-8,
) -> dict[str, object]:
    """Numerically verify the cut-sum law and two/three-cut rigidity."""
    vectors = cut_boundary_vectors(shore, edge_order, flow)
    total = vectors.sum(axis=0) if len(vectors) else np.zeros(flow.shape[1])
    result: dict[str, object] = {
        "cut_size": int(len(vectors)),
        "sum_residual": float(np.linalg.norm(total)),
        "valid_cut_law": bool(np.linalg.norm(total) <= tolerance),
    }
    if len(vectors) == 2:
        result["antipodal_residual"] = float(np.linalg.norm(vectors[0] + vectors[1]))
    if len(vectors) == 3:
        gram = vectors @ vectors.T
        target = np.full((3, 3), -0.5)
        np.fill_diagonal(target, 1.0)
        result["equilateral_gram_residual"] = float(np.max(np.abs(gram - target)))
    return result
