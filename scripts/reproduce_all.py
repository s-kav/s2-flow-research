"""Run a small deterministic reproduction suite."""
from pathlib import Path
from s2flow.experiments.runner import run_experiment

def main() -> None:
    jobs = [("petersen", 3, 12), ("flower:5", 3, 12), ("random:20:1", 3, 8)]
    for graph, dimension, restarts in jobs:
        name = graph.replace(":", "_")
        report = run_experiment(graph, dimension, restarts, 20260717, Path(f"results/json/{name}_d{dimension}.json"))
        print(graph, report["metrics"]["valid"], report["metrics"]["max_unit_norm_residual"])

if __name__ == "__main__":
    main()
