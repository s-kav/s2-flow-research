import networkx as nx
from s2flow.algebra.incidence import cycle_basis_matrix
from s2flow.optimizers.cycle_space import solve_cycle_space

def test_petersen_numerical_candidate():
    g = nx.petersen_graph()
    result = solve_cycle_space(g, dimension=3, restarts=4, seed=7, max_nfev=5000, tolerance=1e-8)
    assert result.metrics["max_conservation_residual"] < 1e-8
    assert result.metrics["max_unit_norm_residual"] < 1e-6
