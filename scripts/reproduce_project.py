"""Run the complete theorem and manuscript reproducibility pipeline."""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path


def run(command: list[str], root: Path) -> dict[str, object]:
    started = time.time()
    print('+', ' '.join(command), flush=True)
    completed = subprocess.run(command, cwd=root, check=True)
    return {
        'command': command,
        'returncode': completed.returncode,
        'seconds': round(time.time() - started, 3),
    }


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    python = sys.executable
    records = []
    commands = [
        [python, 'scripts/reproduce_all.py'],
        [python, 'scripts/verify_route2_algebra.py'],
        [python, 'scripts/strict_ansatz_exact.py'],
        [python, 'scripts/equivariance_all_generators.py'],
        [python, 'scripts/verify_exact_certificates.py'],
        [python, '-m', 'pytest', '-q'],
    ]
    for command in commands:
        records.append(run(command, root))
    output = root / 'results' / 'project_reproduction_summary.json'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({'status': 'passed', 'runs': records}, indent=2), encoding='utf-8')
    print(f'Project reproduction summary: {output}')


if __name__ == '__main__':
    main()
