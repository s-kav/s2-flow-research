#!/usr/bin/env python3
"""Generate the exact rational interval certificate used by the theorem."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from goldberg_s2.interval_proof import generate_interval_certificate


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("certificates/interval_proof_certificate.json"),
    )
    parser.add_argument("--bits", type=int, default=112)
    parser.add_argument("--endpoint-pieces", type=int, default=16)
    parser.add_argument("--derivative-s-pieces", type=int, default=32)
    parser.add_argument("--derivative-x-pieces", type=int, default=32)
    return parser.parse_args()


def main() -> None:
    """Generate, serialize, and hash the exact certificate."""
    args = parse_args()
    certificate = generate_interval_certificate(
        endpoint_pieces=args.endpoint_pieces,
        derivative_s_pieces=args.derivative_s_pieces,
        derivative_x_pieces=args.derivative_x_pieces,
        bits=args.bits,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(certificate, indent=2, sort_keys=True) + "\n"
    args.output.write_text(payload, encoding="utf-8")
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()

    print(f"Certificate: {args.output}")
    print(f"SHA-256: {digest}")
    print(json.dumps(certificate["summary"], indent=2))


if __name__ == "__main__":
    main()
