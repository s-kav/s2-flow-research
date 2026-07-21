# Validation record

The repository was validated on 21 July 2026.

## Exact proof certificate

- Certificate schema: `goldberg-s2-interval-certificate-v1`
- Dyadic precision: 112 bits
- Endpoint partition: 16 x-boxes
- Derivative partition: 32 x 32 boxes
- `H(2/3, x)` certified strictly negative on `x in [0, 13/40]`
- `H(21/25, x)` certified strictly positive on `x in [0, 13/40]`
- `partial H / partial s` certified strictly positive on the full rectangle
- Certificate SHA-256: `0a55c601b8e1ea62c350a97da2cbb883cf8448e38f5f96918ba7c19206bfdf93`

## Numerical regression checks

- 499 odd parameters checked: `k = 5, 7, ..., 1001`
- 149 full Goldberg graphs expanded: `k = 5, 7, ..., 301`
- Worst reduced Kirchhoff residual: `3.036e-16`
- Worst reduced unit-norm residual: `2.220e-15`
- Worst full-graph Kirchhoff residual: `7.196e-14`
- Worst full-graph unit-norm residual: `3.708e-14`
- Independent large instance: `G_1001`, 8,008 vertices and 12,012 edges
- `G_1001` maximum Kirchhoff residual: `1.0414781016765406e-13`
- `G_1001` maximum unit-norm residual: `1.525446435834965e-13`

## Software checks

- 10 automated tests passed
- All Python sources compiled successfully
- The Word report was rendered to six pages and every page was visually inspected
