"""Manifest integrity checks."""
from __future__ import annotations
from pathlib import Path
import hashlib, json

def check_manifest(manifest_path: Path) -> dict[str, object]:
    """Verify the SHA-256 digest recorded in a certificate manifest."""
    manifest_path=Path(manifest_path)
    manifest=json.loads(manifest_path.read_text(encoding="utf-8"))
    certificate=manifest_path.parent / manifest["certificate"]
    actual=hashlib.sha256(certificate.read_bytes()).hexdigest()
    return {"valid": actual == manifest["sha256"], "expected": manifest["sha256"], "actual": actual, "certificate": str(certificate)}
