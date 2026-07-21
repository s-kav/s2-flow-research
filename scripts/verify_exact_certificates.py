"""Independent exact verifier for dyadic flower-snark certificates.

The verifier does not use SciPy and performs every decisive computation with
Python arbitrary-precision integers.  It reconstructs the incidence kernel,
the polynomial residual, the Jacobian, the approximate-inverse defect, the
Jacobian Lipschitz bound, and both Newton-Kantorovich inequalities.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import networkx as nx
import numpy as np


def verify_one(path: Path) -> dict[str, Any]:
    data = np.load(path, allow_pickle=False)
    edges = [tuple(int(value) for value in edge) for edge in data["edges"].tolist()]
    basis = np.asarray(data["Z"], dtype=np.int64)
    y_num = np.asarray(data["y_num"], dtype=np.int64)
    a_num = np.asarray(data["A_num"], dtype=np.int64)
    y_bits = int(data["y_bits"][0])
    a_bits = int(data["A_bits"][0])
    e0, e1 = (int(value) for value in data["gauge_edges"])
    radius_num, radius_den = (int(value) for value in data["radius"])

    graph = nx.Graph()
    graph.add_edges_from(edges)
    node_count = graph.number_of_nodes()
    edge_count = len(edges)
    cycle_rank = basis.shape[1]
    dimension = 3 * cycle_rank
    if basis.shape[0] != edge_count:
        raise ValueError("Cycle basis and edge list disagree")
    if y_num.shape != (dimension,):
        raise ValueError("Coefficient numerator has the wrong dimension")
    if a_num.shape != (dimension, dimension):
        raise ValueError("Approximate inverse has the wrong dimension")
    if dimension != edge_count + 3:
        raise ValueError("The gauge-fixed system is not square")

    incidence = np.zeros((node_count, edge_count), dtype=np.int64)
    for index, (tail, head) in enumerate(edges):
        incidence[tail, index] = 1
        incidence[head, index] = -1
    kernel_defect = incidence @ basis
    if np.max(np.abs(kernel_defect)) != 0:
        raise AssertionError("Z is not an exact incidence-kernel basis")
    # A full rank modulo one prime proves full column rank over the rationals.
    prime = 2_147_483_647
    modular = [[int(value) % prime for value in row] for row in basis.tolist()]
    rank = 0
    for column in range(cycle_rank):
        pivot = next((row for row in range(rank, edge_count) if modular[row][column]), None)
        if pivot is None:
            continue
        modular[rank], modular[pivot] = modular[pivot], modular[rank]
        inverse = pow(modular[rank][column], prime - 2, prime)
        modular[rank] = [(value * inverse) % prime for value in modular[rank]]
        for row in range(edge_count):
            if row != rank and modular[row][column]:
                factor = modular[row][column]
                modular[row] = [
                    (modular[row][col] - factor * modular[rank][col]) % prime
                    for col in range(cycle_rank)
                ]
        rank += 1
    if rank != cycle_rank:
        raise AssertionError("Z does not have exact full column rank")

    y_matrix = y_num.reshape(cycle_rank, 3)
    x_num = basis @ y_matrix
    unit_den = 1 << (2 * y_bits)
    f_num: list[int] = []
    for edge in range(edge_count):
        f_num.append(
            sum(int(x_num[edge, coordinate]) ** 2 for coordinate in range(3))
            - unit_den
        )
    gauge_factor = 1 << y_bits
    f_num.extend(
        [
            int(x_num[e0, 1]) * gauge_factor,
            int(x_num[e0, 2]) * gauge_factor,
            int(x_num[e1, 2]) * gauge_factor,
        ]
    )

    jacobian_num = np.zeros((dimension, dimension), dtype=np.int64)
    for edge in range(edge_count):
        for coordinate in range(3):
            jacobian_num[edge, coordinate::3] = (
                2 * int(x_num[edge, coordinate]) * basis[edge]
            )
    jacobian_num[edge_count, 1::3] = basis[e0] * gauge_factor
    jacobian_num[edge_count + 1, 2::3] = basis[e0] * gauge_factor
    jacobian_num[edge_count + 2, 2::3] = basis[e1] * gauge_factor

    correction = a_num.astype(object) @ np.asarray(f_num, dtype=object)
    alpha_num = max(abs(int(value)) for value in correction)
    alpha_den = 1 << (a_bits + 2 * y_bits)

    inverse_product = a_num.astype(object) @ jacobian_num.astype(object)
    beta_den = 1 << (a_bits + y_bits)
    beta_num = 0
    for row in range(dimension):
        row_sum = 0
        for column in range(dimension):
            identity = beta_den if row == column else 0
            row_sum += abs(identity - int(inverse_product[row, column]))
        beta_num = max(beta_num, row_sum)

    support_sizes = np.sum(np.abs(basis), axis=1)
    lipschitz_num = 0
    for row in range(dimension):
        candidate = 6 * sum(
            abs(int(a_num[row, edge])) * int(support_sizes[edge]) ** 2
            for edge in range(edge_count)
        )
        lipschitz_num = max(lipschitz_num, candidate)
    lipschitz_den = 1 << a_bits

    common_den = alpha_den * beta_den * lipschitz_den * radius_den**2
    radii_num = (
        alpha_num * (common_den // alpha_den)
        + (beta_num - beta_den)
        * radius_num
        * (common_den // (beta_den * radius_den))
        + lipschitz_num
        * radius_num**2
        * (common_den // (lipschitz_den * radius_den**2))
    )
    contraction_num = (
        beta_num * lipschitz_den * radius_den
        + lipschitz_num * radius_num * beta_den
    )
    contraction_den = beta_den * lipschitz_den * radius_den
    certified = radii_num < 0 and contraction_num < contraction_den

    return {
        "file": str(path),
        "vertices": node_count,
        "edges": edge_count,
        "dimension": dimension,
        "alpha": alpha_num / alpha_den,
        "beta": beta_num / beta_den,
        "lipschitz": lipschitz_num / lipschitz_den,
        "radius": radius_num / radius_den,
        "radii_polynomial": radii_num / common_den,
        "contraction_bound": contraction_num / contraction_den,
        "certified": certified,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--certificate-dir", type=Path, default=Path("certificates"))
    parser.add_argument("--output", type=Path, default=Path("results/independent_exact_verification.json"))
    args = parser.parse_args()

    paths = sorted(
        args.certificate_dir.glob("flower_J*_exact_dyadic.npz"),
        key=lambda path: int(path.name.split("J", 1)[1].split("_", 1)[0]),
    )
    if not paths:
        raise FileNotFoundError(f"No certificates found in {args.certificate_dir}")
    records = [verify_one(path) for path in paths]
    if not all(record["certified"] for record in records):
        failed = [record["file"] for record in records if not record["certified"]]
        raise RuntimeError(f"Exact verification failed: {failed}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(records, indent=2), encoding="utf-8")
    print(f"Verified {len(records)} exact dyadic certificates")
    print(f"Saved {args.output}")


if __name__ == "__main__":
    main()
