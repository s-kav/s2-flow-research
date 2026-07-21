"""Oriented incidence and cycle-space matrices."""
from __future__ import annotations
import networkx as nx
import numpy as np
from scipy.linalg import null_space


def oriented_incidence(g: nx.Graph) -> tuple[np.ndarray, list[tuple[int, int]]]:
    """Return an oriented vertex-edge incidence matrix and stable edge order."""
    nodes = list(g.nodes())
    node_index = {v: i for i, v in enumerate(nodes)}
    edges = [(u, v) if node_index[u] < node_index[v] else (v, u) for u, v in g.edges()]
    edges.sort(key=lambda e: (node_index[e[0]], node_index[e[1]]))
    b = np.zeros((len(nodes), len(edges)), dtype=float)
    for j, (u, v) in enumerate(edges):
        b[node_index[u], j] = -1.0
        b[node_index[v], j] = 1.0
    return b, edges


def cycle_basis_matrix(g: nx.Graph) -> tuple[np.ndarray, np.ndarray, list[tuple[int, int]]]:
    """Return B, an orthonormal basis Z of ker(B), and edge order."""
    b, edges = oriented_incidence(g)
    z = null_space(b)
    return b, z, edges
