"""Tests for the explicit Goldberg S^2-flow construction."""

from goldberg_s2.construction import build_templates, representation_index, rotation_angle
from goldberg_s2.verify import verify_full_flow, verify_reduced_templates


def test_representation_closes_for_odd_k() -> None:
    """The selected cyclic representation must satisfy R^k = I."""
    for k in (5, 7, 9, 41):
        ell = representation_index(k)
        assert 2 * ell == k - 1
        assert abs(k * rotation_angle(k) - 2.0 * 3.141592653589793 * ell) < 1e-12


def test_reduced_and_full_flows() -> None:
    """Representative and full-graph equations must agree."""
    for k in (5, 7, 9, 21):
        templates = build_templates(k)
        kirchhoff, norm = verify_reduced_templates(k, templates)
        assert kirchhoff < 2e-13
        assert norm < 2e-13

        result = verify_full_flow(k, templates)
        assert result.max_kirchhoff_residual < 5e-13
        assert result.max_unit_norm_residual < 5e-13
        assert result.cubic
        assert result.connected
        assert result.bridges == 0
