"""Independent verifier for route1_results.json.

This script is deliberately self-contained: it imports nothing from the
project modules and re-implements exact rational interval arithmetic, the
residual and Jacobian of the square system, and the norm bounds from
scratch.  For every stored certificate it

  1. parses the exact rational data (t_lo, t_hi, x_hat, A_hat),
  2. recomputes rational bounds alpha >= sup ||A_hat F(x_hat, t)||_2 and
     beta >= sup ||I - A_hat J(x_hat, t)||_2 over the whole subinterval,
     and omega = 2 * ||A_hat||_2-bound,
  3. re-checks the Kantorovich acceptance beta < 1 and
     4 alpha omega <= (1 - beta)^2,
  4. recomputes the sha256 of the canonical payload and compares.

It then checks global coverage: the subintervals tile [1/10^7, 13/40] with
no gaps and no overlaps, so every t in the range -- in particular
t_n = tan(pi/(2n)) for every odd 5 <= n <= 15,707,963 -- lies in a
certified subinterval.

As a non-certifying sanity check it also rebuilds, in float64, the cascade
solution at both endpoints of every 100th subinterval and confirms it lies
within the certified radius of the stored candidate.

Exit code 0 iff everything verifies.
"""

import hashlib
import argparse
import argparse
import json
import math
import sys
from fractions import Fraction
from pathlib import Path


# ----------------------------------------------------------------- intervals
class IV:
    """Closed interval with exact Fraction endpoints; all operations exact."""

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
            pt = self.lo
            if pt >= 0:
                return IV(pt * o.lo, pt * o.hi)
            return IV(pt * o.hi, pt * o.lo)
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
        return self.__mul__(IV(1 / o.hi, 1 / o.lo))

    def mag(self):
        return max(abs(self.lo), abs(self.hi))


def sqrt_upper(q: Fraction) -> Fraction:
    """Rational upper bound for sqrt(q), q >= 0."""
    if q < 0:
        raise ValueError("negative argument to sqrt_upper")
    a, b = q.numerator, q.denominator
    return Fraction(math.isqrt(a * b) + 1, b)


def norm2_sq_upper(mat):
    """Rational upper bound for ||M||_2^2 via ||M||_1 * ||M||_inf."""
    rows, cols = len(mat), len(mat[0])
    col_sums = [Fraction(0)] * cols
    row_max = Fraction(0)
    for i in range(rows):
        s = Fraction(0)
        for j in range(cols):
            a = abs(mat[i][j])
            s += a
            col_sums[j] += a
        row_max = max(row_max, s)
    return row_max * max(col_sums)


# ------------------------------------------------- system over an interval
def coeff_intervals(t1: Fraction, t2: Fraction):
    if not (0 <= t1 <= t2 < 1):
        raise ValueError(f"interval out of range [0, 1): [{t1}, {t2}]")
    one = Fraction(1)
    q = IV(t1 * t1, t2 * t2)
    den1 = IV(one) + q
    c = (IV(one) - q) / den1
    s = (IV(2) * IV(t1, t2)) / den1
    den2 = den1 * den1
    c2 = (IV(one) - IV(6) * q + q * q) / den2
    s2 = (IV(4) * IV(t1, t2) * (IV(one) - q)) / den2
    return c, s, c2, s2


def residual_interval(x, c, s, c2, s2):
    h = x[0:3]
    t = x[3:6]
    f = x[6:9]
    g = x[9:12]
    p = x[12:15]
    q = x[15:18]
    ag = [(-c) * g[0] + (-s) * g[1], s * g[0] + (-c) * g[1], IV(g[2])]
    at = [(-c) * t[0] + (-s) * t[1], s * t[0] + (-c) * t[1], IV(t[2])]
    rq = [c2 * q[0] + s2 * q[1], (-s2) * q[0] + c2 * q[1], IV(q[2])]
    rows = []
    for i in range(3):
        rows.append(IV(h[i]) + IV(f[i]) + ag[i])
    for i in range(2):
        rows.append(IV(t[i]) - IV(h[i]) - at[i])
    for i in range(3):
        rows.append(IV(p[i]) - IV(f[i]) - rq[i])
    for i in range(3):
        rows.append(IV(q[i]) - IV(g[i]) - IV(p[i]))
    for blk in (h, t, f, g, p, q):
        rows.append(IV(blk[0] * blk[0] + blk[1] * blk[1]
                       + blk[2] * blk[2] - 1))
    rows.append(IV(h[1]))
    return rows


def jacobian_interval(x, c, s, c2, s2):
    zero = IV(Fraction(0))
    one = IV(Fraction(1))
    neg1 = IV(Fraction(-1))
    jac = [[zero for _ in range(18)] for _ in range(18)]
    for i in range(3):
        jac[i][0 + i] = one
        jac[i][6 + i] = one
    jac[0][9], jac[0][10] = -c, -s
    jac[1][9], jac[1][10] = s, -c
    jac[2][11] = one
    jac[3][3] = one - (-c)
    jac[3][4] = zero - (-s)
    jac[4][3] = zero - s
    jac[4][4] = one - (-c)
    jac[3][0] = neg1
    jac[4][1] = neg1
    for i in range(3):
        jac[5 + i][12 + i] = one
        jac[5 + i][6 + i] = neg1
    jac[5][15], jac[5][16] = -c2, -s2
    jac[6][15], jac[6][16] = s2, -c2
    jac[7][17] = neg1
    for i in range(3):
        jac[8 + i][15 + i] = one
        jac[8 + i][9 + i] = neg1
        jac[8 + i][12 + i] = neg1
    for b in range(6):
        for i in range(3):
            jac[11 + b][3 * b + i] = IV(2 * x[3 * b + i])
    jac[17][1] = one
    return jac


def point_times_iv_vec(a_rows, v):
    out = []
    for ai in a_rows:
        acc_lo = Fraction(0)
        acc_hi = Fraction(0)
        for k in range(18):
            pt = ai[k]
            if pt == 0:
                continue
            e = v[k]
            if pt >= 0:
                acc_lo += pt * e.lo
                acc_hi += pt * e.hi
            else:
                acc_lo += pt * e.hi
                acc_hi += pt * e.lo
        out.append(IV(acc_lo, acc_hi))
    return out


def point_times_iv_mat(a_rows, m):
    out = [[None] * 18 for _ in range(18)]
    for i in range(18):
        ai = a_rows[i]
        for j in range(18):
            acc_lo = Fraction(0)
            acc_hi = Fraction(0)
            for k in range(18):
                pt = ai[k]
                if pt == 0:
                    continue
                e = m[k][j]
                if e.lo == 0 == e.hi:
                    continue
                if pt >= 0:
                    acc_lo += pt * e.lo
                    acc_hi += pt * e.hi
                else:
                    acc_lo += pt * e.hi
                    acc_hi += pt * e.lo
            out[i][j] = IV(acc_lo, acc_hi)
    return out


def verify_certificate(cert):
    """Re-verify one certificate from its exact rational data alone."""
    t1 = Fraction(cert["t_lo"])
    t2 = Fraction(cert["t_hi"])
    x = [Fraction(v) for v in cert["x_hat"]]
    if len(x) != 18 or len(cert["A_hat"]) != 324:
        return False, "malformed certificate arrays"
    a_flat = [Fraction(v) for v in cert["A_hat"]]
    a_rows = [a_flat[18 * i: 18 * i + 18] for i in range(18)]

    payload = "|".join([cert["t_lo"], cert["t_hi"],
                        ";".join(cert["x_hat"]), ";".join(cert["A_hat"])])
    digest = hashlib.sha256(payload.encode("ascii")).hexdigest()
    if digest != cert["sha256"]:
        return False, "sha256 mismatch"

    c, s, c2, s2 = coeff_intervals(t1, t2)
    fv = residual_interval(x, c, s, c2, s2)
    av = point_times_iv_vec(a_rows, fv)
    alpha = sqrt_upper(sum(e.mag() ** 2 for e in av))

    jm = jacobian_interval(x, c, s, c2, s2)
    aj = point_times_iv_mat(a_rows, jm)
    mm = []
    for i in range(18):
        row = []
        for j in range(18):
            e = (IV(Fraction(1)) - aj[i][j]) if i == j else (-aj[i][j])
            row.append(e.mag())
        mm.append(row)
    beta = sqrt_upper(norm2_sq_upper(mm))

    am = [[abs(a_rows[i][j]) for j in range(18)] for i in range(18)]
    norm_a = sqrt_upper(norm2_sq_upper(am))
    omega = 2 * norm_a

    if beta >= 1:
        return False, f"beta = {float(beta)} >= 1"
    if 4 * alpha * omega > (1 - beta) ** 2:
        return False, "Kantorovich inequality 4*alpha*omega <= (1-beta)^2 fails"
    return True, {"alpha": alpha, "beta": beta, "norm_a": norm_a,
                  "radius": (1 - beta) / (2 * omega)}


# --------------------------------------------- float cascade (sanity only)
def cascade_solution_float(t_float):
    u = 2.0 * math.atan(t_float)
    s, c = math.sin(u), math.cos(u)
    root = 2.0 * math.sqrt(2.0 * (1.0 + c))
    lo = (-1.0 - root) / (2.0 * (1.0 + c))
    hi = 0.0

    def h_of(m):
        eta = m * s
        zeta = -math.sqrt(max(0.0, 0.75 - eta * eta))
        rho2 = 1.0 / (8.0 * (1.0 + c)) + (m * m * (1.0 + c) + m) / 2.0
        return (0.375 - eta * eta / 2.0 - m / 2.0
                + zeta * math.sqrt(max(0.0, 1.0 - rho2)))

    if not (h_of(lo) > 0.0 > h_of(hi)):
        raise RuntimeError(f"IVT endpoints violated at t={t_float}")
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if h_of(mid) > 0:
            lo = mid
        else:
            hi = mid
    m = 0.5 * (lo + hi)
    eta = m * s
    zeta = -math.sqrt(max(0.0, 0.75 - eta * eta))
    ca, sa = math.cos(math.pi - u), math.sin(math.pi - u)
    gp = (-0.5, eta, zeta)
    g = (ca * gp[0] + sa * gp[1], -sa * gp[0] + ca * gp[1], gp[2])
    f = (-0.5, -eta, -zeta)
    c2m, s2m = math.cos(2 * u), math.sin(2 * u)
    b0 = f[0] + c2m * g[0] + s2m * g[1]
    b1 = f[1] - s2m * g[0] + c2m * g[1]
    p_x = (s * b0 + c * b1) / (2.0 * s)
    p_y = (-c * b0 + s * b1) / (2.0 * s)
    rho2 = 1.0 / (8.0 * (1.0 + c)) + (m * m * (1.0 + c) + m) / 2.0
    p = (p_x, p_y, math.sqrt(max(0.0, 1.0 - rho2)))
    q = (g[0] + p[0], g[1] + p[1], g[2] + p[2])
    den = 2.0 + 2.0 * c
    t_v = (0.5, s / den, math.sqrt(max(0.0, (1.0 + 2.0 * c) / den)))
    return [1.0, 0.0, 0.0, *t_v, *f, *g, *p, *q]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("results/json/route1_results_full.json"))
    args = parser.parse_args()
    with args.input.open(encoding="utf-8") as fh:
        data = json.load(fh)
    certs = data["intervals"]
    n_total = len(certs)
    print(f"loaded {n_total} certificates")

    failures = []
    for k, cert in enumerate(certs):
        ok, info = verify_certificate(cert)
        if not ok:
            failures.append((k, info))
        if (k + 1) % 250 == 0:
            print(f"  re-verified {k + 1}/{n_total}")
    if failures:
        for k, info in failures[:10]:
            print(f"  FAIL certificate {k}: {info}")
        print(f"FAILED: {len(failures)} certificates did not verify")
        sys.exit(1)
    print("all certificates re-verified from exact rational data")

    # coverage: descending chain tiling [1/10^7, 13/40]
    t_his = [Fraction(cc["t_hi"]) for cc in certs]
    t_los = [Fraction(cc["t_lo"]) for cc in certs]
    ok_cover = t_his[0] == Fraction(13, 40) and t_los[-1] == Fraction(1, 10**7)
    for k in range(n_total - 1):
        if t_los[k] != t_his[k + 1]:
            ok_cover = False
            print(f"  coverage gap between certificates {k} and {k + 1}")
            break
    if not ok_cover:
        print("FAILED: coverage is not a gap-free tiling of [1e-7, 13/40]")
        sys.exit(1)
    print("coverage verified: gap-free tiling of [1/10^7, 13/40]")

    # non-certifying sanity: cascade solution inside the certified ball
    worst_ratio = 0.0
    for k in range(0, n_total, 100):
        cert = certs[k]
        xh = [float(Fraction(v)) for v in cert["x_hat"]]
        for t_pt in (cert["t_lo_float"], cert["t_hi_float"]):
            sol = cascade_solution_float(t_pt)
            dist = math.sqrt(sum((a - b) ** 2 for a, b in zip(sol, xh)))
            worst_ratio = max(worst_ratio, dist / cert["radius"])
    print(f"sanity: cascade solutions lie within certified balls "
          f"(worst distance/radius = {worst_ratio:.3f})")
    if worst_ratio >= 1.0:
        print("FAILED: a cascade solution fell outside a certified ball")
        sys.exit(1)

    print("ALL CERTIFICATE CHECKS PASSED")


if __name__ == "__main__":
    main()
