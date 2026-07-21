"""Tests for the exact Goldberg graph construction."""

from goldberg_s2.graph import cyclic_edge_orbits, goldberg_graph, graph_invariants


def test_goldberg_graph_counts_and_orbits() -> None:
    """The cyclic action must have twelve free edge orbits."""
    graph = goldberg_graph(5)
    assert graph.number_of_nodes() == 40
    assert graph.number_of_edges() == 60
    assert all(degree == 3 for _, degree in graph.degree())

    orbits = cyclic_edge_orbits(5)
    assert len(orbits) == 12
    assert {len(orbit) for orbit in orbits} == {5}


def test_small_graph_invariants() -> None:
    """Check the structural invariants of the first Goldberg snark."""
    invariants = graph_invariants(5)
    assert invariants["connected"] is True
    assert invariants["bridges"] == 0
    assert invariants["degree_set"] == [3]
    assert invariants["girth"] == 5
