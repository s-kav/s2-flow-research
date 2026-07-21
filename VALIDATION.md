# Validation Record

Validation date: 21 July 2026

## Scope

This record covers the reviewed release contained in this repository. It distinguishes proof-bearing exact checks from numerical regression checks and from document-quality checks.

## Repository checks

- Python sources in `src/`, `scripts/`, `tests/`, and `benchmarks/` compile successfully.
- The complete automated test suite passes: **28 tests passed**.
- Installation metadata is present through `pyproject.toml`, `requirements.txt`, `requirements-dev.txt`, and `uv.lock`.
- The active licence is MIT. The unresolved licence file from the supplied archive is retained only for provenance at `archive/LICENSE_with_unresolved_merge_conflict.txt`.
- Continuous integration is defined in `.github/workflows/ci.yml`.

## Proof-bearing flower-snark checks

- `scripts/verify_route2_algebra.py` passed all symbolic identities, exact rational inequalities, dense numerical diagnostics, high-precision reconstructions, uniqueness checks, and asymptotic checks supporting the analytic Route 2 proof.
- `scripts/verify_exact_certificates.py` independently verified **19 exact dyadic certificates** for the stored flower instances.
- The all-generator equivariance diagnostic validates all documented cyclic generators when run on the stored certificates.

The universal flower-family theorem is carried by the analytic scalar argument. The finite certificates and numerical checks are independent validation, not the logical basis for extrapolating to infinitely many graphs.

## Proof-bearing Goldberg-snark checks

- `scripts/verify_interval_certificate.py` independently verified the exact rational interval certificate.
- The verified conservative bounds are:
  - `H(2/3, x) < -0.281883098523`;
  - `H(21/25, x) > 0.0585614726995`;
  - `dH/ds > 1.22089199979`;
  for the certified parameter rectangle.
- `scripts/reproduce_all.py` regenerated the interval certificate, checked it independently, performed the numerical sweep, verified `G_1001`, regenerated figures and the Goldberg Word report, and ran the test suite.

The Goldberg-family theorem uses the analytic reduction plus this exact interval certificate. The finite graph sweep is regression validation only.

## Numerical campaign checks

The reviewed release reproduced:

- **499** odd Goldberg parameters from `k = 5` through `k = 1001`;
- **149** complete Goldberg graph expansions through `k = 301`;
- `G_1001` with 8,008 vertices and 12,012 edges;
- worst reduced Kirchhoff residual approximately `3.04e-16`;
- worst reduced unit residual approximately `2.22e-15`;
- worst full-graph Kirchhoff residual approximately `7.20e-14`;
- worst full-graph unit residual approximately `3.71e-14`.

These runs confirm implementation consistency, orientation conventions, orbit indexing, seam handling, and numerical reconstruction. They do not by themselves prove an infinite-family theorem.

## Consolidated orchestration note

`scripts/reproduce_project.py` is the documented full orchestration entry point. In the review environment, its Goldberg stage completed successfully, after which the enclosing tool session reached its execution-time limit while starting the flower analytic verifier. Every remaining component command was then run separately and passed. Therefore the timeout was an orchestration-environment limit, not a failed mathematical or software check.

## Manuscript checks

- Main article DOCX rendered successfully and was visually inspected: **4 pages**.
- Main article LaTeX compiled successfully and was visually inspected: **6 pages**.
- Supplementary DOCX rendered successfully and was visually inspected: **3 pages**.
- Supplementary LaTeX compiled successfully and was visually inspected: **4 pages**.
- No clipping, overlapping objects, truncated equations, or broken page elements were observed.
- The main article remains below the requested 15-page limit in both supplied formats.

## GitHub parity limitation

The supplied ZIP did not contain `.git/`, a Git remote, or an unambiguous public repository URL. The archive itself was validated, but byte-for-byte parity with the GitHub default branch cannot be established from the supplied material. `RUNBOOK.md` provides clone, remote, tag, diff, and manifest commands for performing that comparison from the actual GitHub clone.

## Release recommendation

Before public submission or Zenodo deposition:

1. insert the confirmed GitHub URL into `CITATION.cff` and the manuscript data-availability statement;
2. create a signed or annotated release tag;
3. archive the exact release and mint a DOI;
4. obtain independent expert review of the elimination steps and interval bounds;
5. keep historical reports outside the source distribution or publish them as release assets.
