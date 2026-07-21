#!/usr/bin/env python3
"""Independently recompute and verify the stored interval certificate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from goldberg_s2.interval_proof import verify_interval_certificate


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "certificate",
        type=Path,
        nargs="?",
        default=Path("certificates/interval_proof_certificate.json"),
    )
    return parser.parse_args()


def main() -> None:
    """Load the certificate and verify every exact enclosure."""
    args = parse_args()
    certificate = json.loads(args.certificate.read_text(encoding="utf-8"))
    summary = verify_interval_certificate(certificate)
    print("Exact interval certificate verified.")
    for key, value in summary.items():
        print(f"{key}: {value} ({float(value):.12g})")


if __name__ == "__main__":
    main()
