"""Constructive S2-flow certificates from proper 3-edge-colourings.

The implementation follows a rigorous theorem: the union of any two colour
classes is a 2-factor. Orienting its cycles gives one scalar circulation.
The three scalar circulations are stacked and divided by sqrt(2). Every edge
belongs to exactly two of the three 2-factors, hence every resulting vector
has Euclidean norm one.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Hashable

import networkx as nx
import numpy as np

from s2flow.algebra.incidence import oriented_incidence
from s2flow.flows.verification import verify_candidate

Node = Hashable
Edge = tuple[Node, Node]


@dataclass(frozen=True)
class EdgeColoringCertificate:
    """Result of an exact bounded backtracking search."""

    status: str
    colors: dict[Edge, int] | None
    search_nodes: int
    reason: str


def _canonical_edge(u: Node, v: Node, node_index: dict[Node, int]) -> Edge:
    return (u, v) if node_index[u] < node_index[v] else (v, u)


def find_three_edge_coloring(
    graph: nx.Graph,
    *,
    max_search_nodes: int = 5_000_000,
) -> EdgeColoringCertificate:
    """Find a proper 3-edge-colouring or prove none within the exact search tree.

    The search is exhaustive unless ``max_search_nodes`` is reached. The
    returned status is one of ``colourable``, ``not_colourable``, or ``unknown``.
    """
    if graph.is_multigraph() or nx.number_of_selfloops(graph) != 0:
        return EdgeColoringCertificate(
            status="unknown",
            colors=None,
            search_nodes=0,
            reason="Only simple loopless graphs are supported by this exact search.",
        )
    if any(degree != 3 for _, degree in graph.degree()):
        return EdgeColoringCertificate(
            status="unknown",
            colors=None,
            search_nodes=0,
            reason="The theorem-specific search expects a cubic graph.",
        )

    nodes = list(graph.nodes())
    node_index = {v: i for i, v in enumerate(nodes)}
    edges = sorted(
        (_canonical_edge(u, v, node_index) for u, v in graph.edges()),
        key=lambda e: (node_index[e[0]], node_index[e[1]]),
    )
    incident: dict[Node, list[int]] = {v: [] for v in nodes}
    for idx, (u, v) in enumerate(edges):
        incident[u].append(idx)
        incident[v].append(idx)

    colours = [-1] * len(edges)
    used_masks = {v: 0 for v in nodes}
    search_nodes = 0
    aborted = False

    # Global colour permutation symmetry can be fixed on the first edge.
    first_u, first_v = edges[0]
    colours[0] = 0
    used_masks[first_u] |= 1
    used_masks[first_v] |= 1

    def available_mask(edge_index: int) -> int:
        u, v = edges[edge_index]
        return 0b111 & ~(used_masks[u] | used_masks[v])

    def choose_edge() -> int | None:
        best_index = None
        best_key = None
        for idx, colour in enumerate(colours):
            if colour != -1:
                continue
            mask = available_mask(idx)
            count = mask.bit_count()
            u, v = edges[idx]
            saturation = used_masks[u].bit_count() + used_masks[v].bit_count()
            key = (count, -saturation, idx)
            if best_key is None or key < best_key:
                best_key = key
                best_index = idx
                if count == 0:
                    break
        return best_index

    def propagate_vertex(v: Node) -> tuple[bool, list[tuple[int, int]]]:
        """Force the last missing colour at a vertex when two are already used."""
        changes: list[tuple[int, int]] = []
        uncoloured = [idx for idx in incident[v] if colours[idx] == -1]
        if not uncoloured:
            return used_masks[v] == 0b111, changes
        if len(uncoloured) == 1 and used_masks[v].bit_count() == 2:
            idx = uncoloured[0]
            mask = available_mask(idx)
            if mask.bit_count() != 1:
                return False, changes
            colour = (mask & -mask).bit_length() - 1
            u, w = edges[idx]
            colours[idx] = colour
            used_masks[u] |= 1 << colour
            used_masks[w] |= 1 << colour
            changes.append((idx, colour))
        return True, changes

    def undo(changes: list[tuple[int, int]]) -> None:
        for idx, colour in reversed(changes):
            u, v = edges[idx]
            colours[idx] = -1
            used_masks[u] &= ~(1 << colour)
            used_masks[v] &= ~(1 << colour)

    def dfs() -> bool:
        nonlocal search_nodes, aborted
        search_nodes += 1
        if search_nodes > max_search_nodes:
            aborted = True
            return False

        forced: list[tuple[int, int]] = []
        changed = True
        while changed:
            changed = False
            for vertex in nodes:
                ok, local = propagate_vertex(vertex)
                if not ok:
                    undo(forced + local)
                    return False
                if local:
                    forced.extend(local)
                    changed = True

        idx = choose_edge()
        if idx is None:
            valid = all(mask == 0b111 for mask in used_masks.values())
            if not valid:
                undo(forced)
            return valid

        mask = available_mask(idx)
        if mask == 0:
            undo(forced)
            return False

        u, v = edges[idx]
        options = [colour for colour in range(3) if mask & (1 << colour)]
        for colour in options:
            colours[idx] = colour
            used_masks[u] |= 1 << colour
            used_masks[v] |= 1 << colour
            if dfs():
                return True
            colours[idx] = -1
            used_masks[u] &= ~(1 << colour)
            used_masks[v] &= ~(1 << colour)
            if aborted:
                break

        undo(forced)
        return False

    found = dfs()
    if found:
        return EdgeColoringCertificate(
            status="colourable",
            colors={edge: int(colours[idx]) for idx, edge in enumerate(edges)},
            search_nodes=search_nodes,
            reason="Exact proper 3-edge-colouring found.",
        )
    if aborted:
        return EdgeColoringCertificate(
            status="unknown",
            colors=None,
            search_nodes=search_nodes,
            reason="Exact search-node limit reached.",
        )
    return EdgeColoringCertificate(
        status="not_colourable",
        colors=None,
        search_nodes=search_nodes,
        reason="Exhaustive search proved that no proper 3-edge-colouring exists.",
    )


def _oriented_cycle_edges(cycle_nodes: list[Node]) -> list[tuple[Node, Node]]:
    return list(zip(cycle_nodes, cycle_nodes[1:] + cycle_nodes[:1]))


def construct_s2_flow_from_three_edge_coloring(
    graph: nx.Graph,
    colors: dict[Edge, int],
    *,
    tolerance: float = 1e-10,
) -> tuple[np.ndarray, list[Edge], dict[str, object]]:
    """Construct the explicit three-cycle-cover S2-flow certificate."""
    b, edges = oriented_incidence(graph)
    node_index = {v: i for i, v in enumerate(graph.nodes())}
    canonical_colors = {
        _canonical_edge(u, v, node_index): int(colour)
        for (u, v), colour in colors.items()
    }
    edge_index = {edge: idx for idx, edge in enumerate(edges)}
    signed_cover = np.zeros((len(edges), 3), dtype=float)

    for omitted_colour in range(3):
        factor_edges = [
            edge for edge in edges if canonical_colors[edge] != omitted_colour
        ]
        factor = nx.Graph()
        factor.add_nodes_from(graph.nodes())
        factor.add_edges_from(factor_edges)
        if any(degree != 2 for _, degree in factor.degree()):
            raise ValueError("The supplied colouring does not define three 2-factors.")

        unseen = set(factor.nodes())
        while unseen:
            start = min(unseen, key=lambda v: node_index[v])
            cycle = [start]
            previous = None
            current = start
            while True:
                neighbours = sorted(factor.neighbors(current), key=lambda v: node_index[v])
                next_candidates = [v for v in neighbours if v != previous]
                if not next_candidates:
                    raise RuntimeError("Invalid 2-factor traversal.")
                nxt = next_candidates[0]
                if nxt == start:
                    break
                cycle.append(nxt)
                previous, current = current, nxt
            unseen.difference_update(cycle)

            for u, v in _oriented_cycle_edges(cycle):
                edge = _canonical_edge(u, v, node_index)
                idx = edge_index[edge]
                signed_cover[idx, omitted_colour] = 1.0 if edge == (u, v) else -1.0

    row_nonzero = np.count_nonzero(signed_cover, axis=1)
    if not np.all(row_nonzero == 2):
        raise RuntimeError("Every edge must occur in exactly two oriented 2-factors.")
    x = signed_cover / np.sqrt(2.0)
    metrics = verify_candidate(b, x, tolerance=tolerance)
    metrics = {
        **metrics,
        "certificate_type": "three_oriented_2_factors",
        "cover_multiplicity": 2,
        "coordinates": 3,
    }
    return x, edges, metrics
