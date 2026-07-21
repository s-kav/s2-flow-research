# S²-Flow Research

Reproducible computational framework for finite-instance investigation of the S²-flow conjecture: every bridgeless cubic graph should admit unit vectors on oriented edges satisfying Kirchhoff balance at every vertex.

This repository does not claim a proof. It provides independently checkable numerical candidates, exact structural checks, rank/Gram diagnostics, graph generators, experiment orchestration, and certificate export.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install -U pip
python -m pip install -e ".[dev]"
```

## Quick start

```bash
s2flow analyze --graph petersen --dimension 3 --restarts 12 --output results/json/petersen.json
pytest
python scripts/reproduce_all.py
```

## Mathematical checks

For an oriented incidence matrix `B` and edge-vector matrix `X`, a candidate is accepted only when both conditions hold numerically:

- `B @ X = 0`
- every row of `X` has Euclidean norm `1`

The framework additionally verifies the Gram matrix `Q = X Xᵀ`, its numerical rank, positive semidefiniteness, diagonal constraints, and `B Q = 0`.

## Repository policy

Numerical success is evidence for a finite graph only. Numerical failure is inconclusive. Any claimed certificate must be rechecked with `s2flow verify`.


## Proof research layer

The package now includes `src/s2flow/proof/` with executable candidate-lemma checks, bounded counterexample search, symbolic polynomial formulations, and independently verifiable certificate manifests. These modules support finite experiments and proof development; they do not claim a proof of the open S²-flow conjecture.

## Rigorous partial results and large-scale verification

The package now contains constructive and structural results in
`src/s2flow/proof/theory/`:

- exact S2-flow construction from a proper 3-edge-colouring;
- cut-sum, two-cut antipodality, and three-cut equilateral rigidity checks;
- canonical two-cut and three-cut closures used by the factorisation theorems;
- rank-three PSD cycle-space certificate verification.

Run the deterministic campaign:

```bash
python scripts/massive_verification.py \
  --orders 10 12 14 16 18 20 24 30 40 \
  --samples-per-order 50 \
  --output-dir results/massive

python scripts/verify_campaign.py results/massive
```

For exhaustive nauty input:

```bash
geng -c -d3 -D3 16 | \
  python scripts/nauty_cubic_campaign.py --output-dir results/geng16
```

A successful finite campaign is evidence and provides independently checkable
certificates. It is not a proof of the universal S2-flow conjecture.
