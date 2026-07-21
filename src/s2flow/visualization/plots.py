"""Optional convergence and residual plots."""
from pathlib import Path

def save_residual_bar(metrics: dict[str, float], path: Path) -> None:
    """Save a simple residual bar chart when matplotlib is installed."""
    import matplotlib.pyplot as plt
    keys = ["max_conservation_residual", "max_unit_norm_residual", "max_bq_residual"]
    values = [max(float(metrics[k]), 1e-18) for k in keys]
    fig, ax = plt.subplots()
    ax.bar(keys, values)
    ax.set_yscale("log")
    ax.tick_params(axis="x", rotation=20)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)
