"""Experiment orchestration and certificate export."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
from s2flow.graphs.generators import graph_from_spec
from s2flow.graphs.checks import diagnostics, assert_target_graph
from s2flow.optimizers.cycle_space import solve_cycle_space


def run_experiment(graph_spec: str, dimension: int, restarts: int, seed: int, output: Path | None = None) -> dict[str, object]:
    """Run one finite-instance experiment and optionally save JSON/NPZ certificates."""
    g = graph_from_spec(graph_spec)
    assert_target_graph(g)
    solution = solve_cycle_space(g, dimension=dimension, restarts=restarts, seed=seed)
    report = {"graph": graph_spec, "dimension": dimension, "diagnostics": diagnostics(g), "solver": {"cost": solution.cost, "nfev": solution.nfev}, "metrics": solution.metrics}
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
        np.savez_compressed(output.with_suffix(".npz"), X=solution.x, Y=solution.y)
    return report
