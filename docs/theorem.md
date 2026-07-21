# The S²-Flow Conjecture Holds for All Goldberg Snarks

## Main theorem

For every odd integer `k >= 5`, the Goldberg snark `G_k` admits an `S²`-flow.

## Exact Goldberg construction

For each block index `t` modulo `k`, the block has vertices `v_1^t,...,v_8^t` and internal edges

```text
v1v2, v1v7, v2v8, v3v4, v3v8, v4v7, v5v6, v6v7, v6v8.
```

Consecutive blocks are joined by

```text
v2^t v1^(t+1), v4^t v3^(t+1), v5^t v5^(t+1).
```

The cyclic block shift has exactly twelve free edge orbits, each of size `k`.

## Representation choice

Let

```text
ell = (k-1)/2,
phi = 2*pi*ell/k = pi - pi/k,
x = cot(phi/2) = tan(pi/(2k)).
```

Represent the block shift by the rotation `R_z(phi)`. Since `R_z(phi)^k = I`, the template expansion closes around the block cycle.

The fundamental choice `phi = 2*pi/k` is impossible for `k >= 7`: the vertex-5 channel forces

```text
||(R^-1-I)r|| = 1,
```

but the left-hand side is at most `2*sin(pi/k) < 1`.

## Scalar reduction

For a scalar `y`, define

```text
z_y = sqrt(1-y^2(1+x^2)),
d_y = sqrt(3-4y^2),
lambda_y = 1-y^2,
A_y = (d_y z_y-yx)/(2 lambda_y),
D_y = (z_y+d_y yx)/(2 lambda_y),
B_y = A_y+yx,
C_y = D_y-z_y.
```

Set `t = 1/2-s` and

```text
H(s,x) = (B_t-B_s)^2 + (C_s-C_t)^2 - 3/4.
```

The exact interval certificate proves on

```text
2/3 <= s <= 21/25,
0 <= x <= 13/40
```

that

```text
H(2/3,x) < 0,
H(21/25,x) > 0,
dH/ds > 0.
```

Hence there is a unique root `s=s(x)`.

## Twelve templates

Using that root, define

```text
a = ( A_s,       0,  D_s)
b = (-B_s,       s, -C_s)
c = ( B_s,       s,  C_s)
d = ( A_t,       0,  D_t)
e = (-B_t,       t, -C_t)
f = ( B_t,       t,  C_t)
g = (   0,      -1,    0)
h = (B_s-B_t, -1/2, C_s-C_t)
i = (B_t-B_s, -1/2, C_t-C_s)
p = (-sx,       -s,  z_s)
q = (-tx,       -t,  z_t)
r = ( x/2,     1/2, sqrt(3-x^2)/2).
```

Every template is a unit vector. The eight representative Kirchhoff equations follow by direct substitution. Assigning `R_z(phi)^t` times each template to its edge in block shift `t` yields the full `S²`-flow on `G_k`.
