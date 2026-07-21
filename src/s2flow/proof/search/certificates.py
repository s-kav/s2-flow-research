"""Search-level certificate helpers."""
from __future__ import annotations
from pathlib import Path
import json
import numpy as np

def save_candidate_certificate(path: Path, vectors: np.ndarray, metadata: dict[str, object]) -> None:
    """Save vectors losslessly and metadata in adjacent JSON."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(path, X=np.asarray(vectors, dtype=float))
    path.with_suffix(".json").write_text(json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8")
