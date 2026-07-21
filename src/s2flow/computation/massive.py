"""Deterministic large-scale finite-instance verification pipeline."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import platform
from pathlib import Path
import random
import sys
import time
from typing import Iterable

import networkx as nx
import numpy as np
import scipy

from s2flow.algebra.incidence import oriented_incidence
from s2flow.flows.verification import verify_candidate
from s2flow.graphs.checks import diagnostics
from s2flow.graphs.generators import flower_snark
from s2flow.optimizers.cycle_space import solve_cycle_space
from s2flow.proof.theory.cycle_cover import (
    construct_s2_flow_from_three_edge_coloring,
    find_three_edge_coloring,
)


@dataclass(frozen=True)
class MassiveConfig:
    """Configuration for a deterministic finite-instance campaign."""

    orders: tuple[int, ...] = (10, 12, 14, 16, 18, 20, 24, 30, 40)
    samples_per_order: int = 50
    seed: int = 20260718
    edge_coloring_max_nodes: int = 2_000_000
    nonlinear_restarts: int = 12
    nonlinear_max_nfev: int = 20_000
    tolerance: float = 1e-8
    include_families: bool = True
    flower_parameters: tuple[int, ...] = (5, 7, 9, 11, 13)
    generalized_petersen_parameters: tuple[tuple[int, int], ...] = (
        (5, 2),
        (7, 2),
        (8, 3),
        (9, 2),
        (10, 2),
        (10, 3),
        (12, 5),
        (15, 4),
    )


def _graph_digest(graph: nx.Graph) -> str:
    encoded = nx.to_graph6_bytes(graph, header=False).strip()
    return hashlib.sha256(encoded).hexdigest()


def _is_target(graph: nx.Graph) -> bool:
    return (
        nx.is_connected(graph)
        and all(degree == 3 for _, degree in graph.degree())
        and not list(nx.bridges(graph))
        and nx.number_of_selfloops(graph) == 0
    )


def _random_targets(config: MassiveConfig) -> Iterable[tuple[str, nx.Graph]]:
    rng = random.Random(config.seed)
    for order in config.orders:
        if order % 2 != 0 or order < 4:
            continue
        accepted = 0
        attempts = 0
        while accepted < config.samples_per_order:
            attempts += 1
            graph_seed = rng.randrange(0, 2**32 - 1)
            graph = nx.random_regular_graph(3, order, seed=graph_seed)
            if not _is_target(graph):
                if attempts > config.samples_per_order * 100:
                    raise RuntimeError(f"Unable to sample enough target graphs of order {order}.")
                continue
            yield f"random_n{order}_seed{graph_seed}", graph
            accepted += 1


def _family_targets(config: MassiveConfig) -> Iterable[tuple[str, nx.Graph]]:
    yield "petersen", nx.petersen_graph()
    yield "k4", nx.complete_graph(4)
    yield "k33", nx.complete_bipartite_graph(3, 3)
    yield "heawood", nx.heawood_graph()
    yield "desargues", nx.desargues_graph()
    for n in config.flower_parameters:
        yield f"flower_J{n}", flower_snark(n)
    for n, k in config.generalized_petersen_parameters:
        graph = nx.generalized_petersen_graph(n, k)
        if _is_target(graph):
            yield f"generalized_petersen_{n}_{k}", graph


def _solve_one(name: str, graph: nx.Graph, config: MassiveConfig, instance_seed: int) -> tuple[dict[str, object], np.ndarray | None, list[tuple[int, int]] | None]:
    # Canonical integer labels make graph6 and stored edge orders independently reproducible.
    graph = nx.convert_node_labels_to_integers(graph, ordering="default")
    started = time.perf_counter()
    colouring = find_three_edge_coloring(
        graph,
        max_search_nodes=config.edge_coloring_max_nodes,
    )
    method = ""
    x: np.ndarray | None = None
    edge_order: list[tuple[int, int]] | None = None
    solver_cost = None
    solver_nfev = None

    if colouring.status == "colourable" and colouring.colors is not None:
        x, edge_order, metrics = construct_s2_flow_from_three_edge_coloring(
            graph,
            colouring.colors,
            tolerance=config.tolerance,
        )
        method = "exact_three_edge_colouring_construction"
    else:
        solution = solve_cycle_space(
            graph,
            dimension=3,
            restarts=config.nonlinear_restarts,
            seed=instance_seed,
            max_nfev=config.nonlinear_max_nfev,
            tolerance=config.tolerance,
        )
        x = solution.x
        _, edge_order = oriented_incidence(graph)
        metrics = solution.metrics
        solver_cost = solution.cost
        solver_nfev = solution.nfev
        method = "cycle_space_nonlinear_least_squares"

    elapsed = time.perf_counter() - started
    report = {
        "name": name,
        "graph_sha256": _graph_digest(graph),
        **diagnostics(graph),
        "three_edge_coloring_status": colouring.status,
        "three_edge_coloring_search_nodes": colouring.search_nodes,
        "method": method,
        "valid_s2_certificate": bool(metrics["valid"]),
        "max_conservation_residual": float(metrics["max_conservation_residual"]),
        "max_unit_norm_residual": float(metrics["max_unit_norm_residual"]),
        "gram_rank": int(metrics["gram_rank"]),
        "solver_cost": solver_cost,
        "solver_nfev": solver_nfev,
        "elapsed_seconds": elapsed,
    }
    return report, x, edge_order


def _write_csv(path: Path, records: list[dict[str, object]]) -> None:
    import csv

    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = sorted({key for record in records for key in record})
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)


def run_massive_verification(config: MassiveConfig, output_dir: Path) -> dict[str, object]:
    """Run a deterministic campaign and persist independently checkable artefacts."""
    output_dir.mkdir(parents=True, exist_ok=True)
    certificates_dir = output_dir / "certificates"
    certificates_dir.mkdir(exist_ok=True)

    targets = list(_random_targets(config))
    if config.include_families:
        targets = list(_family_targets(config)) + targets

    records: list[dict[str, object]] = []
    campaign_start = time.perf_counter()
    for index, (name, graph) in enumerate(targets):
        report, x, edge_order = _solve_one(name, graph, config, config.seed + index)
        records.append(report)
        graph6 = nx.to_graph6_bytes(graph, header=False).decode("ascii").strip()
        certificate_path = certificates_dir / f"{index:05d}_{name}.npz"
        np.savez_compressed(
            certificate_path,
            X=x if x is not None else np.empty((0, 3)),
            edges=np.asarray(edge_order if edge_order is not None else [], dtype=object),
            graph6=np.asarray([graph6]),
        )

    elapsed = time.perf_counter() - campaign_start
    _write_csv(output_dir / "summary.csv", records)
    valid_count = sum(bool(record["valid_s2_certificate"]) for record in records)
    exact_count = sum(
        record["method"] == "exact_three_edge_colouring_construction" for record in records
    )
    numerical_count = len(records) - exact_count
    failures = [record for record in records if not record["valid_s2_certificate"]]
    summary = {
        "config": asdict(config),
        "environment": {
            "python": sys.version,
            "platform": platform.platform(),
            "networkx": nx.__version__,
            "numpy": np.__version__,
            "scipy": scipy.__version__,
        },
        "instances": len(records),
        "valid_certificates": valid_count,
        "exact_constructive_certificates": exact_count,
        "nonlinear_certificates": numerical_count,
        "failures": len(failures),
        "elapsed_seconds": elapsed,
        "maximum_conservation_residual": max(
            (float(record["max_conservation_residual"]) for record in records),
            default=0.0,
        ),
        "maximum_unit_norm_residual": max(
            (float(record["max_unit_norm_residual"]) for record in records),
            default=0.0,
        ),
        "failure_records": failures,
    }
    (output_dir / "campaign.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True, default=list),
        encoding="utf-8",
    )
    return summary
