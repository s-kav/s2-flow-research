"""Structural graph validation."""
from __future__ import annotations
import networkx as nx


def diagnostics(g: nx.Graph) -> dict[str, object]:
    """Return structural diagnostics relevant to the conjecture."""
    bridges = list(nx.bridges(g)) if nx.is_connected(g) else []
    return {
        "vertices": g.number_of_nodes(),
        "edges": g.number_of_edges(),
        "connected": nx.is_connected(g),
        "simple": not g.is_multigraph() and nx.number_of_selfloops(g) == 0,
        "cubic": all(degree == 3 for _, degree in g.degree()),
        "bridgeless": len(bridges) == 0,
        "bridges": [list(edge) for edge in bridges],
        "cycle_rank": g.number_of_edges() - g.number_of_nodes() + nx.number_connected_components(g),
    }


def assert_target_graph(g: nx.Graph) -> None:
    """Reject graphs outside the bridgeless cubic target class."""
    d = diagnostics(g)
    if not d["connected"] or not d["cubic"] or not d["bridgeless"]:
        raise ValueError(f"Graph is not connected, cubic, and bridgeless: {d}")
