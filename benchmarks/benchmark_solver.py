"""Minimal solver benchmark."""
from time import perf_counter
from s2flow.graphs.generators import graph_from_spec
from s2flow.optimizers.cycle_space import solve_cycle_space

for spec in ["petersen", "flower:5", "random:20:1"]:
    graph = graph_from_spec(spec)
    start = perf_counter()
    result = solve_cycle_space(graph, restarts=4)
    print(spec, perf_counter() - start, result.metrics["max_unit_norm_residual"])
