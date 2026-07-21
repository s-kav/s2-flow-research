# Complete Reproducibility Runbook

This document lists every supported execution mode in the repository, what it computes, where it writes data, and what kind of mathematical evidence it provides.

## 1. Environment preparation

Run from the repository root.

### 1.1 Recommended editable installation

```bash
python -m venv .venv
source .venv/bin/activate                 # Linux/macOS
# .venv\Scripts\activate                 # Windows PowerShell
python -m pip install --upgrade pip
python -m pip install -e ".[dev,plot,symbolic,report]"
```

**Does:** installs the package, testing tools, plotting stack, symbolic tools, and DOCX dependencies.

**Writes:** `.venv/` and editable-install metadata in the environment, not research results.

**Confirms:** only that dependencies can be resolved and imports can be installed. It proves no theorem.

### 1.2 Minimal installation

```bash
python -m pip install -r requirements.txt
python -m pip install -e .
```

**Does:** installs only runtime dependencies and the package.

**Confirms:** runtime availability, not mathematical correctness.

### 1.3 Locked installation with uv

```bash
uv sync --all-extras
```

**Does:** creates an environment from `uv.lock` and enables all optional groups.

**Confirms:** dependency-lock reproducibility on a compatible platform.

## 2. Fast integrity checks

### 2.1 Compile all Python files

```bash
python -m compileall -q src scripts tests benchmarks
```

**Does:** compiles every Python source file.

**Writes:** temporary `__pycache__` directories.

**Confirms:** syntax and import-time parsing only.

### 2.2 Run the regression test suite

```bash
python -m pytest -q
```

**Does:** executes unit and regression tests for graph construction, incidence matrices, exact certificates, interval arithmetic, theorem formulas, serialisation, and proof modules.

**Writes:** `.pytest_cache/` unless disabled.

**Confirms:** implementation consistency for tested cases. Tests support but do not replace the analytic proofs.

### 2.3 Run the consolidated verification pipeline

```bash
python scripts/verify_all.py
```

**Does:** runs the strict flower-ansatz obstruction, all-generator equivariance diagnostics, exact flower-certificate verification, and the test suite.

**Writes:**

- `results/strict_ansatz_exact.json`
- `results/equivariance_all_generators.json`
- `results/equivariance_all_generators.csv`
- `results/independent_exact_verification.json`
- `.pytest_cache/`

**Confirms:** exact finite certificates and finite diagnostic claims included in the flower analysis. Equivariance residuals are numerical diagnostics, not existence or non-existence proofs.

## 3. Complete project reproduction

### 3.1 Reproduce the current Goldberg theorem package

```bash
python scripts/reproduce_all.py
```

**Does:** regenerates figures, exact interval certificate, numerical sweep, large-graph verification, Word report, and regression tests.

**Writes or refreshes:**

- `docs/figures/goldberg_block.png`
- `docs/figures/scalar_branch.png`
- `docs/figures/endpoint_signs.png`
- `certificates/interval_proof_certificate.json`
- `certificates/numerical_sweep.csv`
- `certificates/verification_G1001.json`
- `docs/Goldberg_Snarks_S2_Flow_Theorem_en.docx`

**Confirms:** the exact interval inequalities used in the Goldberg proof, the explicit construction on a large finite sweep, and the absence of implementation regressions. The theorem for all odd `k >= 5` is proved by the analytic reduction plus exact interval certificate, not by the finite sweep alone.

### 3.2 Reproduce both family theorems

```bash
python scripts/reproduce_project.py
```

**Does:** runs the Goldberg reproduction, flower analytic verification, exact flower-certificate verification, consolidated checks, and manuscript source checks.

**Writes:** the union of outputs listed in Sections 3.1, 4, 5, and 8, plus `results/project_reproduction_summary.json`.

**Confirms:** that one clean command reproduces all theorem-supporting artefacts included in this release.

## 4. Goldberg family runs

### 4.1 Generate the exact interval certificate

```bash
python scripts/run_interval_proof.py \
  --output certificates/interval_proof_certificate.json \
  --bits 112 \
  --endpoint-pieces 16 \
  --derivative-s-pieces 32 \
  --derivative-x-pieces 32
```

**Does:** evaluates endpoint signs and the derivative lower bound using outward-rounded rational intervals.

**Writes:** `certificates/interval_proof_certificate.json`.

**Proves:** for the certified rectangle, the scalar function changes sign between the stated rational endpoints and is strictly increasing in the scalar variable. Together with the explicit reconstruction formulas, this proves existence and uniqueness of the equivariant Goldberg `S^2`-flow branch for all odd `k >= 5`.

### 4.2 Independently verify the stored interval certificate

```bash
python scripts/verify_interval_certificate.py \
  certificates/interval_proof_certificate.json
```

**Does:** rechecks all exact rational boxes and their canonical hash without relying on floating-point fields.

**Writes:** console output only.

**Confirms:** certificate integrity and all interval inequalities. This is an independent checker for the computer-assisted part of the proof.

### 4.3 Verify a single Goldberg graph

```bash
python scripts/verify_one.py 41
```

**Does:** constructs `G_41`, solves the scalar equation by bracketed bisection, expands all templates, and checks graph properties, Kirchhoff conservation, and unit norms.

**Writes:** JSON to standard output.

**Confirms:** one finite instance numerically. It does not by itself prove the infinite-family theorem.

### 4.4 Run the Goldberg numerical sweep

```bash
python scripts/run_numerical_sweep.py \
  --max-k 1001 \
  --full-max-k 301 \
  --output certificates/numerical_sweep.csv
```

**Does:** evaluates every odd `k` through 1001 and performs full graph expansion through 301.

**Writes:** `certificates/numerical_sweep.csv`.

**Confirms:** broad implementation agreement with the analytic formulas and records worst finite-precision residuals. It is validation, not an infinite proof.

### 4.5 Regenerate Goldberg figures

```bash
python scripts/make_figures.py
```

**Writes:** the three PNG files under `docs/figures/`.

**Confirms:** presentation artefacts only.

### 4.6 Regenerate the Goldberg Word report

```bash
python scripts/build_report.py
```

**Writes:** `docs/Goldberg_Snarks_S2_Flow_Theorem_en.docx`.

**Confirms:** documentation generation only. The DOCX must still be rendered and visually reviewed before release.

## 5. Flower family analytic runs

### 5.1 Verify the analytic Route 2 proof

```bash
python scripts/verify_route2_algebra.py
```

**Does:** checks the reduced `18 x 18` system, symbolic identities, exact rational inequality chains, dense parameter samples, high-precision residuals, and full-graph expansions.

**Writes:** console output only.

**Proves/Confirms:** the exact symbolic and rational subclaims used in the proof that every flower snark `J_n`, odd `n >= 5`, admits an `S^2`-flow. Dense and high-precision checks are supplementary validation; the theorem rests on the analytic sign and monotonicity arguments.

### 5.2 Execute the reduced-system demonstrations

```bash
python scripts/stage2_reduced.py
```

**Does:** solves the reduced system, compares it with the scalar cascade, expands selected `J_n`, evaluates conditioning, and illustrates asymptotic behaviour.

**Writes:** console output only.

**Confirms:** numerical agreement between the square system and analytic cascade. It is not the formal proof checker.

### 5.3 Generate the `Z_n`-equivariant numerical branch

```bash
python scripts/zn_ansatz.py \
  --min-n 5 \
  --max-n 41 \
  --branch-k 1 \
  --random-starts 40 \
  --output-dir data/equivariant_flows \
  --summary results/zn_branch.json
```

**Writes:** one NPZ file per odd `n` and `results/zn_branch.json`.

**Confirms:** numerical existence and continuation of the selected equivariant branch on the requested finite range. These files are inputs to exact certificate generation, not proofs by themselves.

### 5.4 Generate exact dyadic flower certificates

```bash
python scripts/exact_rational_certificates.py \
  --flow-dir data/equivariant_flows \
  --output-dir certificates \
  --summary results/exact_certificates.json \
  --min-n 5 \
  --max-n 41
```

**Writes:** `certificates/flower_J*_exact_dyadic.npz` and a JSON summary.

**Confirms:** exact Newton-Kantorovich certificates for the finite range represented by the input flows.

### 5.5 Independently verify exact flower certificates

```bash
python scripts/verify_exact_certificates.py \
  --certificate-dir certificates \
  --output results/independent_exact_verification.json
```

**Does:** recomputes decisive inequalities using integer/rational data.

**Writes:** `results/independent_exact_verification.json`.

**Proves:** exact existence for each certified finite `J_n`. The analytic Route 2 theorem is what extends existence to all odd `n >= 5`.

### 5.6 Regenerate the Route 1 family certificates

```bash
python scripts/route1_kantorovich_family.py \
  --output results/json/route1_results_full.json
```

**Does:** builds a gap-free chain of exact rational Kantorovich boxes over the configured parameter interval.

**Writes:** `results/json/route1_results_full.json`.

**Proves:** exact existence over the covered parameter interval, subject to independent rechecking. This run can be computationally expensive.

### 5.7 Recheck Route 1 certificates independently

```bash
python scripts/recheck_route1_certificates.py \
  --input results/json/route1_results_full.json
```

**Writes:** console output only.

**Proves/Confirms:** exact inequality validity, hash integrity, and gap-free interval coverage of the stored Route 1 certificate chain.

## 6. Flower symmetry and obstruction diagnostics

### 6.1 Prove the strict order-`2n` ansatz obstruction

```bash
python scripts/strict_ansatz_exact.py \
  --output results/strict_ansatz_exact.json
```

**Does:** evaluates the exact structural contradiction for the rejected strict equivariance model.

**Writes:** `results/strict_ansatz_exact.json`.

**Proves:** non-existence within that precisely defined strict ansatz. It does not rule out other `S^2`-flows.

### 6.2 Check every cyclic generator on stored certificates

```bash
python scripts/equivariance_all_generators.py \
  --cert-dir results/massive_run/certificates \
  --n 5 7 9 11 13 \
  --output-json results/equivariance_all_generators.json \
  --output-csv results/equivariance_all_generators.csv
```

**Does:** aligns certificate vectors by orthogonal Procrustes for every generator, averages over cyclic orbits, and records residual and norm collapse.

**Confirms:** that the particular stored numerical certificates are far from the tested equivariant representations. This is a numerical diagnostic and cannot prove non-existence of an equivariant solution.

### 6.3 Original one-generator diagnostic

```bash
python scripts/equivariance_check.py
```

**Writes:** its configured JSON result file.

**Confirms:** historical diagnostic only. Prefer the all-generator script for publication.

### 6.4 Historical ansatz solvers

```bash
python scripts/equivariant_ansatz_solve.py
python scripts/ansatz_extend.py
```

**Writes:** JSON summaries configured in the scripts.

**Confirms:** historical numerical exploration. These runs are retained for provenance and should not be cited as formal proof.

## 7. General finite-graph campaign runs

### 7.1 Massive random and named-family campaign

```bash
python scripts/massive_verification.py \
  --orders 10 12 14 16 18 20 24 30 40 \
  --samples-per-order 30 \
  --nonlinear-restarts 16 \
  --output-dir results/massive_run
```

**Does:** generates named families and random connected cubic graphs, seeks constructive or nonlinear unit-sphere flows, and saves certificates.

**Writes:** `summary.csv`, `campaign.json`, and NPZ certificates under `results/massive_run/`.

**Confirms:** finite computational evidence for sampled graphs. It does not prove the universal conjecture.

### 7.2 Independent campaign verification

```bash
python scripts/verify_campaign.py results/massive_run
```

**Writes:** `results/massive_run/independent_verification.json`.

**Confirms:** graph properties and numerical certificate residuals independently from the campaign driver.

### 7.3 Fully independent NPZ certificate check

```bash
python scripts/independent_check.py \
  --certificate-dir results/massive_run/certificates \
  --output results/massive_run/independent_check_summary.json
```

**Confirms:** cubicity, connectivity, bridgelessness, edge identity, Kirchhoff residuals, norm residuals, and Gram rank for all stored campaign certificates.

### 7.4 Exact Kantorovich proofs for selected campaign certificates

```bash
python scripts/kantorovich_certify.py
```

**Does:** converts selected floating-point campaign solutions to cycle-space coordinates and checks simplified-Newton contraction inequalities using exact rational arithmetic.

**Writes:** `results/massive_run/kantorovich_results.json`.

**Proves:** exact existence of an `S^2`-flow near every candidate whose record is marked `certified: true`. The result applies only to the explicitly listed finite graphs in the script.

### 7.5 Nauty/geng exhaustive stream

```bash
geng -c -d3 -D3 16 | \
python scripts/nauty_cubic_campaign.py \
  --output-dir results/geng16 \
  --limit 0 \
  --nonlinear-restarts 12
```

**Does:** consumes connected cubic graphs from `nauty` and searches for certificates.

**Writes:** `results/geng16/records.json` and associated campaign data.

**Confirms:** exhaustive or prefix-limited evidence for the exact streamed order. It proves no statement about unbounded graph order.

### 7.6 Petersen exact example

```bash
python scripts/petersen_exact.py
```

**Confirms:** a standalone exact or high-precision construction for the Petersen graph, depending on the selected path in the script.

### 7.7 General graph generation

```bash
python scripts/generate_graphs.py
```

**Does:** generates the repository's configured graph data.

**Writes:** graph files under `data/graphs/` when enabled by the script configuration.

## 8. Reports and manuscript generation

### 8.1 Build the historical partial-results report

```bash
python scripts/build_partial_results_report.py
```

**Writes:** a DOCX report and figures under `docs/` and its asset directory.

**Confirms:** presentation only.

### 8.2 Build the submission article and supplementary DOCX

```bash
python scripts/build_submission_documents.py
```

**Writes:**

- `manuscript/S2_Flows_Flower_Goldberg_Snarks.docx`
- `manuscript/S2_Flows_Flower_Goldberg_Snarks_Supplementary.docx`

**Confirms:** document generation only. Use the rendering QA commands in Section 8.4.

### 8.3 Compile LaTeX manuscripts

```bash
cd manuscript/latex
latexmk -pdf -interaction=nonstopmode main.tex
latexmk -pdf -interaction=nonstopmode supplementary.tex
cd ../..
```

**Writes:** `main.pdf`, `supplementary.pdf`, and LaTeX auxiliary files.

**Confirms:** source completeness and typesetting. It does not validate the mathematical argument.

### 8.4 Render Word documents for visual QA

```bash
python /home/oai/skills/docx/render_docx.py \
  manuscript/S2_Flows_Flower_Goldberg_Snarks.docx \
  --output_dir manuscript/render_main --emit_pdf

python /home/oai/skills/docx/render_docx.py \
  manuscript/S2_Flows_Flower_Goldberg_Snarks_Supplementary.docx \
  --output_dir manuscript/render_supplementary --emit_pdf
```

**Does:** renders every DOCX page to PNG and optionally PDF.

**Confirms:** layout quality only after a human inspects every rendered page.

## 9. Benchmark runs

```bash
python benchmarks/benchmark_solver.py
```

**Does:** times selected solvers and records performance characteristics.

**Confirms:** performance on the current machine, not mathematical correctness.

## 10. Legacy reproduction

```bash
python scripts/run_legacy_reproduction.py
```

**Does:** executes `legacy/s2_flow_repro.py` through the compatibility wrapper.

**Confirms:** historical reproducibility only. Prefer current modular scripts for new claims.

## 11. GitHub parity and release verification

The supplied archive contains no `.git` directory or remote URL. From an actual GitHub clone, run:

```bash
git remote -v
git status --short
git rev-parse HEAD
git ls-files -z | sort -z | xargs -0 sha256sum > github-tracked-files.sha256
python -m pytest -q
python scripts/reproduce_project.py
```

To compare a GitHub checkout with this release tree while excluding generated data:

```bash
rsync -avnc --delete \
  --exclude='.git/' \
  --exclude='.venv/' \
  --exclude='__pycache__/' \
  --exclude='.pytest_cache/' \
  /path/to/github-clone/ /path/to/release-tree/
```

A clean comparison plus an identical commit hash and release tag establishes repository parity.

## 12. Epistemic status legend

- **Analytic proof:** symbolic derivation valid for every admissible family parameter.
- **Exact computer-assisted proof:** finite rational or integer certificate independently checkable without floating-point trust.
- **Exact finite certificate:** proves one finite graph or a certified finite parameter interval.
- **Numerical validation:** detects implementation errors and supports a conjectured pattern but is not a proof.
- **Presentation run:** produces figures or documents and has no independent mathematical force.
