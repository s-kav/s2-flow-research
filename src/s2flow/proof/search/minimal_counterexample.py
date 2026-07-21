"""Ordering and filtering of unresolved finite-search candidates."""
from __future__ import annotations
import networkx as nx

def candidate_key(graph: nx.Graph) -> tuple[int, int, int]:
    """Order candidates by vertices, edge-connectivity, and cycle rank."""
    connectivity = nx.edge_connectivity(graph) if nx.is_connected(graph) else 0
    cycle_rank = graph.number_of_edges() - graph.number_of_nodes() + nx.number_connected_components(graph)
    return graph.number_of_nodes(), -connectivity, cycle_rank

def minimal_candidate(graphs) -> nx.Graph | None:
    """Return the smallest graph under the documented deterministic order."""
    items = list(graphs)
    return min(items, key=candidate_key) if items else None
