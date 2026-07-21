import networkx as nx
import numpy as np
from s2flow.algebra.incidence import oriented_incidence, cycle_basis_matrix

def test_incidence_columns_sum_to_zero():
    b, _ = oriented_incidence(nx.petersen_graph())
    assert np.allclose(b.sum(axis=0), 0.0)

def test_cycle_basis_is_in_kernel():
    b, z, _ = cycle_basis_matrix(nx.petersen_graph())
    assert np.max(np.abs(b @ z)) < 1e-10
