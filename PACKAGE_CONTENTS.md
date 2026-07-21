# Package contents

## Main mathematical report

- `docs/S2_flow_partial_theorems_and_structural_lemmas_ru.docx`

The report gives complete proofs for the project-level partial theorems and
structural lemmas, explicitly separates known results from project-derived
results, and states that the universal S²-flow conjecture remains open.

## Reproducibility code

- `src/s2flow/proof/theory/`: exact constructive and structural algorithms.
- `src/s2flow/computation/`: deterministic large-scale campaign orchestration.
- `scripts/massive_verification.py`: sampled and named graph campaign.
- `scripts/verify_campaign.py`: independent certificate verifier.
- `scripts/nauty_cubic_campaign.py`: streaming graph6 input from nauty `geng`.
- `scripts/build_partial_results_report.py`: report and figure regeneration.
- `tests/`: unit and regression tests.

## Stored campaign

- `results/massive_run/campaign.json`
- `results/massive_run/summary.csv`
- `results/massive_run/certificates/*.npz`

The bundled campaign contains 288 certificates, of which 280 are constructed
from proper 3-edge-colourings and 8 are numerical cycle-space certificates.
The independent verifier accepts all 288 under the documented tolerance.

## Research support layer

The broader `src/s2flow/proof/` hierarchy includes candidate lemma checks,
reduction search, symbolic polynomial systems, and certificate utilities. These
modules are research tools, not machine-checked proofs of the universal
conjecture.
