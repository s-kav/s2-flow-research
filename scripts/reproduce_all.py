#!/usr/bin/env python3
"""Run the exact proof, finite sweep, and test suite in one command."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def run(command: list[str], root: Path) -> None:
    """Run one command and fail immediately on errors."""
    print("+", " ".join(command), flush=True)
    subprocess.run(command, cwd=root, check=True)


def main() -> None:
    """Execute the full reproducibility pipeline."""
    root = Path(__file__).resolve().parents[1]
    environment = os.environ.copy()
    source_path = str(root / "src")
    environment["PYTHONPATH"] = source_path + os.pathsep + environment.get("PYTHONPATH", "")

    commands = [
        [sys.executable, "scripts/run_interval_proof.py"],
        [sys.executable, "scripts/verify_interval_certificate.py"],
        [
            sys.executable,
            "scripts/run_numerical_sweep.py",
            "--max-k",
            "1001",
            "--full-max-k",
            "301",
        ],
        [sys.executable, "scripts/verify_one.py", "1001"],
        [sys.executable, "scripts/make_figures.py"],
        [sys.executable, "scripts/build_report.py"],
        [sys.executable, "-m", "pytest"],
    ]
    for command in commands:
        print("+", " ".join(command), flush=True)
        subprocess.run(command, cwd=root, check=True, env=environment)


if __name__ == "__main__":
    main()
