# S²-Flows on Goldberg Snarks

This repository contains a reproducible proof of the following family theorem:

> **Theorem.** Every Goldberg snark `G_k`, for odd `k >= 5`, admits an `S²`-flow.

The proof is constructive and uses a non-fundamental cyclic representation. The block shift is represented by the rotation

```text
phi_k = pi - pi/k = 2*pi*((k-1)/2)/k,
```

so the representation closes after `k` blocks. The original fundamental-angle attempt `phi = 2*pi/k` cannot work for `k >= 7`: the `v5^t-v5^(t+1)` channel would require a unit chord whose maximum possible length is `2*sin(pi/k) < 1`.

The corrected equivariant system has twelve free edge orbits. A reflection-symmetric template reduction converts the `36 x 36` system to one scalar equation `H(s, x) = 0`, where

```text
x = tan(pi/(2k)),  0 < x <= tan(pi/10) < 13/40.
```

Exact rational interval arithmetic proves, uniformly on `x in [0, 13/40]`, that

```text
H(2/3, x) < 0,
H(21/25, x) > 0,
partial H / partial s > 0 on [2/3, 21/25].
```

Therefore a unique root exists for every admissible `x`; the root defines all twelve unit templates and hence the full flow on `G_k`.

## Repository contents

- `src/goldberg_s2/graph.py`: exact Goldberg graph and cyclic orbit construction.
- `src/goldberg_s2/algebra.py`: scalar reduction.
- `src/goldberg_s2/construction.py`: explicit twelve-template flow.
- `src/goldberg_s2/verify.py`: independent reduced and full-graph verification.
- `src/goldberg_s2/interval.py`: exact rational interval arithmetic.
- `src/goldberg_s2/interval_proof.py`: endpoint and monotonicity certificate.
- `certificates/interval_proof_certificate.json`: complete exact interval certificate.
- `certificates/numerical_sweep.csv`: finite regression sweep for odd `k <= 1001`.
- `docs/Goldberg_Snarks_S2_Flow_Theorem_en.docx`: English theorem report.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m pip install -e .
```

On Windows PowerShell, activate with:

```powershell
.venv\Scripts\Activate.ps1
```

## Reproduce the exact proof

```bash
python scripts/run_interval_proof.py
python scripts/verify_interval_certificate.py
```

The verifier recomputes every interval enclosure using integers and exact rational arithmetic. Floating-point arithmetic is not used for the decisive sign and derivative checks.

## Run the finite numerical sweep

```bash
python scripts/run_numerical_sweep.py --max-k 1001 --full-max-k 301
python scripts/verify_one.py 1001
```

## Run everything

```bash
python scripts/reproduce_all.py
```

## Scope

This theorem proves the `S²`-flow conjecture for the complete infinite family of Goldberg snarks. It does not prove the universal conjecture for all bridgeless cubic graphs.
