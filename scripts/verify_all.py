"""Run the complete reproducibility verification pipeline."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def run(command: list[str], cwd: Path) -> None:
    print("+", " ".join(command))
    subprocess.run(command, cwd=cwd, check=True)


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    python = sys.executable
    run([python, "scripts/strict_ansatz_exact.py"], root)
    run([python, "scripts/equivariance_all_generators.py"], root)
    run([python, "scripts/verify_exact_certificates.py"], root)
    run([python, "-m", "pytest", "-q"], root)
    print("All exact, numerical, and regression checks passed.")


if __name__ == "__main__":
    main()
