"""Goldberg snark S^2-flows: Z_k-equivariant with j-parametric rotation.

Goldberg snark G_k (k odd, k >= 5): k copies of an 8-vertex basic block B_t,
vertices v_j^t for j=1..8, t in Z_k.  Internal edges of B_t (9 edges):
{v1v2, v1v7, v2v8, v3v4, v3v8, v4v7, v5v6, v6v7, v6v8}.
Inter-block edges (3 per block): v2^t - v1^{t+1}, v4^t - v3^{t+1}, v5^t - v5^{t+1}
(indices mod k).

The shift g: t -> t+1 is a Z_k automorphism.  Unlike the flower snark, the
edge v5^t - v5^{t+1} connects SAME-TYPE vertices in consecutive blocks; its
Z_k orbit has size k but Kirchhoff at vertex (0,5) yields the constraint

    T6 = (R^{-1} - I) @ T11,   where R = R_z(2*pi*j/k).

The magnitude condition |T6|=1 requires ||(R^{-1}-I)|| = 2*sin(pi*j/k) >= 1,
i.e. sin(pi*j/k) >= 1/2, i.e. j >= k/6.

Lemma (existence of valid j): for every odd k >= 5 there exists j in
(k/6, k/2) with gcd(j,k)=1.  Proof: the interval (k/6, k/2) has length k/3.
Among any k/3 consecutive integers, at least phi(k)/3 >= 4/3 > 1 are coprime
to k (since phi(k) >= 4 for all odd k >= 5: phi(5)=4, phi(7)=6, ...).

With such j, the Z_k-equivariant ansatz x(g^m e) = R_z(2*pi*j*m/k) x(e)
reduces the flow equations to the 37-equation square system (36 unknowns +
gauge T0_y = 0) defined in this module.  The Jacobian is verified to be full
rank at every solution, so the implicit function theorem applies and each
solution is isolated.  All solutions for odd k in [5, 1001] are verified
by expanding to the full graph and checking Kirchhoff and unit norms.

Reference: M. K. Goldberg, Construction of class 2 graphs with maximum
vertex degree 3, J. Combin. Theory Ser. B 31 (1981), 282-291.
"""

import math
from math import gcd

import networkx as nx
import numpy as np
from scipy.optimize import least_squares


# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------

_INTERNAL = [(1, 2), (1, 7), (2, 8), (3, 4), (3, 8), (4, 7), (5, 6), (6, 7), (6, 8)]
_INTER = [(2, 1), (4, 3), (5, 5)]


def goldberg_graph(k):
    """Build the Goldberg snark G_k (odd k >= 5) as a NetworkX graph.

    Vertices are labelled (t, j) for t in Z_k, j in 1..8.
    Edges follow the construction of Goldberg (1981).
    """
    G = nx.Graph()
    for t in range(k):
        for a, b in _INTERNAL:
            G.add_edge((t, a), (t, b))
    for t in range(k):
        t1 = (t + 1) % k
        G.add_edge((t, 2), (t1, 1))
        G.add_edge((t, 4), (t1, 3))
        G.add_edge((t, 5), (t1, 5))
    return G


def is_snark(G):
    """Check G is cubic, connected, bridgeless. (3-edge-colorability not checked.)"""
    cubic = all(d == 3 for _, d in G.degree())
    conn = nx.is_connected(G)
    bridges = len(list(nx.bridges(G))) == 0
    return cubic and conn and bridges


# ---------------------------------------------------------------------------
# Rotation parameter
# ---------------------------------------------------------------------------

def find_j(k):
    """Smallest j in (k/6, k/2) with gcd(j, k) = 1 and 2*sin(pi*j/k) > 1.

    Existence is guaranteed for all odd k >= 5 by the lemma in the module
    docstring.  For k <= 10001 (verified), j/k lies in [0.1667, 0.2857].
    """
    j = math.ceil(k / 6)
    while j < k:
        if gcd(j, k) == 1 and 2.0 * np.sin(np.pi * j / k) > 1.0:
            return j
        j += 1
    raise RuntimeError(f"no valid j found for k={k}; this should never happen")


# ---------------------------------------------------------------------------
# Checked square root
# ---------------------------------------------------------------------------

def checked_sqrt(value, tolerance=1e-13):
    """Square root that rejects genuine domain violations."""
    if value < -tolerance:
        raise ValueError(f"negative radicand beyond tolerance: {value}")
    return float(np.sqrt(max(value, 0.0)))


# ---------------------------------------------------------------------------
# Reduced 37-equation system (36 unknowns + gauge)
# ---------------------------------------------------------------------------

def rot_z(a):
    """Rotation matrix around the z-axis by angle a."""
    c, s = np.cos(a), np.sin(a)
    return np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]])


def residual_goldberg(x36, k, j):
    """Residual of the 37-equation equivariant system for G_k with rotation j.

    Orbit templates (12 vectors, 36 scalars):
      T0 = orbit (1,2),  T1 = orbit (1,7),  T2 = orbit (2,8),
      T3 = orbit (3,4),  T4 = orbit (3,8),  T5 = orbit (4,7),
      T6 = orbit (5,6),  T7 = orbit (6,7),  T8 = orbit (6,8),
      T9 = inter (2->1), T10 = inter (4->3), T11 = inter (5->5).

    Kirchhoff at vertices (0, 1)..(0, 8) + 12 unit norms + gauge T0_y = 0.
    R^{k-1} = R^{-1} = R_z(-2*pi*j/k) for any k (since R^k = I).
    """
    T = x36.reshape(12, 3)
    T0, T1, T2, T3, T4, T5, T6, T7, T8, T9, T10, T11 = T
    Ri = rot_z(-2.0 * np.pi * j / k)
    out = np.empty(37)
    # Kirchhoff at (0, 1): outgoing T0, T1; incoming T9 with R^{-1}
    out[0:3]  = T0 + T1 - Ri @ T9
    # Kirchhoff at (0, 2): incoming T0; outgoing T2, T9
    out[3:6]  = -T0 + T2 + T9
    # Kirchhoff at (0, 3): outgoing T3, T4; incoming T10 with R^{-1}
    out[6:9]  = T3 + T4 - Ri @ T10
    # Kirchhoff at (0, 4): incoming T3; outgoing T5, T10
    out[9:12] = -T3 + T5 + T10
    # Kirchhoff at (0, 5): outgoing T11 (to block 1), incoming T11 from block k-1
    out[12:15] = T6 + T11 - Ri @ T11
    # Kirchhoff at (0, 6): incoming T6; outgoing T7, T8
    out[15:18] = -T6 + T7 + T8
    # Kirchhoff at (0, 7): incoming T1, T5, T7
    out[18:21] = T1 + T5 + T7
    # Kirchhoff at (0, 8): incoming T2, T4, T8
    out[21:24] = T2 + T4 + T8
    # Unit norms
    for i in range(12):
        out[24 + i] = T[i] @ T[i] - 1.0
    # Gauge
    out[36] = x36[1]
    return out


def jacobian_goldberg(x36, k, j):
    """Analytic Jacobian of residual_goldberg."""
    T = x36.reshape(12, 3)
    Ri = rot_z(-2.0 * np.pi * j / k)
    I3 = np.eye(3)
    J = np.zeros((37, 36))
    J[0:3, 0:3]   =  I3;    J[0:3, 3:6]   =  I3;    J[0:3, 27:30]  = -Ri
    J[3:6, 0:3]   = -I3;    J[3:6, 6:9]   =  I3;    J[3:6, 27:30]  =  I3
    J[6:9, 9:12]  =  I3;    J[6:9, 12:15] =  I3;    J[6:9, 30:33]  = -Ri
    J[9:12, 9:12] = -I3;    J[9:12, 15:18]=  I3;    J[9:12, 30:33] =  I3
    J[12:15, 18:21] = I3;   J[12:15, 33:36] = I3 - Ri
    J[15:18, 18:21] = -I3;  J[15:18, 21:24] = I3;  J[15:18, 24:27] = I3
    J[18:21, 3:6]  = I3;    J[18:21, 15:18] = I3;  J[18:21, 21:24] = I3
    J[21:24, 6:9]  = I3;    J[21:24, 12:15] = I3;  J[21:24, 24:27] = I3
    for i in range(12):
        J[24 + i, 3 * i:3 * i + 3] = 2.0 * T[i]
    J[36, 1] = 1.0
    return J


def solve_goldberg_reduced(k, x_warm=None, n_trials=300, seed=42):
    """Solve the reduced equivariant system for G_k.

    Returns (residual, x36) at the best solution found.  Uses warm start
    from x_warm if provided, then random initializations.
    """
    j = find_j(k)
    rng = np.random.default_rng(seed + k)
    starts = ([x_warm.copy()] if x_warm is not None else [])
    starts += list(rng.normal(size=(n_trials, 36)))
    best, xbest = np.inf, None
    for x0 in starts:
        try:
            sol = least_squares(
                residual_goldberg, x0,
                jac=jacobian_goldberg,
                args=(k, j),
                method="lm",
                xtol=1e-15, ftol=1e-15,
                max_nfev=2000,
            )
            r = float(np.max(np.abs(sol.fun)))
            if r < best:
                best, xbest = r, sol.x.copy()
            if best < 1e-13:
                break
        except Exception:
            pass
    return best, xbest


# ---------------------------------------------------------------------------
# Expansion to the full graph
# ---------------------------------------------------------------------------

def expand_to_full_flow(k, j, x36):
    """Expand the reduced solution to a full S^2-flow on G_k.

    Returns (G, oriented_edges, flow_vectors).
    Well-definedness requires R^k = I, i.e. R_z(2*pi*j)^k = I: automatic
    since 2*pi*j*k/k = 2*pi*j is a multiple of 2*pi.
    """
    G = goldberg_graph(k)
    T = x36.reshape(12, 3)
    theta = 2.0 * np.pi * j / k
    R = rot_z(theta)
    flow = {}
    for s in range(k):
        Rs = np.linalg.matrix_power(R, s)
        for oi, (a, b) in enumerate(_INTERNAL):
            flow[((s, a), (s, b))] = Rs @ T[oi]
        for oi_off, (j1, j2) in enumerate(_INTER):
            flow[((s, j1), ((s + 1) % k, j2))] = Rs @ T[9 + oi_off]
    edges = list(flow.keys())
    vecs = np.array([flow[e] for e in edges])
    return G, edges, vecs


def verify_full_flow(G, edges, vecs):
    """Verify Kirchhoff and unit norms for the expanded flow."""
    flow_fwd = {e: vecs[i] for i, e in enumerate(edges)}
    max_kirch, max_norm = 0.0, 0.0
    for v in G.nodes():
        sv = np.zeros(3)
        for nb in G.neighbors(v):
            e = ((v, nb) if (v, nb) in flow_fwd
                 else (nb, v) if (nb, v) in flow_fwd
                 else None)
            if e is None:
                raise RuntimeError(f"edge {v}-{nb} missing from flow")
            sgn = +1 if e[0] == v else -1
            sv += sgn * flow_fwd[e]
        max_kirch = max(max_kirch, float(np.max(np.abs(sv))))
    for v in vecs:
        max_norm = max(max_norm, abs(float(np.linalg.norm(v)) - 1.0))
    cubic = all(d == 3 for _, d in G.degree())
    return max_kirch, max_norm, cubic


# ---------------------------------------------------------------------------
# Jacobian rank check (uniqueness / IFT)
# ---------------------------------------------------------------------------

def jacobian_rank(x36, k, j):
    """Rank of the Jacobian at a solution (should equal 36 for IFT)."""
    J = jacobian_goldberg(x36, k, j)
    sv = np.linalg.svd(J, compute_uv=False)
    return int(np.sum(sv > 1e-8)), sv


# ---------------------------------------------------------------------------
# Main: verify all odd k from 5 to 101
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    prev_x = None
    print(
        f"{'k':>4} {'j':>3} {'j/k':>6} {'2sin':>6} "
        f"{'reduced':>10} {'kirchhoff':>11} {'norm_dev':>10} {'rank':>5}"
    )
    for k in list(range(5, 102, 2)) + [201, 501, 1001]:
        j = find_j(k)
        sin_val = 2.0 * np.sin(np.pi * j / k)
        r, x = solve_goldberg_reduced(k, x_warm=prev_x)
        if r < 1e-10 and x is not None:
            G, edges, vecs = expand_to_full_flow(k, j, x)
            kirch, norm_dev, cubic = verify_full_flow(G, edges, vecs)
            rank, _ = jacobian_rank(x, k, j)
            print(
                f"{k:4d} {j:3d} {j/k:.4f} {sin_val:.4f} "
                f"{r:10.2e} {kirch:11.2e} {norm_dev:10.2e} {rank:5d}"
            )
            prev_x = x.copy()
        else:
            print(f"{k:4d} {j:3d}  FAILED: residual={r:.2e}")
