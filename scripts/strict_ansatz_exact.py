"""Exact algebraic refutation of the strict order-2n equivariant ansatz.

The proof applies to every odd flower parameter n, not only to J_5.  It is
independent of floating-point optimisation and of any finite angle sweep.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import sympy as sp


def symbolic_identity_check() -> dict[str, str]:
    """Verify the scalar contradiction in the improper-orthogonal case."""
    lam = sp.symbols("lambda", real=True)
    b_planar_sq = sp.Integer(1)
    a_sq = sp.simplify(lam * b_planar_sq)

    c_planar_sq = sp.Rational(1, 4)
    c_axis_sq = sp.Rational(3, 4)
    d_axis_sq = sp.simplify(c_axis_sq / 4)
    d_planar_sq = sp.simplify(1 - d_axis_sq)
    c_sq_from_difference = sp.simplify(lam * d_planar_sq + 4 * d_axis_sq)
    contradiction_at_lam_one = sp.simplify(c_sq_from_difference.subs(lam, 1) - 1)

    assert a_sq.subs(lam, 1) == 1
    assert d_axis_sq == sp.Rational(3, 16)
    assert d_planar_sq == sp.Rational(13, 16)
    assert c_sq_from_difference.subs(lam, 1) == sp.Rational(25, 16)
    assert contradiction_at_lam_one == sp.Rational(9, 16)

    return {
        "lambda_from_a_and_b": "1",
        "c_planar_norm_squared": str(c_planar_sq),
        "c_axis_norm_squared": str(c_axis_sq),
        "d_axis_norm_squared": str(d_axis_sq),
        "d_planar_norm_squared": str(d_planar_sq),
        "forced_c_norm_squared": str(c_sq_from_difference.subs(lam, 1)),
        "contradiction_excess": str(contradiction_at_lam_one),
    }


def theorem_text() -> str:
    return (
        "For every odd n >= 5, no unit S^2-flow on the flower snark J_n can "
        "be equivariant under the full one-block automorphism of order 2n "
        "through a single orthogonal matrix Q in O(3)."
    )


def proof_outline() -> list[str]:
    return [
        "Choose canonical orientations A_i=c_i->t_i, B_i=t_i->t_{i+1}, "
        "C_j=c_{j mod n}->w_j, and D_j=w_j->w_{j+1}.",
        "Strict equivariance gives A_i=Q^i a, B_i=Q^i b, C_j=Q^j c, "
        "D_j=Q^j d with unit templates a,b,c,d.",
        "Kirchhoff equations reduce exactly to a=(I-Q^{-1})b, "
        "c=(I-Q^{-1})d, and a+(I+Q^n)c=0, together with "
        "Q^n a=a, Q^n b=b, Q^{2n}c=c, Q^{2n}d=d.",
        "If det(Q)=+1, Q is a rotation. Since b is not fixed by Q but is "
        "fixed by Q^n, Q^n=I. The hub equation becomes a+2c=0, "
        "contradicting |a|=|c|=1.",
        "If det(Q)=-1 and n is odd, decompose R^3=P plus L, where Q is a "
        "planar rotation on P and -1 on L. Q^n b=b forces b in P and "
        "Q^n|P=I. Writing lambda=4 sin^2(theta/2), the first Kirchhoff "
        "equation and unit norms force lambda=1.",
        "The hub equation gives |c_P|^2=1/4 and |c_L|^2=3/4. Because "
        "c=(I-Q^{-1})d, this forces |d_L|^2=3/16 and |d_P|^2=13/16. "
        "Hence |c|^2=lambda*13/16+4*3/16=25/16, contradiction.",
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("results/strict_ansatz_exact.json"))
    args = parser.parse_args()
    payload = {
        "status": "proved",
        "theorem": theorem_text(),
        "scope": "all odd n >= 5",
        "method": "exact orthogonal spectral decomposition and rational algebra",
        "symbolic_check": symbolic_identity_check(),
        "proof_outline": proof_outline(),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(theorem_text())
    print("Exact contradiction verified: 25/16 != 1")
    print(f"Saved {args.output}")


if __name__ == "__main__":
    main()
