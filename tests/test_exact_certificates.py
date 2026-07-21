"""Smoke-test two endpoint exact certificates."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from verify_exact_certificates import verify_one


def test_endpoint_certificates():
    for n in (15, 41):
        path = ROOT / "certificates" / f"flower_J{n}_exact_dyadic.npz"
        assert verify_one(path)["certified"]
