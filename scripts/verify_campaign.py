#!/usr/bin/env python3
"""Independently re-verify every numerical certificate in a campaign directory."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import networkx as nx
import numpy as np

from s2flow.algebra.incidence import oriented_incidence
from s2flow.flows.verification import verify_candidate


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("campaign_dir", type=Path)
    parser.add_argument("--tolerance", type=float, default=1e-7)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    certificate_files = sorted((args.campaign_dir / "certificates").glob("*.npz"))
    failures: list[dict[str, object]] = []
    for path in certificate_files:
        payload = np.load(path, allow_pickle=True)
        graph6 = str(payload["graph6"][0])
        graph = nx.from_graph6_bytes(graph6.encode("ascii"))
        b, edge_order = oriented_incidence(graph)
        stored_edges = [tuple(edge) for edge in payload["edges"].tolist()]
        if stored_edges != edge_order:
            failures.append({"certificate": path.name, "reason": "edge_order_mismatch"})
            continue
        metrics = verify_candidate(b, payload["X"], tolerance=args.tolerance)
        if not metrics["valid"]:
            failures.append({"certificate": path.name, "reason": "invalid_flow", "metrics": metrics})
    result = {
        "certificates": len(certificate_files),
        "valid": len(certificate_files) - len(failures),
        "failures": failures,
    }
    output = args.campaign_dir / "independent_verification.json"
    output.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(1 if failures else 0)


if __name__ == "__main__":
    main()
