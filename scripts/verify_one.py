#!/usr/bin/env python3
"""Build and verify one Goldberg S^2-flow instance."""

from __future__ import annotations

import argparse
import json

from goldberg_s2.construction import build_templates, solve_scalar_root
from goldberg_s2.verify import verify_full_flow


def main() -> None:
    """Run one full-graph verification."""
    parser = argparse.ArgumentParser()
    parser.add_argument("k", type=int)
    args = parser.parse_args()

    root = solve_scalar_root(args.k)
    templates = build_templates(args.k, root)
    result = verify_full_flow(args.k, templates)
    payload = result.to_dict()
    payload["scalar_root"] = root
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
