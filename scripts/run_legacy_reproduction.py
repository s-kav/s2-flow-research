"""Run the original monolithic laboratory script retained for exact reproducibility."""
from pathlib import Path
import runpy

if __name__ == "__main__":
    runpy.run_path(str(Path(__file__).resolve().parents[1] / "legacy" / "s2_flow_repro.py"), run_name="__main__")
