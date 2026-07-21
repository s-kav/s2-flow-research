"""Tests for exact interval arithmetic and theorem certification."""

from fractions import Fraction

from goldberg_s2.interval import RationalInterval, dyadic_sqrt_bounds
from goldberg_s2.interval_proof import generate_interval_certificate


def test_dyadic_sqrt_bounds_are_outward() -> None:
    """Dyadic square-root bounds must contain the exact rational square."""
    lower, upper = dyadic_sqrt_bounds(Fraction(2), bits=80)
    assert lower * lower <= 2
    assert upper * upper >= 2
    assert upper - lower <= Fraction(1, 1 << 80)


def test_interval_square_crossing_zero() -> None:
    """Squaring an interval crossing zero must start at zero."""
    squared = RationalInterval(-2, 3).square()
    assert squared.lower == 0
    assert squared.upper == 9


def test_exact_theorem_certificate_small_partition() -> None:
    """A compact exact certificate must prove signs and strict monotonicity."""
    certificate = generate_interval_certificate(
        endpoint_pieces=16,
        derivative_s_pieces=16,
        derivative_x_pieces=16,
        bits=96,
    )
    summary = certificate["summary"]
    assert Fraction(summary["max_upper_H_at_s_lower"]) < 0
    assert Fraction(summary["min_lower_H_at_s_upper"]) > 0
    assert Fraction(summary["min_lower_dH_ds"]) > 0
