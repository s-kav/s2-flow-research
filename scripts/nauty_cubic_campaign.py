#!/usr/bin/env python3
"""Process exhaustive cubic graph6 streams produced by nauty's geng.

Example:
    geng -c -d3 -D3 16 | python scripts/nauty_cubic_campaign.py --output-dir results/geng16
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import networkx as nx

from s2flow.computation.massive import MassiveConfig, _solve_one


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--seed", type=int, default=20260718)
    parser.add_argument("--nonlinear-restarts", type=int, default=12)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    config = MassiveConfig(
        orders=(),
        samples_per_order=0,
        seed=args.seed,
        nonlinear_restarts=args.nonlinear_restarts,
        include_families=False,
    )
    records = []
    for index, line in enumerate(sys.stdin):
        line = line.strip()
        if not line or line.startswith(">>"):
            continue
        if args.limit and len(records) >= args.limit:
            break
        graph = nx.from_graph6_bytes(line.encode("ascii"))
        if not nx.is_connected(graph) or any(degree != 3 for _, degree in graph.degree()):
            continue
        if list(nx.bridges(graph)):
            continue
        report, _, _ = _solve_one(f"geng_{index}", graph, config, args.seed + index)
        records.append(report)
    output = args.output_dir / "records.json"
    output.write_text(json.dumps(records, indent=2, sort_keys=True), encoding="utf-8")
    failures = sum(not bool(record["valid_s2_certificate"]) for record in records)
    print(f"Processed: {len(records)}")
    print(f"Failures: {failures}")
    raise SystemExit(1 if failures else 0)


if __name__ == "__main__":
    main()
