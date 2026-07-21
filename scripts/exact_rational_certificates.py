"""Generate dyadic Newton-Kantorovich certificates for flower-snark flows.

The certified square system has rational coefficients.  A vector flow is
written as X = ZY using an integer fundamental-cycle basis Z.  The 6n unit
norm equations are supplemented by three linear gauge equations, producing a
square polynomial system in 6n+3 variables.  The certificate stores dyadic
approximations to Y and an inverse Jacobian.  All inequalities are then
verified with Python arbitrary-precision integers, with no floating-point
step in the verifier.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import networkx as nx
import numpy as np
from scipy.optimize import root

from flower_common import incidence_matrix, stable_graph6


def graph_from_edges(edges: list[tuple[int, int]]) -> nx.Graph:
    graph = nx.Graph()
    graph.add_edges_from(edges)
    return graph


def fundamental_cycle_basis(graph: nx.Graph, edges: list[tuple[int, int]]) -> np.ndarray:
    """Return an integer m by (m-v+1) fundamental-cycle basis."""
    edge_index = {edge: index for index, edge in enumerate(edges)}
    root_vertex = min(graph.nodes())
    tree = nx.bfs_tree(graph, source=root_vertex).to_undirected()
    tree_edges = {tuple(sorted(edge)) for edge in tree.edges()}
    chords = [edge for edge in edges if tuple(sorted(edge)) not in tree_edges]
    basis = np.zeros((len(edges), len(chords)), dtype=np.int8)
    for column, (tail, head) in enumerate(chords):
        basis[edge_index[(tail, head)], column] = 1
        path = nx.shortest_path(tree, source=head, target=tail)
        for source, target in zip(path, path[1:]):
            oriented = (min(source, target), max(source, target))
            coefficient = 1 if (source, target) == oriented else -1
            basis[edge_index[oriented], column] = coefficient
    incidence = incidence_matrix(graph.number_of_nodes(), edges)
    if np.max(np.abs(incidence @ basis.astype(np.int64))) != 0:
        raise AssertionError("Constructed cycle basis is not in the incidence kernel")
    return basis


def gauge_rotate(flow: np.ndarray) -> tuple[np.ndarray, int, int]:
    """Rotate a flow so edge e0 is on x and edge e1 lies in the xy-plane."""
    e0 = 0
    dots = np.abs(flow @ flow[e0])
    e1 = int(np.argmin(dots))
    axis_x = flow[e0] / np.linalg.norm(flow[e0])
    planar = flow[e1] - np.dot(flow[e1], axis_x) * axis_x
    if np.linalg.norm(planar) < 1e-6:
        raise ValueError("Could not choose a nonparallel gauge edge")
    axis_y = planar / np.linalg.norm(planar)
    axis_z = np.cross(axis_x, axis_y)
    frame = np.column_stack([axis_x, axis_y, axis_z])
    return flow @ frame, e0, e1


def polynomial_system(basis: np.ndarray, e0: int, e1: int):
    edge_count, cycle_rank = basis.shape
    dimension = 3 * cycle_rank
    basis_float = basis.astype(float)

    def evaluate(vector: np.ndarray) -> np.ndarray:
        coefficients = vector.reshape(cycle_rank, 3)
        flow = basis_float @ coefficients
        return np.concatenate(
            [
                np.einsum("ij,ij->i", flow, flow) - 1.0,
                [flow[e0, 1], flow[e0, 2], flow[e1, 2]],
            ]
        )

    def jacobian(vector: np.ndarray) -> np.ndarray:
        coefficients = vector.reshape(cycle_rank, 3)
        flow = basis_float @ coefficients
        matrix = np.zeros((dimension, dimension), dtype=float)
        for edge in range(edge_count):
            for coordinate in range(3):
                matrix[edge, coordinate::3] = (
                    2.0 * flow[edge, coordinate] * basis_float[edge]
                )
        matrix[edge_count, 1::3] = basis_float[e0]
        matrix[edge_count + 1, 2::3] = basis_float[e0]
        matrix[edge_count + 2, 2::3] = basis_float[e1]
        return matrix

    return evaluate, jacobian


def refine_candidate(
    basis: np.ndarray, flow: np.ndarray
) -> tuple[np.ndarray, np.ndarray, int, int, float]:
    rotated, e0, e1 = gauge_rotate(flow)
    initial = np.linalg.lstsq(basis.astype(float), rotated, rcond=None)[0].ravel()
    evaluate, jacobian = polynomial_system(basis, e0, e1)
    solution = root(
        evaluate,
        initial,
        jac=jacobian,
        method="lm",
        options={"ftol": 1e-14, "xtol": 1e-14, "gtol": 1e-14, "maxiter": 20000},
    )
    vector = np.asarray(solution.x, dtype=float)
    residual = float(np.max(np.abs(evaluate(vector))))
    matrix = jacobian(vector)
    inverse = np.linalg.inv(matrix)
    return vector, inverse, e0, e1, residual


def exact_certificate_bounds(
    basis: np.ndarray,
    y_num: np.ndarray,
    a_num: np.ndarray,
    y_bits: int,
    a_bits: int,
    e0: int,
    e1: int,
    radius_num: int,
    radius_den: int,
) -> dict[str, Any]:
    """Compute exact rational contraction bounds using Python integers."""
    edge_count, cycle_rank = basis.shape
    dimension = 3 * cycle_rank
    if a_num.shape != (dimension, dimension):
        raise ValueError("Inverse-Jacobian numerator has the wrong shape")
    y_matrix = y_num.reshape(cycle_rank, 3)
    x_num = basis.astype(np.int64) @ y_matrix.astype(np.int64)

    f_num: list[int] = []
    unit_scale = 1 << (2 * y_bits)
    for edge in range(edge_count):
        f_num.append(
            sum(int(x_num[edge, coordinate]) ** 2 for coordinate in range(3))
            - unit_scale
        )
    gauge_scale = 1 << y_bits
    f_num.extend(
        [
            int(x_num[e0, 1]) * gauge_scale,
            int(x_num[e0, 2]) * gauge_scale,
            int(x_num[e1, 2]) * gauge_scale,
        ]
    )

    jacobian_num = np.zeros((dimension, dimension), dtype=np.int64)
    for edge in range(edge_count):
        for coordinate in range(3):
            jacobian_num[edge, coordinate::3] = (
                2 * int(x_num[edge, coordinate]) * basis[edge].astype(np.int64)
            )
    jacobian_num[edge_count, 1::3] = basis[e0].astype(np.int64) * gauge_scale
    jacobian_num[edge_count + 1, 2::3] = basis[e0].astype(np.int64) * gauge_scale
    jacobian_num[edge_count + 2, 2::3] = basis[e1].astype(np.int64) * gauge_scale

    a_object = a_num.astype(object)
    f_object = np.asarray(f_num, dtype=object)
    correction = a_object @ f_object
    alpha_num = max(abs(int(value)) for value in correction)
    alpha_den = 1 << (a_bits + 2 * y_bits)

    product = a_object @ jacobian_num.astype(object)
    beta_den = 1 << (a_bits + y_bits)
    beta_num = 0
    for row in range(dimension):
        row_sum = 0
        for column in range(dimension):
            identity_term = beta_den if row == column else 0
            row_sum += abs(identity_term - int(product[row, column]))
        beta_num = max(beta_num, row_sum)

    support_sizes = np.sum(np.abs(basis.astype(np.int64)), axis=1)
    lipschitz_num = 0
    for row in range(dimension):
        row_bound = 6 * sum(
            abs(int(a_num[row, edge])) * int(support_sizes[edge]) ** 2
            for edge in range(edge_count)
        )
        lipschitz_num = max(lipschitz_num, row_bound)
    lipschitz_den = 1 << a_bits

    common_den = (
        alpha_den * beta_den * lipschitz_den * radius_den * radius_den
    )
    polynomial_num = (
        alpha_num * (common_den // alpha_den)
        + (beta_num - beta_den)
        * radius_num
        * (common_den // (beta_den * radius_den))
        + lipschitz_num
        * radius_num
        * radius_num
        * (common_den // (lipschitz_den * radius_den * radius_den))
    )
    contraction_num = (
        beta_num * lipschitz_den * radius_den
        + lipschitz_num * radius_num * beta_den
    )
    contraction_den = beta_den * lipschitz_den * radius_den

    return {
        "alpha_num": alpha_num,
        "alpha_den": alpha_den,
        "beta_num": beta_num,
        "beta_den": beta_den,
        "lipschitz_num": lipschitz_num,
        "lipschitz_den": lipschitz_den,
        "radius_num": radius_num,
        "radius_den": radius_den,
        "radii_polynomial_num": polynomial_num,
        "radii_polynomial_den": common_den,
        "contraction_num": contraction_num,
        "contraction_den": contraction_den,
        "certified": polynomial_num < 0 and contraction_num < contraction_den,
    }


def generate_certificate(
    flow_path: Path,
    output_path: Path,
    y_bits: int = 40,
    a_bits: int = 40,
    radius_num: int = 1,
    radius_den: int = 100_000_000,
) -> dict[str, Any]:
    data = np.load(flow_path, allow_pickle=False)
    edges = [tuple(int(value) for value in edge) for edge in data["edges"].tolist()]
    flow = np.asarray(data["X"], dtype=float)
    graph = graph_from_edges(edges)
    basis = fundamental_cycle_basis(graph, edges)
    y, inverse, e0, e1, residual = refine_candidate(basis, flow)

    y_num = np.rint(y * (1 << y_bits)).astype(np.int64)
    a_scaled = inverse * (1 << a_bits)
    if np.max(np.abs(a_scaled)) >= np.iinfo(np.int64).max:
        raise OverflowError("Increase certificate storage width")
    a_num = np.rint(a_scaled).astype(np.int64)
    bounds = exact_certificate_bounds(
        basis,
        y_num,
        a_num,
        y_bits,
        a_bits,
        e0,
        e1,
        radius_num,
        radius_den,
    )
    if not bounds["certified"]:
        raise RuntimeError(f"Certificate failed for {flow_path}: {bounds}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        output_path,
        edges=np.asarray(edges, dtype=np.int64),
        graph6=np.array([stable_graph6(graph)]),
        Z=basis,
        y_num=y_num,
        A_num=a_num,
        y_bits=np.array([y_bits], dtype=np.int64),
        A_bits=np.array([a_bits], dtype=np.int64),
        gauge_edges=np.array([e0, e1], dtype=np.int64),
        radius=np.array([radius_num, radius_den], dtype=np.int64),
        source_file=np.array([flow_path.name]),
    )
    return {
        "certificate": str(output_path),
        "source": str(flow_path),
        "vertices": graph.number_of_nodes(),
        "edges": graph.number_of_edges(),
        "cycle_rank": basis.shape[1],
        "dimension": 3 * basis.shape[1],
        "floating_refinement_residual": residual,
        "alpha": bounds["alpha_num"] / bounds["alpha_den"],
        "beta": bounds["beta_num"] / bounds["beta_den"],
        "lipschitz": bounds["lipschitz_num"] / bounds["lipschitz_den"],
        "radius": radius_num / radius_den,
        "radii_polynomial": bounds["radii_polynomial_num"]
        / bounds["radii_polynomial_den"],
        "contraction_bound": bounds["contraction_num"] / bounds["contraction_den"],
        "certified": bool(bounds["certified"]),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--flow-dir", type=Path, default=Path("data/equivariant_flows"))
    parser.add_argument("--output-dir", type=Path, default=Path("certificates"))
    parser.add_argument("--summary", type=Path, default=Path("results/exact_certificates.json"))
    parser.add_argument("--min-n", type=int, default=5)
    parser.add_argument("--max-n", type=int, default=41)
    parser.add_argument("--y-bits", type=int, default=40)
    parser.add_argument("--a-bits", type=int, default=40)
    parser.add_argument("--radius-den", type=int, default=100_000_000)
    args = parser.parse_args()

    records = []
    for n in range(args.min_n, args.max_n + 1, 2):
        flow_path = args.flow_dir / f"flower_J{n}_zn_k1.npz"
        output_path = args.output_dir / f"flower_J{n}_exact_dyadic.npz"
        record = generate_certificate(
            flow_path,
            output_path,
            y_bits=args.y_bits,
            a_bits=args.a_bits,
            radius_den=args.radius_den,
        )
        records.append(record)
        print(
            f"J_{n}: certified={record['certified']}, "
            f"p(r)={record['radii_polynomial']:.3e}, "
            f"q={record['contraction_bound']:.3e}"
        )

    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(json.dumps(records, indent=2), encoding="utf-8")
    print(f"Saved {args.summary}")


if __name__ == "__main__":
    main()
