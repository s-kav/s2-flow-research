"""Certificate serialization."""
from __future__ import annotations
from pathlib import Path
import hashlib, json
import numpy as np

def export_npz(path: Path, vectors: np.ndarray, edge_order, metadata: dict[str, object] | None = None) -> dict[str, str]:
    """Export a deterministic certificate payload and SHA-256 digest."""
    path=Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    edges=np.asarray(edge_order, dtype=int)
    np.savez_compressed(path, X=np.asarray(vectors, dtype=float), edges=edges)
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    manifest={"sha256": digest, "certificate": path.name, "metadata": metadata or {}}
    manifest_path=path.with_suffix(".manifest.json")
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return {"certificate": str(path), "manifest": str(manifest_path), "sha256": digest}
