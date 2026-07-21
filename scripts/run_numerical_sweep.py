#!/usr/bin/env python3
"""Solve and verify Goldberg flows for a configurable finite test range."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from goldberg_s2.construction import build_templates, scalar_parameter_x, solve_scalar_root
from goldberg_s2.verify import verify_full_flow, verify_reduced_templates


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-k", type=int, default=1001)
    parser.add_argument("--full-max-k", type=int, default=301)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("certificates/numerical_sweep.csv"),
    )
    return parser.parse_args()


def main() -> None:
    """Run the finite verification sweep and write a CSV report."""
    args = parse_args()
    if args.max_k < 5:
        raise ValueError("max-k must be at least 5")

    rows: list[dict[str, object]] = []
    for k in range(5, args.max_k + 1, 2):
        root = solve_scalar_root(k)
        templates = build_templates(k, root)
        reduced_kirchhoff, reduced_norm = verify_reduced_templates(k, templates)

        row: dict[str, object] = {
            "k": k,
            "x": scalar_parameter_x(k),
            "scalar_root": root,
            "reduced_kirchhoff": reduced_kirchhoff,
            "reduced_norm": reduced_norm,
            "full_verified": False,
            "full_kirchhoff": "",
            "full_norm": "",
            "vertices": 8 * k,
            "edges": 12 * k,
        }

        if k <= args.full_max_k:
            full = verify_full_flow(k, templates)
            row.update(
                {
                    "full_verified": True,
                    "full_kirchhoff": full.max_kirchhoff_residual,
                    "full_norm": full.max_unit_norm_residual,
                    "vertices": full.vertices,
                    "edges": full.edges,
                }
            )
        rows.append(row)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    worst_reduced_kirchhoff = max(float(row["reduced_kirchhoff"]) for row in rows)
    worst_reduced_norm = max(float(row["reduced_norm"]) for row in rows)
    full_rows = [row for row in rows if row["full_verified"]]
    worst_full_kirchhoff = max(float(row["full_kirchhoff"]) for row in full_rows)
    worst_full_norm = max(float(row["full_norm"]) for row in full_rows)

    print(f"Odd k tested: {len(rows)} (5 through {args.max_k})")
    print(f"Full graphs tested: {len(full_rows)} (through {args.full_max_k})")
    print(f"Worst reduced Kirchhoff residual: {worst_reduced_kirchhoff:.3e}")
    print(f"Worst reduced unit residual: {worst_reduced_norm:.3e}")
    print(f"Worst full Kirchhoff residual: {worst_full_kirchhoff:.3e}")
    print(f"Worst full unit residual: {worst_full_norm:.3e}")
    print(f"CSV: {args.output}")


if __name__ == "__main__":
    main()
