"""Command-line interface."""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
from s2flow.experiments.runner import run_experiment
from s2flow.graphs.generators import graph_from_spec
from s2flow.algebra.incidence import oriented_incidence
from s2flow.flows.verification import verify_candidate


def main() -> None:
    parser = argparse.ArgumentParser(prog="s2flow")
    sub = parser.add_subparsers(dest="command", required=True)
    analyze = sub.add_parser("analyze")
    analyze.add_argument("--graph", default="petersen")
    analyze.add_argument("--dimension", type=int, default=3)
    analyze.add_argument("--restarts", type=int, default=12)
    analyze.add_argument("--seed", type=int, default=20260717)
    analyze.add_argument("--output", type=Path)
    verify = sub.add_parser("verify")
    verify.add_argument("--graph", required=True)
    verify.add_argument("--certificate", type=Path, required=True)
    verify.add_argument("--tolerance", type=float, default=1e-8)
    args = parser.parse_args()
    if args.command == "analyze":
        print(json.dumps(run_experiment(args.graph, args.dimension, args.restarts, args.seed, args.output), indent=2))
    else:
        g = graph_from_spec(args.graph)
        b, _ = oriented_incidence(g)
        with np.load(args.certificate) as data:
            metrics = verify_candidate(b, data["X"], args.tolerance)
        print(json.dumps(metrics, indent=2))
        raise SystemExit(0 if metrics["valid"] else 2)

if __name__ == "__main__":
    main()
