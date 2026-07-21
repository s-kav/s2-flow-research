"""Regression tests for the rigorous partial theorems."""
from __future__ import annotations

import networkx as nx
import numpy as np

from s2flow.proof.theory.cycle_cover import (
    construct_s2_flow_from_three_edge_coloring,
    find_three_edge_coloring,
)
from s2flow.proof.theory.cut_factorization import (
    close_edge_cut,
    find_edge_cuts,
    verify_cut_law,
)


def _three_sum_k4() -> nx.Graph:
    left = nx.complete_graph(4)
    right = nx.relabel_nodes(nx.complete_graph(4), lambda v: v + 10)
    left_boundary = list(left.neighbors(0))
    right_boundary = list(right.neighbors(10))
    left.remove_node(0)
    right.remove_node(10)
    graph = nx.compose(left, right)
    graph.add_edges_from(zip(left_boundary, right_boundary))
    return graph


def _two_sum_k4() -> nx.Graph:
    left = nx.complete_graph(4)
    right = nx.relabel_nodes(nx.complete_graph(4), lambda v: v + 10)
    left.remove_edge(0, 1)
    right.remove_edge(10, 11)
    graph = nx.compose(left, right)
    graph.add_edges_from([(0, 10), (1, 11)])
    return graph


def test_constructive_theorem_on_k4() -> None:
    graph = nx.complete_graph(4)
    certificate = find_three_edge_coloring(graph)
    assert certificate.status == "colourable"
    assert certificate.colors is not None
    x, edges, metrics = construct_s2_flow_from_three_edge_coloring(graph, certificate.colors)
    assert x.shape == (6, 3)
    assert len(edges) == 6
    assert metrics["valid"]
    assert metrics["max_conservation_residual"] < 1e-12
    assert metrics["max_unit_norm_residual"] < 1e-12


def test_petersen_is_proved_not_three_edge_colourable() -> None:
    certificate = find_three_edge_coloring(nx.petersen_graph(), max_search_nodes=1_000_000)
    assert certificate.status == "not_colourable"


def test_three_cut_closures_are_cubic() -> None:
    graph = _three_sum_k4()
    cuts = find_edge_cuts(graph, 3, nontrivial_only=True)
    assert cuts
    closure = close_edge_cut(graph, cuts[0])
    assert all(degree == 3 for _, degree in closure.closure_a.degree())
    assert all(degree == 3 for _, degree in closure.closure_b.degree())
    assert not list(nx.bridges(closure.closure_a))
    assert not list(nx.bridges(closure.closure_b))


def test_two_cut_closures_are_cubic() -> None:
    graph = _two_sum_k4()
    cuts = find_edge_cuts(graph, 2, nontrivial_only=True)
    assert cuts
    closure = close_edge_cut(graph, cuts[0])
    assert all(degree == 3 for _, degree in closure.closure_a.degree())
    assert all(degree == 3 for _, degree in closure.closure_b.degree())


def test_cut_rigidity_on_constructive_flow() -> None:
    graph = _three_sum_k4()
    certificate = find_three_edge_coloring(graph)
    assert certificate.colors is not None
    x, edges, metrics = construct_s2_flow_from_three_edge_coloring(graph, certificate.colors)
    assert metrics["valid"]
    cut = find_edge_cuts(graph, 3, nontrivial_only=True)[0]
    closure = close_edge_cut(graph, cut)
    rigidity = verify_cut_law(closure.shore_a, edges, x, tolerance=1e-10)
    assert rigidity["valid_cut_law"]
    assert rigidity["equilateral_gram_residual"] < 1e-10
