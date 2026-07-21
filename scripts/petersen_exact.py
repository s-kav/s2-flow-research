"""Exact S2-flow on the Petersen graph from the icosidodecahedron.

Construction:
  1. Take the 30 vertices of the icosidodecahedron, normalized to unit length.
     Coordinates lie in the field Q(sqrt(5)).
  2. Find all unordered triples of these unit vectors that sum to zero exactly.
  3. The triples come in 10 antipodal pairs {T, -T}; the 30 points come in
     15 antipodal pairs {v, -v}. The incidence structure (triple-pairs as
     vertices, point-pairs as edges) is a cubic graph on 10 vertices; we verify
     it is isomorphic to the Petersen graph.
  4. Choose one representative triple from each antipodal pair such that every
     point-pair appears with opposite signs in its two chosen triples. Each
     point-pair then defines an oriented edge with an exact unit vector, and
     Kirchhoff's law holds at every vertex by the zero-sum property.
  5. Verify B X = 0 and ||x_e|| = 1 exactly in sympy.

All checks are exact symbolic computations; no floating point is trusted.
"""
from __future__ import annotations

import itertools

import networkx as nx
import sympy as sp

sqrt5 = sp.sqrt(5)
phi = (1 + sqrt5) / 2


def icosidodecahedron_unit_vertices() -> list[tuple[sp.Expr, sp.Expr, sp.Expr]]:
    """30 unit vectors: normalized icosidodecahedron vertices (circumradius phi)."""
    vertices = set()
    # Cyclic permutations of (0, 0, +-phi).
    base1 = [sp.Integer(0), sp.Integer(0), phi]
    for signs in itertools.product([1, -1], repeat=1):
        for shift in range(3):
            v = [base1[(k - shift) % 3] for k in range(3)]
            vertices.add(tuple(sp.simplify(signs[0] * c / phi) for c in v))
    # Cyclic permutations of (+-1/2, +-phi/2, +-phi^2/2).
    half = sp.Rational(1, 2)
    base2 = [half, phi / 2, phi**2 / 2]
    for s1, s2, s3 in itertools.product([1, -1], repeat=3):
        signed = [s1 * base2[0], s2 * base2[1], s3 * base2[2]]
        for shift in range(3):
            v = tuple(sp.simplify(signed[(k - shift) % 3] / phi) for k in range(3))
            vertices.add(v)
    return sorted(vertices, key=lambda t: [sp.srepr(c) for c in t])


def main() -> None:
    pts = icosidodecahedron_unit_vertices()
    assert len(pts) == 30, f"expected 30 vertices, got {len(pts)}"
    # Exact unit-norm check for all 30 points.
    for p in pts:
        assert sp.simplify(sum(c**2 for c in p) - 1) == 0
    print("30 exact unit vertices confirmed.")

    index = {p: i for i, p in enumerate(pts)}
    neg = {i: index[tuple(sp.simplify(-c) for c in pts[i])] for i in range(30)}

    # All zero-sum triples.
    triples = []
    for a, b, c in itertools.combinations(range(30), 3):
        s = [sp.simplify(pts[a][k] + pts[b][k] + pts[c][k]) for k in range(3)]
        if all(comp == 0 for comp in s):
            triples.append(frozenset((a, b, c)))
    print(f"zero-sum triples found: {len(triples)}")
    assert len(triples) == 20

    # Each point lies in exactly 2 triples.
    from collections import Counter

    cnt = Counter(i for t in triples for i in t)
    assert all(cnt[i] == 2 for i in range(30)), cnt
    print("each of the 30 points lies in exactly 2 zero-sum triples.")

    # Antipodal pairing of triples.
    tset = set(triples)
    for t in triples:
        assert frozenset(neg[i] for i in t) in tset
    triple_pairs = []
    seen = set()
    for t in triples:
        if t in seen:
            continue
        anti = frozenset(neg[i] for i in t)
        seen.add(t)
        seen.add(anti)
        triple_pairs.append((t, anti))
    assert len(triple_pairs) == 10
    point_pairs = []
    seen_p = set()
    for i in range(30):
        if i in seen_p:
            continue
        seen_p.add(i)
        seen_p.add(neg[i])
        point_pairs.append((i, neg[i]))
    assert len(point_pairs) == 15

    # Quotient incidence graph: vertices = triple pairs, edges = point pairs.
    pp_index = {}
    for j, (i, ni) in enumerate(point_pairs):
        pp_index[i] = j
        pp_index[ni] = j
    tp_index = {}
    for j, (t, anti) in enumerate(triple_pairs):
        tp_index[t] = j
        tp_index[anti] = j

    quotient = nx.MultiGraph()
    quotient.add_nodes_from(range(10))
    edge_of_point_pair = {}
    for j, (i, ni) in enumerate(point_pairs):
        touching = sorted({tp_index[t] for t in triples if i in t or ni in t})
        assert len(touching) == 2, touching
        quotient.add_edge(touching[0], touching[1], key=j)
        edge_of_point_pair[j] = (touching[0], touching[1])
    petersen = nx.petersen_graph()
    iso = nx.is_isomorphic(nx.Graph(quotient), petersen)
    print(f"quotient graph is simple cubic on 10 vertices, isomorphic to Petersen: {iso}")
    assert iso and quotient.number_of_edges() == 15

    # Choose one triple per pair so each point pair appears with opposite signs.
    # choice[j] in {0,1}: use triple_pairs[j][choice[j]].
    import itertools as it

    def representatives(choice):
        return [triple_pairs[j][choice[j]] for j in range(10)]

    solution = None
    for choice in it.product([0, 1], repeat=10):
        reps = representatives(choice)
        ok = True
        for j, (i, ni) in enumerate(point_pairs):
            u, w = edge_of_point_pair[j]
            in_u = i if i in reps[u] else (ni if ni in reps[u] else None)
            in_w = i if i in reps[w] else (ni if ni in reps[w] else None)
            assert in_u is not None and in_w is not None
            if in_u == in_w:  # same sign at both endpoints: not realizable
                ok = False
                break
        if ok:
            solution = choice
            break
    assert solution is not None, "no consistent antipodal selection exists"
    print(f"consistent sign selection found: {solution}")

    # Build the exact flow: edge j oriented from the endpoint using +v to the
    # endpoint using -v, with vector v (the representative at the tail).
    reps = representatives(solution)
    edges_oriented = []
    vectors = []
    for j, (i, ni) in enumerate(point_pairs):
        u, w = edge_of_point_pair[j]
        in_u = i if i in reps[u] else ni
        in_w = i if i in reps[w] else ni
        assert in_w == neg[in_u]
        edges_oriented.append((u, w))
        vectors.append(pts[in_u])  # contribution +v at u, -v at w

    # Exact verification: Kirchhoff at every quotient vertex and unit norms.
    for v in range(10):
        total = [sp.Integer(0)] * 3
        for (u, w), vec in zip(edges_oriented, vectors):
            if u == v:
                total = [sp.simplify(total[k] + vec[k]) for k in range(3)]
            if w == v:
                total = [sp.simplify(total[k] - vec[k]) for k in range(3)]
        assert all(t == 0 for t in total), (v, total)
    for vec in vectors:
        assert sp.simplify(sum(c**2 for c in vec) - 1) == 0
    print("EXACT VERIFICATION PASSED: B X = 0 and ||x_e|| = 1 hold symbolically.")

    print("\nOriented edges of the quotient (Petersen) graph and exact vectors:")
    for (u, w), vec in zip(edges_oriented, vectors):
        print(f"  {u} -> {w}: ({sp.nsimplify(vec[0])}, {sp.nsimplify(vec[1])}, {sp.nsimplify(vec[2])})")


if __name__ == "__main__":
    main()
