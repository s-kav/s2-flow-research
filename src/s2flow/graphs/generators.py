"""Graph generators used by experiments."""
from __future__ import annotations
import networkx as nx


def flower_snark(n: int) -> nx.Graph:
    """Return the Isaacs flower snark J_n for odd n >= 5."""
    if n < 5 or n % 2 == 0:
        raise ValueError("n must be odd and at least 5")
    g = nx.Graph()
    for i in range(n):
        for prefix in "abcd":
            g.add_node((prefix, i))
        g.add_edges_from([(("a", i), ("b", i)), (("a", i), ("c", i)), (("a", i), ("d", i))])
    for i in range(n):
        j = (i + 1) % n
        g.add_edge(("b", i), ("b", j))
    # One 2n-cycle alternating c and d vertices.
    seq = [("c", i) for i in range(n)] + [("d", i) for i in range(n)]
    for u, v in zip(seq, seq[1:] + seq[:1]):
        g.add_edge(u, v)
    return nx.convert_node_labels_to_integers(g)


def graph_from_spec(spec: str) -> nx.Graph:
    """Build a graph from a compact CLI specification."""
    if spec == "petersen":
        return nx.petersen_graph()
    if spec.startswith("flower:"):
        return flower_snark(int(spec.split(":")[1]))
    if spec.startswith("gpg:"):
        _, n, k = spec.split(":")
        return nx.generators.classic.circular_ladder_graph(int(n)) if int(k) == 1 else nx.Graph(nx.generators.classic.cycle_graph(0))
    if spec.startswith("random:"):
        _, n, seed = spec.split(":")
        return nx.random_regular_graph(3, int(n), seed=int(seed))
    raise ValueError(f"Unsupported graph specification: {spec}")
