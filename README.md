# Spherical Unit-Vector Flows on Cubic Graphs

[![DOI](https://zenodo.org/badge/1307368331.svg)](https://doi.org/10.5281/zenodo.21478983)

Proof, exact-certification, and reproducibility research framework for the rigorous and reproducible study of spherical unit-vector flows on bridgeless cubic graphs, with complete results for Isaacs flower snarks and Goldberg snarks.

## Scope

Let `G = (V, E)` be a finite graph with a fixed orientation and oriented incidence matrix `B`. An `S^2`-flow is an assignment of a unit vector in `R^3` to every oriented edge:

\[
X \in \mathbb{R}^{|E|\times 3},
\qquad
BX = 0,
\qquad
\|X_e\|_2 = 1 \quad (e \in E).
\]

The equation `BX = 0` is Kirchhoff conservation at every vertex. Reversing an edge and negating its vector does not change existence, so the property is independent of the chosen orientation.

This repository establishes the following infinite-family theorems:

1. **Flower-snark theorem.** Every Isaacs flower snark `J_n`, for odd `n >= 5`, admits an `S^2`-flow.
2. **Goldberg-snark theorem.** Every Goldberg snark `G_k`, for odd `k >= 5`, admits an `S^2`-flow.

The repository also contains structural reductions, equivalent algebraic formulations, exact finite certificates, large finite campaigns, symbolic tools, and a staged programme for the universal problem.

> **Important:** the universal conjecture that every bridgeless cubic graph admits an `S^2`-flow remains open. This repository proves it for two named infinite families and for several additional constructive classes. It does not claim a universal proof.

## Main mathematical results

### Complete infinite-family results

| Result | Method | Formal status |
|---|---|---|
| Every flower snark `J_n`, odd `n >= 5`, has an `S^2`-flow | Free `Z_n` action, six orbit templates, analytic reduction to one scalar equation, endpoint signs, strict monotonicity | Analytic theorem |
| Every Goldberg snark `G_k`, odd `k >= 5`, has an `S^2`-flow | Free `Z_k` action, twelve orbit templates, representation index `(k - 1) / 2`, scalar reduction, rational interval bounds | Exact computer-assisted theorem |

### Structural and constructive results

The theoretical layer includes:

- rigid `120 degree` geometry at every cubic vertex;
- the cut law for vector flows;
- incidence-matrix, cycle-space, Gram, and rank-three PSD formulations;
- a constructive `S^2`-flow for every cubic graph admitting a nowhere-zero `4`-flow, including every `3`-edge-colourable cubic graph;
- exact factorisation across non-trivial `2`-edge cuts;
- exact factorisation across non-trivial `3`-edge cuts;
- injection and triangle blow-up equivalences;
- restrictions on a hypothetical minimal counterexample;
- matching and spherical-chord formulations;
- an obstruction to representing the general problem by a fixed `F_2^3` vector palette;
- spectrahedral and rank-compression formulations used by the proof-search framework.

### Dimension audit

The project distinguishes two different notions of dimension:

- **ambient embedding dimension**, which affects geometric drawings but not graph invariants;
- **flow-value dimension**, which changes the vector-flow feasibility problem.

Every finite simple snark has straight-line crossing-free embedding dimension exactly `3`, but this standard geometric fact does not resolve edge-uncolourability. The non-trivial research problem is the existence of unit-vector flows in `R^3`.

## Research stages

### Stage 1: formulations, partial theorems, and finite evidence

Stage 1 developed the general framework and tested it independently on finite graphs.

Key outputs:

- cycle-space and direct nonlinear solvers;
- exact and numerical certificate formats;
- an exact Petersen-graph certificate over `Q(sqrt(5))`;
- a campaign of `288` bridgeless cubic graphs;
- `280` constructive certificates derived from `3`-edge-colourings;
- `8` independently verified nonlinear rank-three certificates;
- exact Newton-Kantorovich certification machinery;
- symbolic elimination, Groebner, SOS, polynomial-system, reduction, and counterexample-search modules.

The stored campaign reports:

```text
Instances:                         288
Valid certificates:               288
Exact constructive certificates:  280
Nonlinear certificates:             8
Failures:                            0
Maximum conservation residual:    2.17e-15
Maximum unit-norm residual:       7.80e-08
```

These finite computations validate implementations and produce certified examples. They do not prove the universal conjecture.

### Equivariance audit

Previously generated unconstrained certificates for `J_5` through `J_13` were tested against all relevant cyclic generators using orientation-aware Procrustes alignment and group averaging.

The audit showed that:

- generic Newton certificates were strongly non-equivariant;
- orbit averaging substantially reduced vector norms;
- the natural strict order-`2n` ansatz is structurally impossible;
- the correct symmetry is the index-two subgroup `Z_n`;
- the reduced flower system has six orbit templates.

This negative result was essential: it replaced an incorrect symmetry model with the representation used in the final theorem.

### Stage 2: complete flower-snark theorem

For odd `n >= 5`, the correct `Z_n`-equivariant ansatz reduces the full graph problem to an `18 x 18` template system and then to a scalar equation. The analytic route proves existence for the entire parameter interval, not only for finitely many values of `n`.

Independent validation includes:

- `19` exact dyadic certificates for `J_5, J_7, ..., J_41`;
- an integer-only independent certificate verifier;
- an exact rational Newton-Kantorovich covering with `1,510` intervals;
- coverage of odd parameters from `5` through `15,707,963` by the independent Route 1 computation;
- symbolic, rational, dense numerical, and high-precision checks of the analytic Route 2 identities.

The finite certificates and Route 1 covering are independent checks. The infinite flower theorem is based on the analytic Route 2 argument.

### Goldberg replication

The Goldberg investigation repeated the full research pipeline on a structurally different cyclic snark family.

The exact graph construction uses an eight-vertex block with nine internal edges and three cyclic inter-block connections. The shift action has twelve free edge orbits.

The initial representation with angle `2*pi/k` fails for `k >= 7` because one inter-block unit chord cannot be realised. The correct representation uses

\[
\ell = \frac{k-1}{2},
\qquad
\varphi = \frac{2\pi\ell}{k} = \pi - \frac{\pi}{k}.
\]

With this representation, the `36 x 36` orbit-template system reduces to one scalar equation. Exact rational interval arithmetic establishes endpoint signs and strict positivity of the scalar derivative on the full parameter rectangle, giving a unique root and an `S^2`-flow for every odd `k >= 5`.

Independent validation includes:

```text
Odd Goldberg parameters checked:        499, through k = 1001
Complete graphs expanded and verified:  149, through k = 301
Largest stored full verification:        G_1001
Vertices of G_1001:                      8,008
Edges of G_1001:                         12,012
```

## Proof-status policy

The repository separates five epistemic levels.

| Level | Meaning | Examples |
|---|---|---|
| Analytic proof | Human-checkable proof valid for an unbounded class | Flower-snark theorem, cut factorisation |
| Exact computer-assisted proof | Finite rational or integer verification of uniform inequalities | Goldberg interval theorem |
| Exact finite certificate | Exact verification for specified finite instances | Dyadic flower certificates `J_5` through `J_41` |
| Numerical validation | Floating-point consistency or finite-range testing | Equivariance residuals, large sweeps |
| Research programme | Proposed route without a completed universal proof | Spectrahedral, variational, topological, holonomy, real-algebraic routes |

See [FORMAL_STATUS.md](FORMAL_STATUS.md) for the concise formal statement and [VALIDATION.md](VALIDATION.md) for the reviewed execution record.

## Repository layout

```text
.github/workflows/ci.yml       Continuous integration
archive/                       Superseded metadata retained for provenance
benchmarks/                    Solver and scaling benchmarks
certificates/                  Exact dyadic and interval certificates
configs/                       Runtime and experiment configurations
docs/                          Theorem reports, theory notes, and development history
legacy/                        Original monolithic reproduction script
manuscript/                    Journal manuscript and supplementary material
notebooks/                     Interactive finite-instance exploration
results/                       Stored exact, numerical, and campaign outputs
scripts/                       Reproduction, verification, certification, and report drivers
source_notes/                  Supplied derivations and provenance notes
src/goldberg_s2/               Current Goldberg theorem implementation
src/s2flow/                    General graph-flow and proof-search framework
tests/                         Unit and regression tests
```

### Core implementation map

```text
src/goldberg_s2/
├── algebra.py                 Scalar reduction and template formulas
├── construction.py            Equivariant flow construction
├── graph.py                   Exact Goldberg graph builder
├── interval.py                Rational interval arithmetic
├── interval_proof.py          Uniform sign and derivative proof
└── verify.py                  Reduced and full-graph verification

src/s2flow/proof/
├── lemmas/                    Cycle, matching, gluing, PSD, rotation, extension lemmas
├── search/                    Counterexample, reduction, induction, certificate search
├── symbolic/                  SymPy, elimination, Groebner, SOS, polynomial systems
├── certificates/              Certificate export and independent verification
└── theory/                    Cut factorisation, cycle-cover, Gram-compression results
```

The current source tree preserves both the mature Goldberg package and the broader historical `s2flow` framework. A future major release may consolidate family-specific code under `src/s2flow/families/`, but the present layout is retained for compatibility with stored certificates and historical scripts.

## Requirements

- Python `>= 3.10`
- NumPy
- SciPy
- NetworkX
- PyYAML

Optional groups provide testing, plotting, symbolic algebra, SDP, and DOCX generation.

## Installation

### Recommended editable installation

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev,plot,symbolic,report]"
```

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev,plot,symbolic,report]"
```

### Locked environment with `uv`

```bash
uv sync --all-extras
```

### Minimal runtime installation

```bash
python -m pip install -r requirements.txt
python -m pip install -e .
```

## Fast verification

Run from the repository root:

```bash
python -m compileall -q src scripts tests benchmarks
python -m pytest -q
python scripts/verify_interval_certificate.py
python scripts/verify_route2_algebra.py
python scripts/verify_exact_certificates.py
```

The reviewed release completed `28` automated tests successfully.

## Main execution modes

### Complete project reproduction

```bash
python scripts/reproduce_project.py
```

This orchestrates:

1. the complete Goldberg theorem pipeline;
2. flower Stage 2 algebra verification;
3. exact exclusion of the strict order-`2n` ansatz;
4. all-generator equivariance analysis;
5. exact flower-certificate verification;
6. the regression test suite.

It writes:

```text
results/project_reproduction_summary.json
```

### Goldberg theorem reproduction

```bash
python scripts/reproduce_all.py
```

This generates and verifies the rational interval certificate, runs the parameter sweep, verifies `G_1001`, rebuilds figures and the Goldberg report, and runs the tests.

Principal outputs:

```text
certificates/interval_proof_certificate.json
certificates/numerical_sweep.csv
certificates/verification_G1001.json
results/figures/
docs/Goldberg_Snarks_S2_Flow_Theorem_en.docx
```

### Flower exact and equivariance verification

```bash
python scripts/verify_all.py
```

This checks:

- the exact obstruction to the strict order-`2n` ansatz;
- all cyclic generators used in the equivariance audit;
- all stored dyadic flower certificates;
- the regression test suite.

### Flower analytic Stage 2 verification

```bash
python scripts/verify_route2_algebra.py
```

This verifies the symbolic and numerical identities used by the analytic flower theorem, including the reduced equations, scalar reduction, endpoint signs, and reconstruction checks.

### Independent Route 1 certificate verification

```bash
python scripts/recheck_route1_certificates.py \
  --input results/json/route1_results_full.json
```

This recomputes the rational Newton-Kantorovich inequalities from the stored exact centres and inverse-Jacobian approximations. Informational floating-point fields are not trusted.

### Finite-instance CLI

After installation:

```bash
s2flow analyze \
  --graph petersen \
  --dimension 3 \
  --restarts 24 \
  --seed 20260717 \
  --output results/json/petersen_cli.json
```

Supported graph specifications include:

```text
petersen
flower:5
flower:7
random:20:12345
```

To verify a stored finite certificate:

```bash
s2flow verify \
  --graph petersen \
  --certificate results/json/petersen_cli.npz \
  --tolerance 1e-8
```

### Massive finite campaign

```bash
python scripts/massive_verification.py \
  --orders 10 12 14 16 18 20 24 30 40 \
  --samples-per-order 30 \
  --edge-coloring-max-nodes 2000000 \
  --nonlinear-restarts 16 \
  --output-dir results/massive_run
```

Independent verification:

```bash
python scripts/verify_campaign.py results/massive_run --tolerance 1e-7
```

### Exhaustive cubic graphs from `nauty`

```bash
geng -c -d3 -D3 16 | \
  python scripts/nauty_cubic_campaign.py --output-dir results/geng16
```

`geng` is supplied by `nauty/Traces` and is not bundled with this repository.

## Generated outputs

| Path | Content |
|---|---|
| `certificates/flower_J*_exact_dyadic.npz` | Exact finite flower certificates |
| `certificates/interval_proof_certificate.json` | Rational Goldberg interval proof certificate |
| `results/equivariance_all_generators.*` | All-generator equivariance audit |
| `results/exact_certificates.json` | Exact flower-certificate summary |
| `results/independent_exact_verification.json` | Independent exact verification |
| `results/json/route1_results_full.json` | Full rational Route 1 certificate atlas |
| `results/massive_run/` | Finite campaign, certificates, CSV, independent verification |
| `results/strict_ansatz_exact.json` | Exact strict-ansatz obstruction |
| `results/zn_branch.json` | Finite cyclic branch continuation data |
| `MANIFEST.sha256` | Release-file integrity manifest |

For every supported command, its purpose, output paths, and proof status, see [RUNBOOK.md](RUNBOOK.md).

## Manuscripts and documentation

### Submission manuscript

```text
manuscript/S2_Flows_Flower_Goldberg_Snarks.docx
manuscript/S2_Flows_Flower_Goldberg_Snarks_Supplementary.docx
manuscript/latex/main.tex
manuscript/latex/supplementary.tex
manuscript/latex/main.pdf
manuscript/latex/supplementary.pdf
```

The submission manuscript focuses on the two infinite-family theorems and separates analytic and computer-assisted components.

### Comprehensive research article

A separate comprehensive article package consolidates the full programme:

- dimension audit;
- local cubic geometry;
- structural reductions;
- Stage 1;
- exact Petersen and flower certificates;
- equivariance audit;
- Stage 2 flower theorem;
- Goldberg replication;
- negative results;
- alternative universal-proof routes.

The comprehensive article is intended as the full research record, while the manuscript directory contains the shorter journal-submission package.

### Additional documentation

| File | Purpose |
|---|---|
| `FORMAL_STATUS.md` | Exact statement of what is proved and what remains open |
| `RUNBOOK.md` | Complete execution catalogue |
| `VALIDATION.md` | Reviewed validation record |
| `REPOSITORY_AUDIT.md` | Repository findings and release recommendations |
| `REPRODUCIBILITY.md` | Finite-campaign reproduction guide |
| `PACKAGE_CONTENTS.md` | Deliverable inventory |
| `docs/theory.md` | General theory notes |
| `docs/theorem.md` | Theorem-oriented development notes |
| `docs/conjectures.md` | Open problems and conjectural routes |
| `docs/algorithms.md` | Algorithmic methods |
| `docs/experiments.md` | Experimental design and results |

Historical DOCX reports are preserved in `docs/` for provenance. The current formal status is defined by the latest theorem documents, `FORMAL_STATUS.md`, and the reviewed manuscripts.

## Continuous integration

GitHub Actions runs:

```text
editable installation with all research extras
Python compilation
Pytest suite
Goldberg interval-certificate verification
flower Stage 2 algebra verification
exact flower-certificate verification
```

Workflow file:

```text
.github/workflows/ci.yml
```

## Known limitations

- The universal `S^2`-flow conjecture remains open.
- Finite campaigns and floating-point solver convergence are not universal proofs.
- The Goldberg theorem relies on an exact computer-assisted interval component and should be distributed with its certificate and verifier.
- The repository includes historical material and two overlapping source namespaces for provenance and backward compatibility.
- The compact CLI has limited graph-specification support and is intended for finite experiments, not for reproducing the family theorems.
- `nauty/Traces`, a full TeX distribution, and Microsoft Word or LibreOffice are external tools and are not bundled.
- Before archival publication, the confirmed public repository URL and DOI should be added to the citation metadata and manuscript data-availability statement.

## Integrity verification

Verify all release files against the manifest:

```bash
sha256sum -c MANIFEST.sha256
```

Verify a downloaded ZIP independently:

```bash
unzip -t S2-flow-research-reviewed-submission-package.zip
```

## Citation

Citation metadata is provided in [CITATION.cff](CITATION.cff). Cite both the associated mathematical article and the exact software release used for verification.

Before creating the archival release:

1. confirm the public GitHub repository URL;
2. create a signed or annotated version tag;
3. archive the tag through Zenodo or an equivalent service;
4. add the resulting DOI to `CITATION.cff` and the manuscript.

## References

For citing you should use:

Sergii Kavun. (2026). s-kav/s2-flow-research: Version 0.2.0 (v.0.2.0). Zenodo. https://doi.org/10.5281/zenodo.21478983

[![DOI](https://zenodo.org/badge/1307368331.svg)](https://doi.org/10.5281/zenodo.21478983)

## Licence

MIT License. See [LICENSE](LICENSE).

The source archive originally contained an unresolved MIT/AGPL merge conflict. The reviewed release resolves the active licence to MIT, consistent with `CITATION.cff`, and preserves the original conflicted file under `archive/` for auditability.

## Project status

**Version:** `0.2.0`  
**Reviewed release date:** `2026-07-21`  
**Maintainer:** Sergii Kavun

Current completed scope:

```text
[complete] general formulations and structural reductions
[complete] Stage 1 finite and exact certification framework
[complete] equivariance audit and strict-ansatz obstruction
[complete] flower-snark theorem for all odd n >= 5
[complete] Goldberg-snark theorem for all odd k >= 5
[complete] exact and independent certificate verification
[complete] journal manuscript and supplementary material
[open]     universal S^2-flow conjecture for all bridgeless cubic graphs
```
