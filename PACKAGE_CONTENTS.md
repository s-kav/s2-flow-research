# Package Contents

## Primary deliverables

- `RUNBOOK.md`: complete execution catalogue with outputs and proof status.
- `REPOSITORY_AUDIT.md`: structure review, corrections, and release recommendations.
- `manuscript/S2_Flows_Flower_Goldberg_Snarks.docx`: English journal manuscript.
- `manuscript/S2_Flows_Flower_Goldberg_Snarks_Supplementary.docx`: English supplementary material.
- `manuscript/latex/main.tex`: LaTeX source for the main manuscript.
- `manuscript/latex/supplementary.tex`: LaTeX source for the supplementary material.
- `manuscript/latex/main.pdf` and `supplementary.pdf`: compiled LaTeX previews.

## Mathematical implementations

- `scripts/stage2_reduced.py` and `verify_route2_algebra.py`: flower-snark analytic reduction and verification.
- `src/goldberg_s2/`: Goldberg construction, scalar reduction, exact interval arithmetic, and full-graph verification.
- `certificates/`: exact interval and dyadic certificates.
- `src/s2flow/proof/`: structural lemmas, symbolic tools, certificate interfaces, and search infrastructure.

## Reproducibility infrastructure

- `scripts/reproduce_project.py`: combined theorem reproduction.
- `scripts/reproduce_all.py`: Goldberg theorem reproduction.
- `scripts/verify_all.py`: consolidated flower and regression checks.
- `.github/workflows/ci.yml`: continuous-integration checks.
- `tests/`: 28 automated tests in the reviewed environment.
- `requirements.txt`, `requirements-dev.txt`, `pyproject.toml`, and `uv.lock`: environment definitions.

## Provenance and historical material

- `docs/`: theorem reports and development documents.
- `source_notes/`: supplied source notes.
- `legacy/`: original monolithic implementation.
- `archive/`: superseded metadata and the original conflicted licence retained for auditability.
