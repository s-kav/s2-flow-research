"""Independent certificate verification."""
from __future__ import annotations
from pathlib import Path
import numpy as np
from s2flow.algebra.incidence import oriented_incidence
from s2flow.flows.verification import verify_candidate
from s2flow.proof.lemmas.lemma04_psd_rank import gram_diagnostics

def verify_npz(graph, path: Path, tolerance: float = 1e-8) -> dict[str, object]:
    """Verify conservation, unit norms, and rank diagnostics from an NPZ file."""
    b, _ = oriented_incidence(graph)
    with np.load(path, allow_pickle=False) as data:
        x=np.asarray(data["X"], dtype=float)
    metrics=verify_candidate(b, x, tolerance)
    metrics["gram"] = gram_diagnostics(x, tolerance)
    return metrics
