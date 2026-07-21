"""Goldberg graph construction and cyclic-orbit utilities."""

from __future__ import annotations

from collections.abc import Iterable

import networkx as nx

INTERNAL_EDGES: tuple[tuple[int, int], ...] = (
    (1, 2),
    (1, 7),
    (2, 8),
    (3, 4),
    (3, 8),
    (4, 7),
    (5, 6),
    (6, 7),
    (6, 8),
)

INTER_BLOCK_EDGES: tuple[tuple[int, int], ...] = (
    (2, 1),
    (4, 3),
    (5, 5),
)


def validate_k(k: int) -> None:
    """Validate the standard Goldberg-snark parameter."""
    if not isinstance(k, int):
        raise TypeError("k must be an integer")
    if k < 5 or k % 2 == 0:
        raise ValueError("Goldberg snarks use odd k >= 5")


def goldberg_graph(k: int) -> nx.Graph:
    """Build the Goldberg graph G_k from the exact eight-vertex block."""
    validate_k(k)
    graph = nx.Graph()

    for block in range(k):
        for left, right in INTERNAL_EDGES:
            graph.add_edge((block, left), (block, right))

    for block in range(k):
        next_block = (block + 1) % k
        for source_label, target_label in INTER_BLOCK_EDGES:
            graph.add_edge(
                (block, source_label),
                (next_block, target_label),
            )

    return graph


def canonical_edge(edge: tuple[tuple[int, int], tuple[int, int]]) -> tuple[tuple[int, int], tuple[int, int]]:
    """Return the undirected edge with lexicographically ordered endpoints."""
    first, second = edge
    return (first, second) if first <= second else (second, first)


def shift_vertex(vertex: tuple[int, int], shift: int, k: int) -> tuple[int, int]:
    """Apply the cyclic block shift to one vertex."""
    block, label = vertex
    return ((block + shift) % k, label)


def shift_edge(
    edge: tuple[tuple[int, int], tuple[int, int]],
    shift: int,
    k: int,
) -> tuple[tuple[int, int], tuple[int, int]]:
    """Apply the cyclic block shift to an undirected edge."""
    first, second = edge
    return canonical_edge(
        (
            shift_vertex(first, shift, k),
            shift_vertex(second, shift, k),
        )
    )


def cyclic_edge_orbits(k: int) -> list[list[tuple[tuple[int, int], tuple[int, int]]]]:
    """Return the exact Z_k edge orbits under the block shift."""
    graph = goldberg_graph(k)
    remaining = {canonical_edge(edge) for edge in graph.edges()}
    orbits: list[list[tuple[tuple[int, int], tuple[int, int]]]] = []

    while remaining:
        representative = min(remaining)
        orbit = [shift_edge(representative, shift, k) for shift in range(k)]
        orbit_set = set(orbit)
        if len(orbit_set) != k:
            raise RuntimeError("The cyclic action is not free on the selected edge")
        if not orbit_set <= remaining | {edge for existing in orbits for edge in existing}:
            raise RuntimeError("A shifted edge is not present in the graph")
        orbits.append(orbit)
        remaining -= orbit_set

    orbits.sort(key=lambda orbit: orbit[0])
    return orbits


def graph_invariants(k: int) -> dict[str, int | bool | list[int]]:
    """Compute structural invariants used by the reproducibility tests."""
    graph = goldberg_graph(k)
    degrees = sorted({degree for _, degree in graph.degree()})
    bridges = list(nx.bridges(graph))
    return {
        "k": k,
        "vertices": graph.number_of_nodes(),
        "edges": graph.number_of_edges(),
        "connected": nx.is_connected(graph),
        "degree_set": degrees,
        "bridges": len(bridges),
        "girth": nx.girth(graph),
        "edge_orbits": len(cyclic_edge_orbits(k)),
        "orbit_sizes": sorted({len(orbit) for orbit in cyclic_edge_orbits(k)}),
    }


def oriented_edge_templates() -> tuple[tuple[tuple[int, int], tuple[int, int]], ...]:
    """Return the twelve oriented representative edges in theorem order."""
    internal = tuple(((0, left), (0, right)) for left, right in INTERNAL_EDGES)
    external = tuple(((0, left), (1, right)) for left, right in INTER_BLOCK_EDGES)
    return internal + external


def iter_oriented_edges(k: int) -> Iterable[tuple[int, tuple[int, int], tuple[int, int]]]:
    """Yield orbit index and oriented edge for every cyclic shift."""
    validate_k(k)
    for orbit_index, (source, target) in enumerate(oriented_edge_templates()):
        for shift in range(k):
            yield (
                orbit_index,
                shift_vertex(source, shift, k),
                shift_vertex(target, shift, k),
            )
