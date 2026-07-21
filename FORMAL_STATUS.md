# Formal Status of the Results

## Theorems established in this release

### Flower snarks

For every odd integer `n >= 5`, the Isaacs flower snark `J_n` admits an `S^2`-flow. The proof uses a free cyclic `Z_n` action, a six-template reduction, an analytic cascade to one scalar equation, endpoint signs, and strict monotonicity. The stored finite Kantorovich certificates and numerical branches are supplementary reproducibility evidence, not the logical basis of the infinite theorem.

### Goldberg snarks

For every odd integer `k >= 5`, the Goldberg snark `G_k` defined by the eight-vertex block in the cited construction admits an `S^2`-flow. The proof uses a cyclic representation of index `(k-1)/2`, an explicit twelve-template reconstruction, reduction to `H(s,x)=0`, and an exact rational interval certificate establishing endpoint signs and `partial H / partial s > 0` on the full parameter rectangle.

## Exact computer-assisted statements

- The Goldberg interval certificate is checked with rational interval arithmetic.
- Exact dyadic Newton-Kantorovich certificates are supplied for flower snarks `J_5` through `J_41`.
- The strict order-`2n` flower ansatz is excluded by an exact structural obstruction.

## Numerical evidence only

- Equivariance residuals of previously stored unconstrained certificates.
- Finite sweeps over large parameter ranges.
- Random and `nauty` finite-graph campaigns.
- Solver timing, conditioning, and branch-continuation diagnostics.

These computations validate implementations and guide conjecture formation but are not proofs for unbounded graph classes.

## Not claimed

The universal conjecture that every bridgeless cubic graph admits an `S^2`-flow remains open. This repository proves the conjecture for two named infinite snark families only.
