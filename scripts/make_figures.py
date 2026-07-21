#!/usr/bin/env python3
"""Generate figures used by the English theorem report."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np

from goldberg_s2.algebra import scalar_function
from goldberg_s2.construction import solve_scalar_root
from goldberg_s2.graph import INTERNAL_EDGES


def make_block_figure(output: Path) -> None:
    """Draw the eight-vertex Goldberg block and its six external terminals."""
    graph = nx.Graph()
    graph.add_edges_from(INTERNAL_EDGES)
    positions = {
        1: (-1.8, 1.2),
        2: (-0.6, 1.2),
        3: (0.6, 1.2),
        4: (1.8, 1.2),
        7: (-0.9, 0.0),
        8: (0.9, 0.0),
        6: (0.0, -1.0),
        5: (0.0, -2.0),
    }

    fig, axis = plt.subplots(figsize=(8.2, 5.4))
    nx.draw_networkx_edges(graph, positions, ax=axis, width=1.8)
    nx.draw_networkx_nodes(graph, positions, ax=axis, node_size=900)
    nx.draw_networkx_labels(
        graph,
        positions,
        labels={vertex: rf"$v_{vertex}^t$" for vertex in graph.nodes()},
        font_size=11,
        ax=axis,
    )

    external = [
        ((-0.6, 1.2), (-0.6, 2.1), r"$v_2^t\to v_1^{t+1}$"),
        ((1.8, 1.2), (1.8, 2.1), r"$v_4^t\to v_3^{t+1}$"),
        ((0.0, -2.0), (1.25, -2.0), r"$v_5^t\to v_5^{t+1}$"),
        ((-1.8, 1.2), (-1.8, 2.1), r"$v_2^{t-1}\to v_1^t$"),
        ((0.6, 1.2), (0.6, 2.1), r"$v_4^{t-1}\to v_3^t$"),
        ((0.0, -2.0), (-1.25, -2.0), r"$v_5^{t-1}\to v_5^t$"),
    ]
    for start, end, label in external:
        axis.annotate("", xy=end, xytext=start, arrowprops={"arrowstyle": "->", "lw": 1.4})
        midpoint = ((start[0] + end[0]) / 2, (start[1] + end[1]) / 2)
        axis.text(midpoint[0], midpoint[1], label, fontsize=9, ha="center", va="center")

    axis.set_title("Goldberg block and inter-block channels")
    axis.set_xlim(-2.7, 2.8)
    axis.set_ylim(-2.6, 2.55)
    axis.set_axis_off()
    fig.tight_layout()
    fig.savefig(output, dpi=220, bbox_inches="tight")
    plt.close(fig)


def make_scalar_figure(output: Path) -> None:
    """Plot the unique scalar root and the uniform theorem bracket."""
    k_values = np.arange(5, 502, 2)
    x_values = np.tan(np.pi / (2.0 * k_values))
    roots = np.array([solve_scalar_root(int(k)) for k in k_values])

    fig, axis = plt.subplots(figsize=(8.2, 4.8))
    axis.plot(x_values, roots, linewidth=1.8, label=r"unique root $s(x)$")
    axis.axhline(2.0 / 3.0, linestyle="--", linewidth=1.2, label=r"lower bracket $2/3$")
    axis.axhline(21.0 / 25.0, linestyle="--", linewidth=1.2, label=r"upper bracket $21/25$")
    axis.set_xlabel(r"$x=\tan(\pi/(2k))$")
    axis.set_ylabel(r"$s$")
    axis.set_title("Scalar branch for odd Goldberg parameters")
    axis.grid(True, alpha=0.25)
    axis.legend()
    fig.tight_layout()
    fig.savefig(output, dpi=220, bbox_inches="tight")
    plt.close(fig)


def make_endpoint_figure(output: Path) -> None:
    """Plot endpoint signs across the exact proof domain."""
    x_values = np.linspace(0.0, 13.0 / 40.0, 400)
    lower = np.array([scalar_function(2.0 / 3.0, x) for x in x_values])
    upper = np.array([scalar_function(21.0 / 25.0, x) for x in x_values])

    fig, axis = plt.subplots(figsize=(8.2, 4.8))
    axis.plot(x_values, lower, linewidth=1.8, label=r"$H(2/3,x)$")
    axis.plot(x_values, upper, linewidth=1.8, label=r"$H(21/25,x)$")
    axis.axhline(0.0, linewidth=1.0)
    axis.set_xlabel(r"$x$")
    axis.set_ylabel(r"$H$")
    axis.set_title("Uniform sign separation used by the exact interval proof")
    axis.grid(True, alpha=0.25)
    axis.legend()
    fig.tight_layout()
    fig.savefig(output, dpi=220, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    """Generate all report figures."""
    root = Path(__file__).resolve().parents[1]
    output = root / "docs" / "figures"
    output.mkdir(parents=True, exist_ok=True)
    make_block_figure(output / "goldberg_block.png")
    make_scalar_figure(output / "scalar_branch.png")
    make_endpoint_figure(output / "endpoint_signs.png")


if __name__ == "__main__":
    main()
