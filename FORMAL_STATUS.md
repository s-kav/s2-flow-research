# Formal status

## Proved analytically

- The strict one-block order-2n equivariant ansatz with one orthogonal matrix
  is impossible for every odd flower parameter n >= 5.

## Proved by exact computer-assisted certificates

- J_n admits an S²-flow for every odd n with 5 <= n <= 41.
- Each certificate is verified by exact dyadic/integer Newton-Kantorovich
  inequalities. The verification radius is 1e-8.

## Validated numerical diagnostics

- All 38 generators of the relevant cyclic groups were tested on the stored
  J5-J13 generic certificates.
- The generic certificates are far from equivariant.
- The pure Z_n, k=1 numerical branch solves to floating-point precision for
  every odd n from 5 through 41.

## Still open in this package

- A uniform proof of the pure Z_n branch for every odd n, equivalently a
  continuation theorem for the reduced system over theta in (0, 2*pi/5].
