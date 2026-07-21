"""Exact interval certificate for the Goldberg scalar theorem."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

from .interval import DualInterval, RationalInterval, dual_sqrt, interval_sqrt

X_UPPER = Fraction(13, 40)
S_LOWER = Fraction(2, 3)
S_UPPER = Fraction(21, 25)


@dataclass(frozen=True)
class IntervalLocalCoordinates:
    """Interval enclosure of the local scalar formulas."""

    z: RationalInterval
    delta: RationalInterval
    a_x: RationalInterval
    a_z: RationalInterval
    b_x: RationalInterval
    b_z: RationalInterval


@dataclass(frozen=True)
class DualLocalCoordinates:
    """Dual-interval enclosure of the local scalar formulas."""

    z: DualInterval
    delta: DualInterval
    a_x: DualInterval
    a_z: DualInterval
    b_x: DualInterval
    b_z: DualInterval


def interval_local_coordinates(
    y: Fraction,
    x: RationalInterval,
    bits: int,
) -> IntervalLocalCoordinates:
    """Evaluate the local formulas with exact rational intervals."""
    one = RationalInterval(1)
    z = interval_sqrt(one - y * y * (one + x.square()), bits)
    delta = interval_sqrt(RationalInterval(3 - 4 * y * y), bits)
    denominator = 2 * (1 - y * y)
    a_x = (delta * z - y * x) / denominator
    a_z = (z + delta * y * x) / denominator
    b_x = a_x + y * x
    b_z = a_z - z
    return IntervalLocalCoordinates(z, delta, a_x, a_z, b_x, b_z)


def interval_scalar_function(
    s: Fraction,
    x: RationalInterval,
    bits: int,
) -> RationalInterval:
    """Enclose H(s, x) for one fixed rational s."""
    t = Fraction(1, 2) - s
    left = interval_local_coordinates(s, x, bits)
    right = interval_local_coordinates(t, x, bits)
    horizontal = right.b_x - left.b_x
    vertical = left.b_z - right.b_z
    return horizontal.square() + vertical.square() - Fraction(3, 4)


def dual_local_coordinates(
    y: DualInterval,
    x: DualInterval,
    bits: int,
) -> DualLocalCoordinates:
    """Evaluate the local formulas and their s-derivatives."""
    z = dual_sqrt(1 - y * y * (1 + x * x), bits)
    delta = dual_sqrt(3 - 4 * y * y, bits)
    denominator = 2 * (1 - y * y)
    a_x = (delta * z - y * x) / denominator
    a_z = (z + delta * y * x) / denominator
    b_x = a_x + y * x
    b_z = a_z - z
    return DualLocalCoordinates(z, delta, a_x, a_z, b_x, b_z)


def dual_scalar_function(
    s_interval: RationalInterval,
    x_interval: RationalInterval,
    bits: int,
) -> DualInterval:
    """Enclose H and partial H/partial s on one rectangle."""
    s = DualInterval(s_interval, 1)
    t = DualInterval(Fraction(1, 2), 0) - s
    x = DualInterval(x_interval, 0)
    left = dual_local_coordinates(s, x, bits)
    right = dual_local_coordinates(t, x, bits)
    horizontal = right.b_x - left.b_x
    vertical = left.b_z - right.b_z
    return horizontal * horizontal + vertical * vertical - Fraction(3, 4)


def partition_interval(
    lower: Fraction,
    upper: Fraction,
    pieces: int,
) -> list[RationalInterval]:
    """Split a rational interval into equal exact subintervals."""
    if pieces <= 0:
        raise ValueError("pieces must be positive")
    width = upper - lower
    return [
        RationalInterval(
            lower + width * index / pieces,
            lower + width * (index + 1) / pieces,
        )
        for index in range(pieces)
    ]


def generate_interval_certificate(
    endpoint_pieces: int = 16,
    derivative_s_pieces: int = 32,
    derivative_x_pieces: int = 32,
    bits: int = 112,
) -> dict[str, object]:
    """Generate all exact enclosures needed by the theorem."""
    x_intervals = partition_interval(Fraction(0), X_UPPER, endpoint_pieces)
    lower_boxes = []
    upper_boxes = []

    for index, x_interval in enumerate(x_intervals):
        lower_value = interval_scalar_function(S_LOWER, x_interval, bits)
        upper_value = interval_scalar_function(S_UPPER, x_interval, bits)
        lower_boxes.append(
            {
                "index": index,
                "x": x_interval.to_json(),
                "H": lower_value.to_json(),
            }
        )
        upper_boxes.append(
            {
                "index": index,
                "x": x_interval.to_json(),
                "H": upper_value.to_json(),
            }
        )

    s_intervals = partition_interval(S_LOWER, S_UPPER, derivative_s_pieces)
    derivative_x_intervals = partition_interval(Fraction(0), X_UPPER, derivative_x_pieces)
    derivative_boxes = []

    for s_index, s_interval in enumerate(s_intervals):
        for x_index, x_interval in enumerate(derivative_x_intervals):
            result = dual_scalar_function(s_interval, x_interval, bits)
            derivative_boxes.append(
                {
                    "s_index": s_index,
                    "x_index": x_index,
                    "s": s_interval.to_json(),
                    "x": x_interval.to_json(),
                    "H": result.value.to_json(),
                    "dH_ds": result.derivative.to_json(),
                }
            )

    lower_worst = max(Fraction(box["H"]["upper"]) for box in lower_boxes)
    upper_worst = min(Fraction(box["H"]["lower"]) for box in upper_boxes)
    derivative_worst = min(Fraction(box["dH_ds"]["lower"]) for box in derivative_boxes)

    if lower_worst >= 0:
        raise RuntimeError("Lower endpoint sign was not certified")
    if upper_worst <= 0:
        raise RuntimeError("Upper endpoint sign was not certified")
    if derivative_worst <= 0:
        raise RuntimeError("Strict monotonicity was not certified")

    return {
        "schema": "goldberg-s2-interval-certificate-v1",
        "bits": bits,
        "domain": {
            "x": RationalInterval(0, X_UPPER).to_json(),
            "s": RationalInterval(S_LOWER, S_UPPER).to_json(),
        },
        "partitions": {
            "endpoint_x": endpoint_pieces,
            "derivative_s": derivative_s_pieces,
            "derivative_x": derivative_x_pieces,
        },
        "summary": {
            "max_upper_H_at_s_lower": str(lower_worst),
            "min_lower_H_at_s_upper": str(upper_worst),
            "min_lower_dH_ds": str(derivative_worst),
        },
        "lower_endpoint_boxes": lower_boxes,
        "upper_endpoint_boxes": upper_boxes,
        "derivative_boxes": derivative_boxes,
    }


def verify_interval_certificate(certificate: dict[str, object]) -> dict[str, Fraction]:
    """Recompute and compare every exact interval in a stored certificate."""
    if certificate.get("schema") != "goldberg-s2-interval-certificate-v1":
        raise ValueError("Unsupported interval certificate schema")

    bits = int(certificate["bits"])
    partitions = certificate["partitions"]
    regenerated = generate_interval_certificate(
        endpoint_pieces=int(partitions["endpoint_x"]),
        derivative_s_pieces=int(partitions["derivative_s"]),
        derivative_x_pieces=int(partitions["derivative_x"]),
        bits=bits,
    )

    if regenerated != certificate:
        raise RuntimeError("Stored certificate differs from exact recomputation")

    summary = regenerated["summary"]
    return {
        "max_upper_H_at_s_lower": Fraction(summary["max_upper_H_at_s_lower"]),
        "min_lower_H_at_s_upper": Fraction(summary["min_lower_H_at_s_upper"]),
        "min_lower_dH_ds": Fraction(summary["min_lower_dH_ds"]),
    }
