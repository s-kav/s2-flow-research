"""Exact rational interval arithmetic with dyadic square-root enclosures."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from math import isqrt


@dataclass(frozen=True)
class RationalInterval:
    """A closed interval with exact rational endpoints."""

    lower: Fraction
    upper: Fraction

    def __init__(self, lower: int | Fraction, upper: int | Fraction | None = None):
        low = Fraction(lower)
        high = low if upper is None else Fraction(upper)
        if low > high:
            raise ValueError("Interval lower endpoint exceeds upper endpoint")
        object.__setattr__(self, "lower", low)
        object.__setattr__(self, "upper", high)

    @staticmethod
    def coerce(value: int | Fraction | "RationalInterval") -> "RationalInterval":
        """Convert a scalar or interval to RationalInterval."""
        return value if isinstance(value, RationalInterval) else RationalInterval(value)

    def __add__(self, other: int | Fraction | "RationalInterval") -> "RationalInterval":
        rhs = self.coerce(other)
        return RationalInterval(self.lower + rhs.lower, self.upper + rhs.upper)

    __radd__ = __add__

    def __neg__(self) -> "RationalInterval":
        return RationalInterval(-self.upper, -self.lower)

    def __sub__(self, other: int | Fraction | "RationalInterval") -> "RationalInterval":
        return self + (-self.coerce(other))

    def __rsub__(self, other: int | Fraction | "RationalInterval") -> "RationalInterval":
        return self.coerce(other) - self

    def __mul__(self, other: int | Fraction | "RationalInterval") -> "RationalInterval":
        rhs = self.coerce(other)
        products = (
            self.lower * rhs.lower,
            self.lower * rhs.upper,
            self.upper * rhs.lower,
            self.upper * rhs.upper,
        )
        return RationalInterval(min(products), max(products))

    __rmul__ = __mul__

    def reciprocal(self) -> "RationalInterval":
        """Return an exact reciprocal enclosure."""
        if self.lower <= 0 <= self.upper:
            raise ZeroDivisionError("Interval contains zero")
        values = (Fraction(1, 1) / self.lower, Fraction(1, 1) / self.upper)
        return RationalInterval(min(values), max(values))

    def __truediv__(self, other: int | Fraction | "RationalInterval") -> "RationalInterval":
        return self * self.coerce(other).reciprocal()

    def __rtruediv__(self, other: int | Fraction | "RationalInterval") -> "RationalInterval":
        return self.coerce(other) / self

    def square(self) -> "RationalInterval":
        """Return an exact square enclosure."""
        if self.lower >= 0:
            return RationalInterval(self.lower * self.lower, self.upper * self.upper)
        if self.upper <= 0:
            return RationalInterval(self.upper * self.upper, self.lower * self.lower)
        return RationalInterval(0, max(self.lower * self.lower, self.upper * self.upper))

    def to_json(self) -> dict[str, str]:
        """Serialize exact endpoints as numerator/denominator strings."""
        return {
            "lower": fraction_to_text(self.lower),
            "upper": fraction_to_text(self.upper),
        }


def fraction_to_text(value: Fraction) -> str:
    """Serialize a Fraction without losing information."""
    return f"{value.numerator}/{value.denominator}"


def fraction_from_text(value: str) -> Fraction:
    """Parse a numerator/denominator string."""
    numerator, denominator = value.split("/", maxsplit=1)
    return Fraction(int(numerator), int(denominator))


def dyadic_sqrt_bounds(value: Fraction, bits: int) -> tuple[Fraction, Fraction]:
    """Return exact outward dyadic bounds for a rational square root."""
    if bits < 8:
        raise ValueError("bits must be at least 8")
    rational = Fraction(value)
    if rational < 0:
        raise ValueError("Square root requires a non-negative rational")
    if rational == 0:
        return Fraction(0), Fraction(0)

    scaled_numerator = rational.numerator << (2 * bits)
    denominator = rational.denominator
    floor_quotient = scaled_numerator // denominator
    lower_integer = isqrt(floor_quotient)
    lower = Fraction(lower_integer, 1 << bits)

    if lower_integer * lower_integer * denominator == scaled_numerator:
        upper = lower
    else:
        upper = Fraction(lower_integer + 1, 1 << bits)
    return lower, upper


def interval_sqrt(interval: RationalInterval, bits: int) -> RationalInterval:
    """Return an outward dyadic enclosure for sqrt(interval)."""
    if interval.lower < 0:
        raise ValueError("Square-root interval crosses the negative axis")
    lower, _ = dyadic_sqrt_bounds(interval.lower, bits)
    _, upper = dyadic_sqrt_bounds(interval.upper, bits)
    return RationalInterval(lower, upper)


@dataclass(frozen=True)
class DualInterval:
    """Interval value and first derivative with respect to one variable."""

    value: RationalInterval
    derivative: RationalInterval

    def __init__(
        self,
        value: int | Fraction | RationalInterval,
        derivative: int | Fraction | RationalInterval = 0,
    ):
        object.__setattr__(self, "value", RationalInterval.coerce(value))
        object.__setattr__(self, "derivative", RationalInterval.coerce(derivative))

    @staticmethod
    def coerce(value: int | Fraction | RationalInterval | "DualInterval") -> "DualInterval":
        """Convert a scalar, interval, or dual interval."""
        return value if isinstance(value, DualInterval) else DualInterval(value)

    def __add__(self, other: int | Fraction | RationalInterval | "DualInterval") -> "DualInterval":
        rhs = self.coerce(other)
        return DualInterval(self.value + rhs.value, self.derivative + rhs.derivative)

    __radd__ = __add__

    def __neg__(self) -> "DualInterval":
        return DualInterval(-self.value, -self.derivative)

    def __sub__(self, other: int | Fraction | RationalInterval | "DualInterval") -> "DualInterval":
        return self + (-self.coerce(other))

    def __rsub__(self, other: int | Fraction | RationalInterval | "DualInterval") -> "DualInterval":
        return self.coerce(other) - self

    def __mul__(self, other: int | Fraction | RationalInterval | "DualInterval") -> "DualInterval":
        rhs = self.coerce(other)
        return DualInterval(
            self.value * rhs.value,
            self.derivative * rhs.value + self.value * rhs.derivative,
        )

    __rmul__ = __mul__

    def reciprocal(self) -> "DualInterval":
        """Return the reciprocal and its derivative enclosure."""
        return DualInterval(
            self.value.reciprocal(),
            -self.derivative / self.value.square(),
        )

    def __truediv__(self, other: int | Fraction | RationalInterval | "DualInterval") -> "DualInterval":
        return self * self.coerce(other).reciprocal()

    def __rtruediv__(self, other: int | Fraction | RationalInterval | "DualInterval") -> "DualInterval":
        return self.coerce(other) / self


def dual_sqrt(value: DualInterval, bits: int) -> DualInterval:
    """Return sqrt(value) and the derivative enclosure."""
    square_root = interval_sqrt(value.value, bits)
    return DualInterval(square_root, value.derivative / (2 * square_root))
