"""Perfect-matching decomposition utilities for cubic graphs."""
from __future__ import annotations
import networkx as nx

def perfect_matching_and_two_factor(graph: nx.Graph) -> tuple[set[tuple[int, int]], nx.Graph]:
    """Return a perfect matching and complementary 2-factor when one is found."""
    matching = nx.algorithms.matching.max_weight_matching(graph, maxcardinality=True)
    normalized = {tuple(sorted(edge)) for edge in matching}
    if len(normalized) * 2 != graph.number_of_nodes():
        raise ValueError("No perfect matching was found")
    two_factor = graph.copy()
    two_factor.remove_edges_from(normalized)
    if any(degree != 2 for _, degree in two_factor.degree()):
        raise ValueError("Complement of matching is not a 2-factor")
    return normalized, two_factor

def two_factor_cycles(graph: nx.Graph) -> list[list[int]]:
    """Return the cycle components induced by a perfect-matching complement."""
    _, two_factor = perfect_matching_and_two_factor(graph)
    return [list(component) for component in nx.connected_components(two_factor)]
