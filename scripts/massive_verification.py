#!/usr/bin/env python3
"""Run deterministic large-scale S2-flow verification campaigns."""
from __future__ import annotations

import argparse
from pathlib import Path

from s2flow.computation.massive import MassiveConfig, run_massive_verification


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--orders", nargs="+", type=int, default=[10, 12, 14, 16, 18, 20, 24, 30, 40])
    parser.add_argument("--samples-per-order", type=int, default=50)
    parser.add_argument("--seed", type=int, default=20260718)
    parser.add_argument("--edge-coloring-max-nodes", type=int, default=2_000_000)
    parser.add_argument("--nonlinear-restarts", type=int, default=12)
    parser.add_argument("--nonlinear-max-nfev", type=int, default=20_000)
    parser.add_argument("--tolerance", type=float, default=1e-8)
    parser.add_argument("--skip-families", action="store_true")
    parser.add_argument("--output-dir", type=Path, default=Path("results/massive"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = MassiveConfig(
        orders=tuple(args.orders),
        samples_per_order=args.samples_per_order,
        seed=args.seed,
        edge_coloring_max_nodes=args.edge_coloring_max_nodes,
        nonlinear_restarts=args.nonlinear_restarts,
        nonlinear_max_nfev=args.nonlinear_max_nfev,
        tolerance=args.tolerance,
        include_families=not args.skip_families,
    )
    summary = run_massive_verification(config, args.output_dir)
    print(f"Instances: {summary['instances']}")
    print(f"Valid certificates: {summary['valid_certificates']}")
    print(f"Exact constructive certificates: {summary['exact_constructive_certificates']}")
    print(f"Nonlinear certificates: {summary['nonlinear_certificates']}")
    print(f"Failures: {summary['failures']}")
    print(f"Output: {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()
