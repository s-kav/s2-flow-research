"""Export canonical graphs to GraphML."""
from pathlib import Path
import networkx as nx
from s2flow.graphs.generators import flower_snark

def main() -> None:
    out = Path("data/graphs")
    out.mkdir(parents=True, exist_ok=True)
    nx.write_graphml(nx.petersen_graph(), out / "petersen.graphml")
    nx.write_graphml(flower_snark(5), out / "flower_j5.graphml")

if __name__ == "__main__":
    main()
