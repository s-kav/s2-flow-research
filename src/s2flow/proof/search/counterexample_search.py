"""Bounded computational counterexample search."""
from __future__ import annotations
from dataclasses import dataclass
import networkx as nx
from s2flow.graphs.checks import validate_bridgeless_cubic
from s2flow.optimizers.cycle_space import solve_cycle_space

@dataclass(frozen=True)
class SearchRecord:
    graph_index: int
    nodes: int
    edges: int
    valid_graph: bool
    flow_found: bool
    cost: float | None

def search_graphs(graphs, restarts: int = 24, seed: int = 20260717, tolerance: float = 1e-8) -> list[SearchRecord]:
    """Search a finite graph collection; failures are candidates, not proofs."""
    records=[]
    for index, graph in enumerate(graphs):
        try:
            validate_bridgeless_cubic(graph)
        except ValueError:
            records.append(SearchRecord(index, graph.number_of_nodes(), graph.number_of_edges(), False, False, None))
            continue
        result=solve_cycle_space(graph, dimension=3, restarts=restarts, seed=seed+index, tolerance=tolerance)
        records.append(SearchRecord(index, graph.number_of_nodes(), graph.number_of_edges(), True, bool(result.metrics["valid"]), result.cost))
    return records

def random_cubic_graphs(order: int, samples: int, seed: int = 20260717):
    """Yield connected random cubic graphs with deterministic seeds."""
    if order % 2 or order < 4:
        raise ValueError("order must be even and at least 4")
    for offset in range(samples):
        graph = nx.random_regular_graph(3, order, seed=seed + offset)
        if nx.is_connected(graph):
            yield graph
