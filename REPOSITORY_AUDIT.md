# Repository Structure and Reproducibility Audit

Audit date: 21 July 2026

## Executive assessment

The repository contains the complete mathematical and computational material needed to reproduce the two principal family results:

1. exact equivariant unit-sphere flows for every Isaacs flower snark `J_n`, with odd `n >= 5`;
2. exact equivariant unit-sphere flows for every Goldberg snark `G_k`, with odd `k >= 5`.

The core implementations are internally coherent and the automated test suite passes after an editable installation. The submitted archive, however, mixed a current Goldberg package, a broader historical `s2flow` framework, generated build artefacts, several historical reports, and scripts with machine-specific paths. This release repairs execution blockers while retaining the historical material for provenance.

## Changes applied in this reviewed release

- Resolved the merge conflict in `LICENSE` in favour of MIT, consistent with the original `CITATION.cff`.
- Preserved the conflicting original file as `archive/LICENSE_with_unresolved_merge_conflict.txt`.
- Added `requirements.txt` and `requirements-dev.txt` for users who do not use dependency extras.
- Removed committed `__pycache__`, `.pyc`, `.pytest_cache`, and `.egg-info` artefacts.
- Corrected the default flower-certificate directory used by the all-generator equivariance check.
- Replaced machine-specific output and certificate paths in reproducibility scripts.
- Added a GitHub Actions workflow under `.github/workflows/ci.yml`.
- Added this audit and a complete execution guide in `RUNBOOK.md`.
- Archived incremental README and manifest fragments under `archive/`.
- Renamed the shadowed module `src/s2flow/proof/certificates.py` to `certificate_api.py` when present.

## Recommended logical structure

The present physical layout is usable and was not aggressively reorganised because moving historical modules would risk breaking imports and old certificates. Its logical interpretation is:

```text
src/goldberg_s2/       Current closed-form and interval-certified Goldberg theorem
scripts/stage2_*.py    Current analytic flower theorem
src/s2flow/            General research framework and earlier finite-graph machinery
certificates/          Exact flower and Goldberg proof certificates
results/               Reproducible numerical and exact verification outputs
docs/                  Current papers plus historical reports
source_notes/           Supplied derivations and provenance material
legacy/                 Original monolithic reproduction script
archive/                Superseded metadata retained for provenance
```

For a future major release, a cleaner split would be:

```text
src/s2flow/families/flower/
src/s2flow/families/goldberg/
src/s2flow/general/
archive/reports/
```

That refactor should be performed only with import-compatibility shims and a versioned migration note.

## Findings by severity

### Resolved release blockers

1. **Unresolved licence conflict.** The original `LICENSE` simultaneously contained MIT and AGPL-3.0 text separated by Git conflict markers. A public release cannot have an indeterminate licence.
2. **Missing installation files.** `README.md` referred to `requirements-dev.txt`, which was absent.
3. **Broken default certificate location.** `scripts/equivariance_all_generators.py` pointed to a directory not included in the repository.
4. **Machine-specific absolute paths.** Independent verification and Kantorovich scripts contained `/home/claude/...` paths.
5. **Generated artefacts committed as source.** Python caches and package metadata obscured the actual source tree.

### Remaining publication tasks

1. Add the exact public GitHub URL to `CITATION.cff` after confirming the repository owner and name. The archive did not contain `.git` metadata or a remote URL, and the public repository could not be identified reliably from its generic name.
2. Create a permanent release and DOI, preferably through GitHub Releases plus Zenodo, after the manuscript is frozen.
3. Keep the theorem statements, code, and article version synchronised through tagged releases.
4. Obtain independent mathematical review before claiming priority. The universal `S^2`-flow conjecture is not claimed; the results concern two infinite snark families.
5. Decide whether historical DOCX files belong in the public source repository or in a release asset bundle. They are useful for provenance but increase repository size.

## Reproduced checks

The reviewed archive was installed with:

```bash
python -m pip install -e ".[dev,plot,symbolic,report]"
```

The following checks completed successfully during the audit:

- Python compilation of `src`, `scripts`, and `tests`;
- complete Pytest suite: 28 tests passed;
- Goldberg exact interval certificate generation and verification;
- numerical Goldberg sweep over 499 odd parameters through `k = 1001`;
- full-graph Goldberg expansion for 149 parameters through `k = 301`;
- flower Route 2 symbolic, rational, dense numerical, and high-precision checks;
- exact verification of the stored dyadic flower certificates.

The complete commands, outputs, and epistemic status of each run are documented in `RUNBOOK.md`.

## GitHub comparison limitation

The supplied ZIP does not contain `.git/`, a Git remote, or an unambiguous repository URL. Therefore this audit verifies the archive itself but cannot prove that the GitHub default branch is byte-for-byte identical. Use the commands in the GitHub parity section of `RUNBOOK.md` from a clone of the public repository.
