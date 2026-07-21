# Rigorous equivariance addendum for flower-snark S²-flows

This package removes three reproducibility and proof-status gaps from the
first equivariance addendum.

## What is now rigorous

1. **The strict order-2n ansatz is impossible for every odd n >= 5.**
   The result is proved analytically for all proper and improper orthogonal
   generators. It no longer relies on Levenberg-Marquardt or a finite angle
   sweep.
2. **The J15-J41 existence claims are accompanied by complete certificates.**
   Nineteen compressed dyadic certificates for J5-J41 are included in `certificates/`.
   The independent verifier reconstructs all Newton-Kantorovich inequalities
   with arbitrary-precision integer arithmetic.
3. **Every cyclic generator is tested.**
   `equivariance_all_generators.py` evaluates every exponent coprime to 2n,
   validates the pipeline on synthetic exactly equivariant data, and uses the
   correct cyclic pullback in the averaging formula.

## One-command verification

```bash
python -m pip install -r requirements.txt
python scripts/verify_all.py
```

## Rebuild numerical candidates and certificates

```bash
python scripts/zn_ansatz.py --min-n 5 --max-n 41
python scripts/exact_rational_certificates.py --min-n 5 --max-n 41
python scripts/verify_exact_certificates.py
```

The exact verifier has no SciPy dependency at runtime; SciPy is needed only to
rebuild the floating-point candidates and approximate inverse Jacobians.

## Mathematical scope

The package rigorously proves existence for the finite range J5-J41 through
the nineteen included exact dyadic certificates. The proposed all-n continuation on
`theta in (0, 2*pi/5]` remains a separate Stage 2 theorem to be proved.
