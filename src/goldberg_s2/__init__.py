"""Goldberg snark S^2-flow theorem and reproducibility package."""

from .construction import build_templates, solve_scalar_root
from .graph import goldberg_graph
from .verify import verify_full_flow, verify_reduced_templates

__all__ = [
    "build_templates",
    "goldberg_graph",
    "solve_scalar_root",
    "verify_full_flow",
    "verify_reduced_templates",
]
