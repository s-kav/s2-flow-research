import networkx as nx
import numpy as np
from s2flow.algebra.incidence import cycle_basis_matrix
from s2flow.proof.lemmas.lemma01_cycle_lifting import verify_cycle_lifting
from s2flow.proof.lemmas.lemma02_matching import perfect_matching_and_two_factor
from s2flow.proof.lemmas.lemma04_psd_rank import gram_diagnostics
from s2flow.proof.lemmas.lemma05_rotation import infinitesimal_rotation_directions
from s2flow.proof.lemmas.lemma06_local_extension import local_extension_diagnostics
from s2flow.proof.search.induction import InductionNode, verify_induction_plan


def test_cycle_lifting_is_conservative():
    graph = nx.petersen_graph()
    _, z, _ = cycle_basis_matrix(graph)
    coordinates = np.ones((z.shape[1], 3))
    assert verify_cycle_lifting(graph, coordinates)["valid"]


def test_matching_complement_is_two_factor():
    matching, two_factor = perfect_matching_and_two_factor(nx.petersen_graph())
    assert len(matching) == 5
    assert all(degree == 2 for _, degree in two_factor.degree())


def test_rank_and_rotation_helpers():
    vectors = np.eye(3)
    assert gram_diagnostics(vectors)["rank"] == 3
    assert infinitesimal_rotation_directions(vectors).shape == (3, 9)


def test_local_extension_and_induction_plan():
    first = np.array([1.0, 0.0, 0.0])
    second = np.array([-0.5, np.sqrt(3.0) / 2.0, 0.0])
    assert local_extension_diagnostics(first, second)["extendable"]
    plan = [InductionNode("base", True), InductionNode("step", True, ["base"])]
    assert verify_induction_plan(plan)["valid"]
