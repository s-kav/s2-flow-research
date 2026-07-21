"""Safe graph reductions used to study hypothetical minimal counterexamples."""
from __future__ import annotations
import networkx as nx

def suppress_degree_two_vertices(graph: nx.Graph) -> nx.Graph:
    """Suppress degree-two vertices while preserving parallel-edge information in a MultiGraph."""
    reduced = nx.MultiGraph(graph)
    changed = True
    while changed:
        changed = False
        for vertex, degree in list(reduced.degree()):
            if degree == 2:
                neighbors = list(reduced.neighbors(vertex))
                if len(neighbors) == 2:
                    reduced.remove_node(vertex)
                    reduced.add_edge(neighbors[0], neighbors[1])
                    changed = True
                    break
    return reduced

def nontrivial_edge_cuts(graph: nx.Graph, maximum_size: int = 3) -> list[set[tuple[int, int]]]:
    """Enumerate unique small edge cuts that leave at least two vertices per side."""
    cuts=[]
    seen=set()
    for cut in nx.all_node_cuts(nx.line_graph(graph)):
        edges={tuple(sorted(edge)) for edge in cut}
        if 0 < len(edges) <= maximum_size:
            key=tuple(sorted(edges))
            if key not in seen:
                seen.add(key); cuts.append(edges)
    return cuts
