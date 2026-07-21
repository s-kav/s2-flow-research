"""The reduced equivariant system for flower snarks and its validation.

Canonical J_n: hubs c_i, outer cycle t_i (i in Z_n), strand 2n-cycle w_j
(j in Z_2n), edges oriented as h_i = (c_i -> t_i), T_i = (t_i -> t_{i+1}),
F_j = (c_{j mod n} -> w_j), E_j = (w_j -> w_{j+1}).  The two-block shift
g: indices +2 is an automorphism of order n (n odd) acting freely on the
four edge families, splitting the strand families into even/odd orbits.

Z_n-equivariant ansatz with R = R_z(theta), theta = 2*pi/n (branch k = 1):
templates H = x(h_0), T = x(T_0), F = x(F_0), G = x(F_1), P = x(E_0),
Q = x(E_1); all other values are R-powers of these.  Kirchhoff at the four
vertex-orbit representatives c_0, t_0, w_0, w_1 gives, with
A := R^((n-1)/2) = R_z(pi - theta/2):

    E1:  H + F + A G           = 0        (hub c_0)
    E2:  T - H - A T           = 0        (outer t_0)
    E3:  P - F - R^{-1} Q      = 0        (strand w_0)
    E4:  Q - G - P             = 0        (strand w_1)

plus the six unit norms.  The z-component of E2 is the exact linear
combination -(E1 + E3 + E4)_z, so the regular square system consists of
E1, E2_xy, E3, E4, the six norms and one gauge equation H_y = 0
(18 equations, 18 unknowns), parametrised smoothly by u := theta/2 through
R = R_z(2u) and A = R_z(pi - u).

This module provides: the square parametric residual and Jacobian; the
expansion of a template solution to a full flow on J_n with verification;
and the closed-form cascade that reduces the whole system to a single
scalar equation on a circle (see stage2_scalar.py for its analysis):

    gauge + |H| = 1, H_z = 0        =>  H = (1, 0, 0)
    E2 + |T| = 1                    =>  T explicit, T_z^2 = (1+2cos u)/(2+2cos u)
    G' := A G = (-1/2, eta, zeta),  eta^2 + zeta^2 = 3/4   (from |F|=|G|=1)
    F = (-1/2, -eta, -zeta)
    b := F + R^{-1} G,  b_z = 0
    P_xy = rot(u - pi/2) b_xy / (2 sin u),   P_z = eps * sqrt(1 - |P_xy|^2)
    Q = G + P
    remaining equation:  <G, P> = -1/2       (equivalent to |Q| = 1).
"""

import numpy as np
import networkx as nx


def rot_z(a):
    return np.array(
        [
            [np.cos(a), -np.sin(a), 0.0],
            [np.sin(a), np.cos(a), 0.0],
            [0.0, 0.0, 1.0],
        ]
    )


def rot2(a):
    return np.array([[np.cos(a), -np.sin(a)], [np.sin(a), np.cos(a)]])


def residual_square(x18, u):
    """Square 18x18 residual: E1, E2_xy, E3, E4, six norms, gauge H_y = 0."""
    h, t, f, g, p, q = x18.reshape(6, 3)
    r_inv = rot_z(-2.0 * u)
    a_mat = rot_z(np.pi - u)
    e1 = h + f + a_mat @ g
    e2 = t - h - a_mat @ t
    e3 = p - f - r_inv @ q
    e4 = q - g - p
    norms = np.array(
        [v @ v - 1.0 for v in (h, t, f, g, p, q)]
    )
    return np.concatenate([e1, e2[:2], e3, e4, norms, [h[1]]])


def jacobian_square(x18, u):
    jac = np.zeros((18, 18))
    eye = np.eye(3)
    r_inv = rot_z(-2.0 * u)
    a_mat = rot_z(np.pi - u)
    # variable blocks: H:0-2, T:3-5, F:6-8, G:9-11, P:12-14, Q:15-17
    jac[0:3, 0:3] = eye
    jac[0:3, 6:9] = eye
    jac[0:3, 9:12] = a_mat
    jac[3:5, 3:6] = (eye - a_mat)[0:2, :]
    jac[3:5, 0:3] = -eye[0:2, :]
    jac[5:8, 12:15] = eye
    jac[5:8, 6:9] = -eye
    jac[5:8, 15:18] = -r_inv
    jac[8:11, 15:18] = eye
    jac[8:11, 9:12] = -eye
    jac[8:11, 12:15] = -eye
    x = x18.reshape(6, 3)
    for i in range(6):
        jac[11 + i, 3 * i : 3 * i + 3] = 2.0 * x[i]
    jac[17, 1] = 1.0
    return jac


def expand_to_full_flow(x18, n):
    """Expand a template solution at u = pi/n to the full flow on J_n.

    Returns (graph, oriented edge list, X) with the canonical orientations.
    """
    theta = 2.0 * np.pi / n
    r_mat = rot_z(theta)
    powers = [np.linalg.matrix_power(r_mat, m) for m in range(n)]
    h, t, f, g, p, q = x18.reshape(6, 3)
    mu = [((n + 1) // 2 * i) % n for i in range(n)]

    graph = nx.Graph()
    edges = []
    vecs = []

    def c(i):
        return ("c", i % n)

    def tt(i):
        return ("t", i % n)

    def w(j):
        return ("w", j % (2 * n))

    for i in range(n):
        edges.append((c(i), tt(i)))
        vecs.append(powers[mu[i]] @ h)
        edges.append((tt(i), tt(i + 1)))
        vecs.append(powers[mu[i]] @ t)
    for j in range(2 * n):
        m, odd = divmod(j, 2)
        edges.append((c(j % n), w(j)))
        vecs.append(powers[m] @ (g if odd else f))
        edges.append((w(j), w(j + 1)))
        vecs.append(powers[m] @ (q if odd else p))
    graph.add_edges_from(edges)
    x = np.array(vecs)
    return graph, edges, x


def verify_full_flow(graph, edges, x):
    idx = {v: i for i, v in enumerate(graph.nodes())}
    b = np.zeros((graph.number_of_nodes(), len(edges)))
    for k, (usrc, vdst) in enumerate(edges):
        b[idx[usrc], k] = 1.0
        b[idx[vdst], k] = -1.0
    kirch = float(np.max(np.abs(b @ x)))
    norm = float(np.max(np.abs(np.linalg.norm(x, axis=1) - 1.0)))
    cubic = all(d == 3 for _, d in graph.degree())
    return kirch, norm, cubic


def scalar_data(psi, u, eps):
    """The one-equation cascade: returns (h_value, rho) at circle angle psi.

    G' = (-1/2, eta, zeta) with (eta, zeta) = (sqrt(3)/2)(cos psi, sin psi);
    h_value = <G, P> + 1/2 must vanish; rho = |P_xy| must be <= 1.
    """
    s3 = np.sqrt(3.0) / 2.0
    eta, zeta = s3 * np.cos(psi), s3 * np.sin(psi)
    gp = np.array([-0.5, eta, zeta])
    a_inv = rot_z(-(np.pi - u))
    g_vec = a_inv @ gp
    f_vec = np.array([-0.5, -eta, -zeta])
    r_inv = rot_z(-2.0 * u)
    b_vec = f_vec + r_inv @ g_vec
    rot_m = np.array([[np.sin(u), np.cos(u)], [-np.cos(u), np.sin(u)]])
    p_xy = rot_m @ b_vec[:2] / (2.0 * np.sin(u))
    rho = float(np.hypot(*p_xy))
    if rho > 1.0:
        return None, rho
    p_vec = np.array([p_xy[0], p_xy[1], eps * checked_sqrt(1.0 - rho * rho, 1e-9)])
    return float(g_vec @ p_vec + 0.5), rho


def solve_scalar(u, eps, n_grid=2000):
    """Root of the scalar equation on the circle by sign change + bisection."""
    psis = np.linspace(-np.pi, np.pi, n_grid, endpoint=False)
    vals = []
    for psi in psis:
        v, rho = scalar_data(psi, u, eps)
        vals.append(v)
    roots = []
    for i in range(n_grid):
        v1, v2 = vals[i], vals[(i + 1) % n_grid]
        if v1 is None or v2 is None or v1 * v2 > 0:
            continue
        lo, hi = psis[i], psis[i] + (psis[1] - psis[0])
        for _ in range(80):
            mid = 0.5 * (lo + hi)
            vm, _ = scalar_data(mid, u, eps)
            if vm is None:
                break
            if v1 * vm <= 0:
                hi = mid
            else:
                lo, v1 = mid, vm
        roots.append(0.5 * (lo + hi))
    return roots


def checked_sqrt(value, tolerance=1e-13):
    """Square root that rejects genuine domain violations.

    Boundary evaluations (e.g. rho = 1 exactly at m = m_-) legitimately
    produce radicands that are zero up to rounding; values below -tolerance
    indicate a formula error or an out-of-domain call and raise instead of
    being silently clipped.
    """
    if value < -tolerance:
        raise ValueError(f"negative radicand beyond tolerance: {value}")
    return float(np.sqrt(max(value, 0.0)))


def m_boundary(u):
    """Roots m_- < m_+ of rho(m) = 1: the admissible interval in m = eta/sin u.

    rho^2(m) = 1/(8(1+cos u)) + (m^2 (1+cos u) + m)/2 and
    rho^2 - 1 = ((1+cos u)/2) (m - m_-)(m - m_+).
    """
    c = np.cos(u)
    root = 2.0 * np.sqrt(2.0 * (1.0 + c))
    return (-1.0 - root) / (2.0 * (1.0 + c)), (-1.0 + root) / (2.0 * (1.0 + c))


def h_of_m(m, u, eps=+1.0):
    """The scalar function on the branch zeta = -sqrt(3/4 - eta^2), eta = m sin u.

    h(m) = 3/8 - eta^2/2 - m/2 + eps * zeta * sqrt(1 - rho^2(m)).
    Defined for m in [m_-, m_+]; h(m_-) > 0 and h(0) < 0 for u in (0, pi/5].
    This evaluation involves no division by sin u, so it is uniformly
    well-conditioned as u -> 0 (unlike template reconstruction; see
    templates_from_m).
    """
    s, c = np.sin(u), np.cos(u)
    eta = m * s
    zeta = -checked_sqrt(0.75 - eta * eta)
    rho2 = 1.0 / (8.0 * (1.0 + c)) + (m * m * (1.0 + c) + m) / 2.0
    return 0.375 - eta * eta / 2.0 - m / 2.0 + eps * zeta * checked_sqrt(
        1.0 - rho2
    )


def h_prime_of_m(m, u):
    """d h / d m on the branch eps = +1, zeta < 0, for m in (m_-, 0).

    Decomposition used in the uniqueness proof (Lemma 4):
        h'(m) = -m s^2 - 1/2 + zeta' w + zeta w',
        zeta' = m s^2 / |zeta|,   w' = -(m(1+c) + 1/2) / (2w).
    """
    s, c = np.sin(u), np.cos(u)
    eta2 = m * m * s * s
    zeta = -checked_sqrt(0.75 - eta2)
    rho2 = 1.0 / (8.0 * (1.0 + c)) + (m * m * (1.0 + c) + m) / 2.0
    w = checked_sqrt(1.0 - rho2)
    dzeta = m * s * s / (-zeta)
    dw = -(m * (1.0 + c) + 0.5) / (2.0 * w)
    return -m * s * s - 0.5 + dzeta * w + zeta * dw


def solve_scalar_m(u, eps=+1.0, iters=200):
    """Root of h on [m_-, 0] by bisection.

    The bisection itself is uniformly well-posed down to u -> 0: h contains
    no division by sin u, and by Lemma 4 (dh/dm < 0 on (m_-, 0)) the root is
    unique, so the returned m approximates m*(u) to the bisection tolerance
    for every u in (0, pi/5].
    """
    m_lo, _ = m_boundary(u)
    lo, hi = m_lo, 0.0
    v_lo, v_hi = h_of_m(lo, u, eps), h_of_m(hi, u, eps)
    if not (v_lo > 0 > v_hi):
        raise RuntimeError(
            f"IVT endpoints violated at u={u!r}: h(m_-)={v_lo!r}, h(0)={v_hi!r}"
        )
    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        vm = h_of_m(mid, u, eps)
        if vm > 0:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def templates_from_scalar(psi, u, eps):
    """Rebuild the full 18-vector template solution from a scalar root.

    Float64 caveat: b_xy is O(u) and is divided by 2 sin u, so the
    evaluation-path condition number grows like n = pi/u; for very large n
    use higher-precision arithmetic (see residual_square_mp in the verifier).
    """
    s3 = np.sqrt(3.0) / 2.0
    eta, zeta = s3 * np.cos(psi), s3 * np.sin(psi)
    gp = np.array([-0.5, eta, zeta])
    a_inv = rot_z(-(np.pi - u))
    g_vec = a_inv @ gp
    f_vec = np.array([-0.5, -eta, -zeta])
    r_inv = rot_z(-2.0 * u)
    b_vec = f_vec + r_inv @ g_vec
    rot_m = np.array([[np.sin(u), np.cos(u)], [-np.cos(u), np.sin(u)]])
    p_xy = rot_m @ b_vec[:2] / (2.0 * np.sin(u))
    p_vec = np.array(
        [p_xy[0], p_xy[1], eps * checked_sqrt(1.0 - p_xy @ p_xy, 1e-9)]
    )
    q_vec = g_vec + p_vec
    h_vec = np.array([1.0, 0.0, 0.0])
    cu = np.cos(u)
    tz2 = (1.0 + 2.0 * cu) / (2.0 + 2.0 * cu)
    txy_den = 2.0 + 2.0 * cu
    t_vec = np.array(
        [(1.0 + cu) / txy_den, np.sin(u) / txy_den, checked_sqrt(tz2)]
    )
    return np.concatenate([h_vec, t_vec, f_vec, g_vec, p_vec, q_vec])


def templates_from_m(m, u, eps=+1.0):
    """Rebuild the 18-vector template solution directly from the m-root.

    eta = m sin u, zeta = -sqrt(3/4 - eta^2); avoids the psi round-trip.
    Float64 caveat: unlike the m-bisection, this reconstruction divides the
    O(u) vector b_xy by 2 sin u, so its evaluation-path condition number
    grows like n = pi/u; residuals of order n * machine-eps are expected and
    are evaluation noise, not solution error (confirmed in 60-digit
    arithmetic by the verifier). Use higher precision for very large n.
    """
    s, c = np.sin(u), np.cos(u)
    eta = m * s
    zeta = -checked_sqrt(0.75 - eta * eta)
    gp = np.array([-0.5, eta, zeta])
    g_vec = rot_z(-(np.pi - u)) @ gp
    f_vec = np.array([-0.5, -eta, -zeta])
    b_vec = f_vec + rot_z(-2.0 * u) @ g_vec
    rot_m = np.array([[s, c], [-c, s]])
    p_xy = rot_m @ b_vec[:2] / (2.0 * s)
    rho2 = 1.0 / (8.0 * (1.0 + c)) + (m * m * (1.0 + c) + m) / 2.0
    p_vec = np.array([p_xy[0], p_xy[1], eps * checked_sqrt(1.0 - rho2)])
    q_vec = g_vec + p_vec
    h_vec = np.array([1.0, 0.0, 0.0])
    den = 2.0 + 2.0 * c
    t_vec = np.array(
        [0.5, s / den, checked_sqrt((1.0 + 2.0 * c) / den)]
    )
    return np.concatenate([h_vec, t_vec, f_vec, g_vec, p_vec, q_vec])


if __name__ == "__main__":
    from scipy.optimize import least_squares

    rng = np.random.default_rng(3)
    print("A. square 18x18 system: solve by LM, expand, verify on the graph")
    for n in (7, 13, 41, 101, 1001):
        u = np.pi / n
        best, xbest = np.inf, None
        for _ in range(60):
            sol = least_squares(
                residual_square,
                rng.normal(size=18),
                jac=jacobian_square,
                args=(u,),
                method="lm",
                xtol=1e-15,
                ftol=1e-15,
                max_nfev=800,
            )
            r = float(np.max(np.abs(sol.fun)))
            if r < best:
                best, xbest = r, sol.x.copy()
            if best < 1e-13:
                break
        graph, edges, x = expand_to_full_flow(xbest, n)
        kirch, norm, cubic = verify_full_flow(graph, edges, x)
        cond = np.linalg.cond(jacobian_square(xbest, u))
        print(
            f"  n={n:5d}: reduced residual {best:.2e}, expanded kirchhoff "
            f"{kirch:.2e}, norms {norm:.2e}, cubic={cubic}, cond(J)={cond:.1e}"
        )

    print("B. scalar reduction: roots reproduce solutions of the square system")
    for n in (7, 13, 41, 1001):
        u = np.pi / n
        for eps in (+1.0, -1.0):
            roots = solve_scalar(u, eps)
            for psi in roots[:1]:
                x18 = templates_from_scalar(psi, u, eps)
                r = float(np.max(np.abs(residual_square(x18, u))))
                # gauge row may differ; drop it in the check
                r_nogauge = float(np.max(np.abs(residual_square(x18, u)[:17])))
                print(
                    f"  n={n:5d} eps={int(eps):+d}: {len(roots)} roots; at "
                    f"psi={psi:+.4f} square residual (no gauge) {r_nogauge:.2e}"
                )
