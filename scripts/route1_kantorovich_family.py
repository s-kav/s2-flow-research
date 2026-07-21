"""Route 1: computer-rigorous certification of the solution branch of the
reduced 18x18 flower snark system over a whole parameter interval.

Parameterization.  u = theta/2 = pi/n; Weierstrass substitution
t = tan(u/2) makes every coefficient of the square system rational:

    cos u = (1 - t^2)/(1 + t^2),      sin u = 2t/(1 + t^2),
    cos 2u = (1 - 6t^2 + t^4)/(1+t^2)^2,  sin 2u = 4t(1 - t^2)/(1+t^2)^2.

The square system F(x, t) = 0 (18 equations, 18 unknowns) consists of
E1, E2_xy, E3, E4, six unit-norm equations and the gauge H_y = 0, with
A(t) = R_z(pi - u) and R^{-1}(t) = R_z(-2u).  Only the Kirchhoff rows
depend on t; all dependence is through the four rational functions above.

Certificate.  The interval [T_MIN, T_STAR] = [10^-7, 13/40] is covered by
finitely many closed subintervals [t1, t2].  On each subinterval we fix a
rational candidate x_hat (built in 40-digit arithmetic from the scalar
cascade and rationalized to denominator <= 10^22) and a rational
approximate inverse A_hat of the Jacobian at the midpoint, and we compute,
in EXACT rational interval arithmetic (no floating point, no rounding),
rational bounds

    alpha >= sup_t ||A_hat F(x_hat, t)||_2,
    beta  >= sup_t ||I - A_hat J(x_hat, t)||_2,
    omega  = 2 * ||A_hat||_2-bound        (Lipschitz constant of J in x is
                                           exactly 2 in the l2 norm, for all t),

and accept the subinterval iff  beta < 1  and  4 alpha omega <= (1-beta)^2.
By the Newton-Kantorovich/contraction theorem this proves: for EVERY real
t in the subinterval the system F(., t) has a solution within
r = (1-beta)/(2 omega) of x_hat.  Since tan(pi/(2n)) lies in [T_MIN, T_STAR]
for every odd 5 <= n <= 15,707,963  (because tan x >= x gives
tan(pi/(2n)) >= pi/(2n) >= 10^-7 for n <= pi/2 * 10^7, and
tan(pi/10) < 13/40 was verified exactly), the certified family contains a
solution for each such n, which expands to an exact S2-flow on J_n by the
expansion lemma.

The union of certificates therefore constitutes a machine proof for all
odd n from 5 up to 15,707,963 -- independent of, and complementary to, the
analytic proof (Route 2) that covers all odd n >= 5.

Output: route1_results.json with every subinterval and its constants.
"""

import hashlib
import argparse
import json
import math
import time
from fractions import Fraction
from pathlib import Path

import mpmath as mp
import numpy as np

import stage2_reduced as sr

try:
    from kantorovich_certify import sqrt_upper, norm1_inf_bound_sq
except ModuleNotFoundError:
    import os
    import sys
    _here = os.path.dirname(os.path.abspath(__file__))
    _candidates = [
        os.path.join(_here, "scripts"),
        os.path.join(_here, "..", "scripts"),
        os.path.join(_here, "s2-flow-research", "scripts"),
        os.path.join(_here, "..", "s2-flow-research", "scripts"),
    ]
    for _c in _candidates:
        if os.path.isfile(os.path.join(_c, "kantorovich_certify.py")):
            sys.path.insert(0, _c)
            break
    else:
        raise ModuleNotFoundError(
            "kantorovich_certify.py not found next to this file or in "
            "scripts/, ../scripts/, s2-flow-research/scripts/; it lives in "
            "the s2-flow-research repository under scripts/."
        )
    from kantorovich_certify import sqrt_upper, norm1_inf_bound_sq

UNIT = Fraction(1, 10**10)          # grid quantum for interval endpoints
T_MIN_UNITS = 10**3                 # 10^3 * 1e-10 = 1e-7
T_STAR_UNITS = 3_250_000_000        # 3.25e9 * 1e-10 = 0.325 = 13/40
X_DEN = 10**22                      # rationalization denominator for x_hat
A_DEN = 10**12                      # rationalization denominator for A_hat
CAND_DPS = 40                       # candidate precision (digits)


class IV:
    """Closed interval with exact Fraction endpoints; all ops exact."""

    __slots__ = ("lo", "hi")

    def __init__(self, lo, hi=None):
        self.lo = lo
        self.hi = lo if hi is None else hi

    def __add__(self, o):
        if isinstance(o, IV):
            return IV(self.lo + o.lo, self.hi + o.hi)
        return IV(self.lo + o, self.hi + o)

    def __sub__(self, o):
        if isinstance(o, IV):
            return IV(self.lo - o.hi, self.hi - o.lo)
        return IV(self.lo - o, self.hi - o)

    def __neg__(self):
        return IV(-self.hi, -self.lo)

    def __mul__(self, o):
        if not isinstance(o, IV):
            o = IV(o)
        if self.lo == self.hi:
            p = self.lo
            if p >= 0:
                return IV(p * o.lo, p * o.hi)
            return IV(p * o.hi, p * o.lo)
        if o.lo == o.hi:
            return o.__mul__(self)
        c1, c2 = self.lo * o.lo, self.lo * o.hi
        c3, c4 = self.hi * o.lo, self.hi * o.hi
        return IV(min(c1, c2, c3, c4), max(c1, c2, c3, c4))

    __rmul__ = __mul__

    def __truediv__(self, o):
        if not isinstance(o, IV):
            o = IV(o)
        if o.lo <= 0 <= o.hi:
            raise ZeroDivisionError("interval denominator contains zero")
        inv = IV(1 / o.hi, 1 / o.lo)
        return self.__mul__(inv)

    def mag(self):
        return max(abs(self.lo), abs(self.hi))


def coeff_intervals(t1: Fraction, t2: Fraction):
    """Exact interval enclosures of cos u, sin u, cos 2u, sin 2u on [t1,t2].

    0 <= t1 <= t2 < 1 is assumed (our range is within [1e-7, 0.325]).
    """
    if not (0 <= t1 <= t2 < 1):
        raise ValueError(f"interval out of range [0, 1): [{t1}, {t2}]")
    q = IV(t1 * t1, t2 * t2)                      # t^2, exact (monotone, t>=0)
    one = Fraction(1)
    den1 = IV(one) + q                            # 1 + t^2 in [1+t1^2, 1+t2^2]
    c = (IV(one) - q) / den1                      # cos u
    s = (IV(2) * IV(t1, t2)) / den1               # sin u
    den2 = den1 * den1
    c2 = (IV(one) - IV(6) * q + q * q) / den2     # cos 2u
    s2 = (IV(4) * IV(t1, t2) * (IV(one) - q)) / den2  # sin 2u
    return c, s, c2, s2


def residual_interval(x, c, s, c2, s2):
    """F(x, [t]) as 18 IV rows; x is a list of 18 Fractions."""
    h = x[0:3]
    t = x[3:6]
    f = x[6:9]
    g = x[9:12]
    p = x[12:15]
    q = x[15:18]
    # A = R_z(pi - u): xy block [[-c, -s], [s, -c]], z = 1
    ag = [(-c) * g[0] + (-s) * g[1], s * g[0] + (-c) * g[1], IV(g[2])]
    at = [(-c) * t[0] + (-s) * t[1], s * t[0] + (-c) * t[1], IV(t[2])]
    # R^{-1} = R_z(-2u): xy block [[c2, s2], [-s2, c2]], z = 1
    rq = [c2 * q[0] + s2 * q[1], (-s2) * q[0] + c2 * q[1], IV(q[2])]
    rows = []
    for i in range(3):                            # E1
        rows.append(IV(h[i]) + IV(f[i]) + ag[i])
    for i in range(2):                            # E2 xy
        rows.append(IV(t[i]) - IV(h[i]) - at[i])
    for i in range(3):                            # E3
        rows.append(IV(p[i]) - IV(f[i]) - rq[i])
    for i in range(3):                            # E4
        rows.append(IV(q[i]) - IV(g[i]) - IV(p[i]))
    for blk in (h, t, f, g, p, q):                # norms
        rows.append(IV(blk[0] * blk[0] + blk[1] * blk[1]
                       + blk[2] * blk[2] - 1))
    rows.append(IV(h[1]))                         # gauge
    return rows


def jacobian_interval(x, c, s, c2, s2):
    """J(x, [t]) as an 18x18 matrix of IV entries."""
    zero = IV(Fraction(0))
    one = IV(Fraction(1))
    jac = [[zero for _ in range(18)] for _ in range(18)]
    # E1 rows 0..2: d/dH = I, d/dF = I, d/dG = A
    for i in range(3):
        jac[i][0 + i] = one
        jac[i][6 + i] = one
    jac[0][9], jac[0][10] = -c, -s
    jac[1][9], jac[1][10] = s, -c
    jac[2][11] = one
    # E2 xy rows 3..4: d/dT = (I - A)_xy, d/dH = -I_xy
    jac[3][3] = one - (-c)
    jac[3][4] = zero - (-s)
    jac[4][3] = zero - s
    jac[4][4] = one - (-c)
    jac[3][0] = IV(Fraction(-1))
    jac[4][1] = IV(Fraction(-1))
    # E3 rows 5..7: d/dP = I, d/dF = -I, d/dQ = -R^{-1}
    for i in range(3):
        jac[5 + i][12 + i] = one
        jac[5 + i][6 + i] = IV(Fraction(-1))
    jac[5][15], jac[5][16] = -c2, -s2
    jac[6][15], jac[6][16] = s2, -c2
    jac[7][17] = IV(Fraction(-1))
    # E4 rows 8..10: d/dQ = I, d/dG = -I, d/dP = -I
    for i in range(3):
        jac[8 + i][15 + i] = one
        jac[8 + i][9 + i] = IV(Fraction(-1))
        jac[8 + i][12 + i] = IV(Fraction(-1))
    # norm rows 11..16: 2 x_blk
    for b in range(6):
        for i in range(3):
            jac[11 + b][3 * b + i] = IV(2 * x[3 * b + i])
    # gauge row 17
    jac[17][1] = one
    return jac


def mat_point_times_iv(a, m):
    """a: 18x18 Fractions; m: 18x18 IV -> 18x18 IV product."""
    n = 18
    out = [[None] * n for _ in range(n)]
    for i in range(n):
        ai = a[i]
        for j in range(n):
            acc_lo = Fraction(0)
            acc_hi = Fraction(0)
            for k in range(n):
                p = ai[k]
                if p == 0:
                    continue
                e = m[k][j]
                if e.lo == 0 == e.hi:
                    continue
                if p >= 0:
                    acc_lo += p * e.lo
                    acc_hi += p * e.hi
                else:
                    acc_lo += p * e.hi
                    acc_hi += p * e.lo
            out[i][j] = IV(acc_lo, acc_hi)
    return out


def vec_point_times_iv(a, v):
    n = 18
    out = []
    for i in range(n):
        acc_lo = Fraction(0)
        acc_hi = Fraction(0)
        ai = a[i]
        for k in range(n):
            p = ai[k]
            if p == 0:
                continue
            e = v[k]
            if p >= 0:
                acc_lo += p * e.lo
                acc_hi += p * e.hi
            else:
                acc_lo += p * e.hi
                acc_hi += p * e.lo
        out.append(IV(acc_lo, acc_hi))
    return out


def candidate_mp(u_float):
    """High-precision candidate templates via the scalar cascade (40 digits)."""
    with mp.workdps(CAND_DPS):
        u = mp.mpf(u_float)
        s_mp, c_mp = mp.sin(u), mp.cos(u)

        def sqrt_checked(v, tol=mp.mpf("1e-30")):
            if v < -tol:
                raise ValueError(f"negative radicand beyond tolerance: {v}")
            return mp.sqrt(v if v > 0 else mp.mpf(0))

        def h_mp(m):
            eta = m * s_mp
            zeta = -sqrt_checked(mp.mpf(3) / 4 - eta**2)
            rho2 = 1 / (8 * (1 + c_mp)) + (m**2 * (1 + c_mp) + m) / 2
            return (mp.mpf(3) / 8 - eta**2 / 2 - m / 2
                    + zeta * sqrt_checked(1 - rho2))

        root = 2 * mp.sqrt(2 * (1 + c_mp))
        lo = (-1 - root) / (2 * (1 + c_mp))
        hi = mp.mpf(0)
        v_lo, v_hi = h_mp(lo), h_mp(hi)
        if not (v_lo > 0 > v_hi):
            raise RuntimeError(
                f"IVT endpoints violated in candidate_mp at u={u_float!r}: "
                f"h(m_-)={mp.nstr(v_lo, 8)}, h(0)={mp.nstr(v_hi, 8)}"
            )
        for _ in range(160):
            mid = (lo + hi) / 2
            if v_lo * h_mp(mid) > 0:
                lo = mid
            else:
                hi = mid
        m = (lo + hi) / 2

        eta = m * s_mp
        zeta = -sqrt_checked(mp.mpf(3) / 4 - eta**2)
        ca, sa = mp.cos(mp.pi - u), mp.sin(mp.pi - u)
        gp = (-mp.mpf(1) / 2, eta, zeta)
        g_vec = (ca * gp[0] + sa * gp[1], -sa * gp[0] + ca * gp[1], gp[2])
        f_vec = (-mp.mpf(1) / 2, -eta, -zeta)
        c2m, s2m = mp.cos(2 * u), mp.sin(2 * u)
        b0 = f_vec[0] + c2m * g_vec[0] + s2m * g_vec[1]
        b1 = f_vec[1] - s2m * g_vec[0] + c2m * g_vec[1]
        p_x = (s_mp * b0 + c_mp * b1) / (2 * s_mp)
        p_y = (-c_mp * b0 + s_mp * b1) / (2 * s_mp)
        rho2 = 1 / (8 * (1 + c_mp)) + (m**2 * (1 + c_mp) + m) / 2
        p_vec = (p_x, p_y, sqrt_checked(1 - rho2))
        q_vec = (g_vec[0] + p_vec[0], g_vec[1] + p_vec[1], g_vec[2] + p_vec[2])
        den = 2 + 2 * c_mp
        t_vec = (mp.mpf(1) / 2, s_mp / den, sqrt_checked((1 + 2 * c_mp) / den))
        vals = [mp.mpf(1), mp.mpf(0), mp.mpf(0)]
        vals += list(t_vec) + list(f_vec) + list(g_vec)
        vals += list(p_vec) + list(q_vec)
        return [mp.nstr(v, CAND_DPS - 2) for v in vals]


def rationalize_strs(strs, den_limit):
    out = []
    for s_ in strs:
        out.append(Fraction(s_).limit_denominator(den_limit))
    return out


def certify_interval(t1: Fraction, t2: Fraction):
    """Try to certify [t1, t2]; return dict on success, None on failure."""
    t_mid = (t1 + t2) / 2
    u_mid = 2.0 * math.atan(float(t_mid))
    x_strs = candidate_mp(u_mid)
    x = rationalize_strs(x_strs, X_DEN)

    x_float = np.array([float(v) for v in x])
    jf = sr.jacobian_square(x_float, u_mid)
    a_float = np.linalg.inv(jf)
    a = [
        [Fraction(a_float[i, j]).limit_denominator(A_DEN) for j in range(18)]
        for i in range(18)
    ]

    c, s, c2, s2 = coeff_intervals(t1, t2)
    fv = residual_interval(x, c, s, c2, s2)
    av = vec_point_times_iv(a, fv)
    alpha2 = Fraction(0)
    for e in av:
        mgn = e.mag()
        alpha2 += mgn * mgn
    alpha = sqrt_upper(alpha2)

    jm = jacobian_interval(x, c, s, c2, s2)
    aj = mat_point_times_iv(a, jm)
    mmat = [
        [
            (IV(Fraction(1)) - aj[i][j]) if i == j else (-aj[i][j])
            for j in range(18)
        ]
        for i in range(18)
    ]
    mm = [[mmat[i][j].mag() for j in range(18)] for i in range(18)]
    beta = sqrt_upper(norm1_inf_bound_sq(mm))

    am = [[abs(a[i][j]) for j in range(18)] for i in range(18)]
    norm_a = sqrt_upper(norm1_inf_bound_sq(am))
    omega = 2 * norm_a

    if beta >= 1:
        return None
    if 4 * alpha * omega > (1 - beta) ** 2:
        return None
    r = (1 - beta) / (2 * omega)
    x_strs_out = [str(v) for v in x]
    a_strs_out = [str(a[i][j]) for i in range(18) for j in range(18)]
    payload = "|".join([str(t1), str(t2), ";".join(x_strs_out),
                        ";".join(a_strs_out)])
    digest = hashlib.sha256(payload.encode("ascii")).hexdigest()
    return {
        "t_lo": str(t1),
        "t_hi": str(t2),
        "t_lo_float": float(t1),
        "t_hi_float": float(t2),
        "x_hat": x_strs_out,
        "A_hat": a_strs_out,
        "sha256": digest,
        "alpha": float(alpha),
        "beta": float(beta),
        "norm_A": float(norm_a),
        "radius": float(r),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("results/json/route1_results_full.json"))
    args = parser.parse_args()
    t0 = time.time()
    results = []
    hi_units = T_STAR_UNITS
    ratio = 0.010                      # delta ~ ratio * t, adapted on the fly
    fails_in_a_row = 0
    steps = tries = 0
    while hi_units > T_MIN_UNITS:
        tries += 1
        delta_units = max(1, int(hi_units * ratio))
        lo_units = max(T_MIN_UNITS, hi_units - delta_units)
        t1 = Fraction(lo_units, 10**10)
        t2 = Fraction(hi_units, 10**10)
        cert = certify_interval(t1, t2)
        if cert is None:
            fails_in_a_row += 1
            ratio *= 0.5
            if fails_in_a_row > 60:
                raise RuntimeError(
                    f"cannot certify below t = {float(t2):.3e}"
                )
            continue
        fails_in_a_row = 0
        results.append(cert)
        steps += 1
        hi_units = lo_units
        ratio = min(ratio * 1.15, 0.25)
        if steps % 50 == 0:
            print(
                f"  {steps:4d} intervals, t down to {float(t1):.4e}, "
                f"beta={cert['beta']:.2e}, |A|={cert['norm_A']:.2e}, "
                f"ratio={ratio:.4f}, {time.time() - t0:.0f}s",
                flush=True,
            )
    worst_beta = max(r_["beta"] for r_ in results)
    worst_alpha = max(r_["alpha"] for r_ in results)
    max_norm_a = max(r_["norm_A"] for r_ in results)
    n_max = 15_707_963
    summary = {
        "intervals": len(results),
        "attempts": tries,
        "t_min": str(Fraction(T_MIN_UNITS, 10**10)),
        "t_star": str(Fraction(T_STAR_UNITS, 10**10)),
        "worst_beta": worst_beta,
        "worst_alpha": worst_alpha,
        "max_norm_A": max_norm_a,
        "covered_odd_n_from": 5,
        "covered_odd_n_to": n_max,
        "runtime_seconds": round(time.time() - t0, 1),
        "candidate_dps": CAND_DPS,
        "x_denominator_limit": X_DEN,
        "A_denominator_limit": A_DEN,
        "certificate_format": (
            "Each certificate carries the exact rational data (t_lo, t_hi, "
            "x_hat as 18 fractions, A_hat as 18x18 fractions row-major) plus "
            "a sha256 of the canonical payload t_lo|t_hi|x;...|A;... . "
            "The floats alpha/beta/norm_A/radius are informational; an "
            "independent verifier must recompute rational bounds from the "
            "exact data and re-check beta < 1 and 4*alpha*omega <= "
            "(1-beta)^2 with omega = 2*norm_A (see "
            "recheck_route1_certificates.py)."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as fh:
        json.dump({"summary": summary, "intervals": results}, fh, indent=1)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
