import networkx as nx
from s2flow.graphs.generators import flower_snark
from s2flow.graphs.checks import diagnostics

def test_petersen_is_target_graph():
    d = diagnostics(nx.petersen_graph())
    assert d["connected"] and d["cubic"] and d["bridgeless"]

def test_flower_j5_is_cubic_bridgeless():
    d = diagnostics(flower_snark(5))
    assert d["vertices"] == 20
    assert d["cubic"] and d["bridgeless"]
