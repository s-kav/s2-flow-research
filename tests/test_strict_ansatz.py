"""Regression tests for the exact strict-ansatz contradiction."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from strict_ansatz_exact import symbolic_identity_check


def test_improper_case_exact_contradiction():
    result = symbolic_identity_check()
    assert result["forced_c_norm_squared"] == "25/16"
    assert result["contradiction_excess"] == "9/16"
