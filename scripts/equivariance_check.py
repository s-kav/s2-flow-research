"""Equivariance analysis of the stored flower snark S2-flow certificates.

For each flower snark J_n (n = 5, 7, 9, 11, 13) this script:

1. Builds a canonical labelled copy of J_n and its one-block rotation sigma,
   which is a graph automorphism of order 2n (the strand vertices form a
   single 2n-cycle, so one block shift has order 2n; its n-th power is the
   Moebius half-turn swapping the two strands).
2. Transports sigma to the certificate's labelling via a VF2 isomorphism,
   obtaining an automorphism tau of the stored graph, and lifts tau to the
   stored oriented edge list with orientation signs s_e in {+1, -1}.
3. Solves the orthogonal Procrustes problem
       min_{R in O(3)}  sum_e || s_e * x_{tau(e)} - R x_e ||^2
   by SVD, preferring the det(R) = +1 branch, and reports the equivariance
   residual max_e || s_e * x_{tau(e)} - R x_e ||.
4. Extracts the rotation angle of R and compares it with odd multiples of
   pi/n (the angle predicted by the equivariant ansatz).
5. Averages the flow over the full cyclic group <tau> of order 2n,
       xbar_e = (1/2n) * sum_k (R^k)^T * s^(k)_e * x_{tau^k(e)},
   and reports how far the averaged flow is from unit norms (Kirchhoff is
   preserved exactly by averaging because tau is an automorphism and the
   constraint is linear), plus the distance between the averaged flow and
   the original certificate.

A small max equivariance residual and a small norm deficit of the averaged
flow together mean the stored numerical certificates already lie
(numerically) on the equivariant ansatz, supporting the Stage 2 programme.

Output: printed table plus equivariance_results.json.
"""

import json
import glob
import os

import numpy as np
import networkx as nx
from networkx.algorithms.isomorphism import GraphMatcher

CERT_DIR = "s2-flow-research/results/massive_run/certificates"
FLOWER_NS = [5, 7, 9, 11, 13]


def canonical_flower(n):
    """Canonical flower snark J_n with its one-block rotation automorphism.

    Vertices: ('c', i) hubs, ('t', i) outer cycle, ('w', j) the single
    2n-cycle formed by the two strands, where w_j = u_j for j < n and
    w_j = v_{j-n} for j >= n.  Hub ('c', i) is adjacent to ('t', i),
    ('w', i) and ('w', n + i).
    """
    g = nx.Graph()
    for i in range(n):
        g.add_edge(("c", i), ("t", i))
        g.add_edge(("c", i), ("w", i))
        g.add_edge(("c", i), ("w", n + i))
        g.add_edge(("t", i), ("t", (i + 1) % n))
    for j in range(2 * n):
        g.add_edge(("w", j), ("w", (j + 1) % (2 * n)))
    sigma = {}
    for i in range(n):
        sigma[("c", i)] = ("c", (i + 1) % n)
        sigma[("t", i)] = ("t", (i + 1) % n)
    for j in range(2 * n):
        sigma[("w", j)] = ("w", (j + 1) % (2 * n))
    return g, sigma


def mapping_order(perm):
    """Order of a permutation given as a dict."""
    order = 1
    current = dict(perm)
    identity = {k: k for k in perm}
    while current != identity:
        current = {k: perm[current[k]] for k in perm}
        order += 1
        if order > 10000:
            raise RuntimeError("runaway permutation order")
    return order


def edge_action(edges, tau):
    """Lift a vertex automorphism tau to the oriented edge list.

    Returns (pi, s) with pi a permutation of edge indices and s in {+1,-1}
    such that the image of oriented edge i is s[i] times oriented edge pi[i].
    """
    index = {e: k for k, e in enumerate(edges)}
    m = len(edges)
    pi = np.empty(m, dtype=int)
    s = np.empty(m, dtype=int)
    for k, (u, v) in enumerate(edges):
        img = (tau[u], tau[v])
        if img in index:
            pi[k], s[k] = index[img], 1
        else:
            rev = (img[1], img[0])
            pi[k], s[k] = index[rev], -1
    return pi, s


def procrustes_rotation(x_src, x_dst):
    """Best R (preferring det +1) minimising sum ||x_dst - R x_src||^2."""
    m3 = x_dst.T @ x_src
    u, _, vt = np.linalg.svd(m3)
    r_free = u @ vt
    if np.linalg.det(r_free) < 0:
        d = np.diag([1.0, 1.0, -1.0])
        r_rot = u @ d @ vt
    else:
        r_rot = r_free
    return r_rot, float(np.linalg.det(r_free))


def analyse(n):
    hits = [
        f
        for f in glob.glob(f"{CERT_DIR}/*.npz")
        if os.path.basename(f).split("_", 1)[1].rsplit(".", 1)[0] == f"flower_J{n}"
    ]
    assert len(hits) == 1, hits
    data = np.load(hits[0], allow_pickle=True)
    g = nx.from_graph6_bytes(str(data["graph6"][0]).encode("ascii"))
    edges = [tuple(int(a) for a in e) for e in data["edges"].tolist()]
    x = np.asarray(data["X"], dtype=float)
    m = len(edges)

    canon, sigma = canonical_flower(n)
    gm = GraphMatcher(canon, g)
    assert gm.is_isomorphic()
    phi = gm.mapping
    tau = {phi[v]: phi[sigma[v]] for v in canon.nodes()}
    order = mapping_order(tau)

    pi, s = edge_action(edges, tau)
    x_img = s[:, None] * x[pi]

    r_rot, det_free = procrustes_rotation(x, x_img)
    resid = np.linalg.norm(x_img - x @ r_rot.T, axis=1)
    angle = float(np.arccos(np.clip((np.trace(r_rot) - 1.0) / 2.0, -1.0, 1.0)))
    angle_units = angle * n / np.pi  # predicted: an odd integer

    # Average over the cyclic group <tau> of order 2n.
    xbar = np.zeros_like(x)
    cur_pi = np.arange(m)
    cur_s = np.ones(m)
    r_pow = np.eye(3)
    for _ in range(order):
        xbar += cur_s[:, None] * x[cur_pi] @ r_pow  # (R^k)^T x_{tau^k(e)} rowwise
        cur_s = cur_s * s[cur_pi]
        cur_pi = pi[cur_pi]
        r_pow = r_pow @ r_rot.T
    xbar /= order
    assert np.array_equal(cur_pi, np.arange(m)), "group order mismatch"

    b = np.zeros((g.number_of_nodes(), m))
    for k, (u, v) in enumerate(edges):
        b[u, k] = 1.0
        b[v, k] = -1.0

    result = {
        "graph": f"flower_J{n}",
        "n": n,
        "vertices": g.number_of_nodes(),
        "edges": m,
        "automorphism_order": order,
        "det_unconstrained_procrustes": det_free,
        "rotation_angle_over_pi_over_n": angle_units,
        "nearest_odd_multiple": int(round(angle_units))
        if int(round(angle_units)) % 2 == 1
        else int(round(angle_units)),
        "equivariance_residual_max": float(resid.max()),
        "equivariance_residual_rms": float(np.sqrt(np.mean(resid**2))),
        "averaged_norm_deficit_max": float(
            np.max(np.abs(np.linalg.norm(xbar, axis=1) - 1.0))
        ),
        "averaged_kirchhoff_residual": float(np.max(np.abs(b @ xbar))),
        "distance_original_to_averaged_max": float(
            np.max(np.linalg.norm(x - xbar, axis=1))
        ),
    }
    return result


def main():
    results = [analyse(n) for n in FLOWER_NS]
    header = (
        f"{'graph':<12}{'order':>6}{'det':>6}{'angle/(pi/n)':>14}"
        f"{'equiv max':>12}{'equiv rms':>12}{'avg norm':>12}"
        f"{'avg kirch':>12}{'dist max':>12}"
    )
    print(header)
    for r in results:
        print(
            f"{r['graph']:<12}{r['automorphism_order']:>6}"
            f"{r['det_unconstrained_procrustes']:>6.2f}"
            f"{r['rotation_angle_over_pi_over_n']:>14.6f}"
            f"{r['equivariance_residual_max']:>12.3e}"
            f"{r['equivariance_residual_rms']:>12.3e}"
            f"{r['averaged_norm_deficit_max']:>12.3e}"
            f"{r['averaged_kirchhoff_residual']:>12.3e}"
            f"{r['distance_original_to_averaged_max']:>12.3e}"
        )
    with open("equivariance_results.json", "w") as f:
        json.dump(results, f, indent=1)
    print("saved equivariance_results.json")


if __name__ == "__main__":
    main()
