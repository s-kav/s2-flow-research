"""Ensure graph serialization preserves the explicit certificate labels."""

import sys
from pathlib import Path

import networkx as nx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from flower_common import canonical_relabelled, stable_graph6


def test_stable_graph6_matches_edges():
    graph, edges, _ = canonical_relabelled(15)
    decoded = nx.from_graph6_bytes(stable_graph6(graph).encode("ascii"))
    assert sorted(tuple(sorted(edge)) for edge in decoded.edges()) == edges
