import networkx as nx
import pytest
from s2flow.graphs.checks import assert_target_graph

def test_path_is_rejected():
    with pytest.raises(ValueError):
        assert_target_graph(nx.path_graph(4))
