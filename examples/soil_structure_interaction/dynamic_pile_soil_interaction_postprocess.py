# =============================================================================
# Femora: Fast Efficient Meta-modeling for OpenSees-based Resilience Analysis
# Copyright 2026 Amin Pakzad and Pedro Arduino
# Developed at the UW Geotechnical Lab
# SPDX-License-Identifier: Apache-2.0
# =============================================================================

"""Compare dynamic pile-head displacement for the available boundary cases."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

import femora as fm


ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = ROOT / "example_outputs" / "dynamic_pile_soil_interaction"
OUTPUT_FILE = OUTPUT_DIR / "post_processing" / "boundary_comparison.png"
PILE_HEAD = np.array([0.0, 0.0, 2.0])
BOUNDARY_STYLES = {
    "fixed": ("Fixed boundary", "#2b6cb0"),
    "pml": ("PML absorbing boundary", "#d64545"),
    "rayleigh": ("Rayleigh absorbing boundary", "#2f855a"),
}


def read_head_response(mode: str, results_root=OUTPUT_DIR) -> tuple[np.ndarray, np.ndarray] | None:
    """Read one boundary case, returning ``None`` when it was not run."""
    results_dir = Path(results_root) / mode / "results"
    if not list(results_dir.glob("dynamic_pile_response*.vtkhdf")):
        return None
    with fm.results.open(str(results_dir / "dynamic_pile_response*.vtkhdf")) as results:
        point = results.nearest_point(PILE_HEAD, tolerance=1.0e-6)
        displacement = np.asarray(results.point_history("displacement", point))[:, :3]
        time = results.times
        if time is None:
            raise ValueError(f"{mode}: recorder output has no physical time values")
        if len(time) != len(displacement) or not len(time):
            raise ValueError(f"{mode}: empty or inconsistent response history")
    return np.asarray(time), displacement


def generate_results(results_root=OUTPUT_DIR, output_dir=None, require_all=False) -> tuple[Path, ...]:
    """Generate a comparison plot for every available boundary case."""
    responses = {
        mode: response
        for mode in BOUNDARY_STYLES
        if (response := read_head_response(mode, results_root)) is not None
    }
    if require_all and set(responses) != set(BOUNDARY_STYLES):
        raise FileNotFoundError(f"Missing boundary results: {sorted(set(BOUNDARY_STYLES) - set(responses))}")
    if not responses:
        raise FileNotFoundError(
            f"No dynamic responses found below {results_root}. Run a boundary case first."
        )

    output_dir = Path(output_dir) if output_dir is not None else Path(results_root) / "post_processing"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "boundary_comparison.png"
    artifacts = []
    figure, axes = plt.subplots(3, 1, figsize=(8.0, 7.0), sharex=True, constrained_layout=True)
    labels = ("$d_x$ (m)", "$d_y$ (m)", "$d_z$ (m)")
    for mode, (time, displacement) in responses.items():
        history_file = output_dir / f"{mode}_pile_head.csv"
        np.savetxt(history_file, np.column_stack((time, displacement)), delimiter=",",
                   header="time_s,dx_m,dy_m,dz_m", comments="")
        artifacts.append(history_file)
        legend_label, color = BOUNDARY_STYLES[mode]
        for axis, component, label in zip(axes, displacement.T, labels):
            axis.plot(time, component, color=color, linewidth=1.3, label=legend_label)
    for axis, label in zip(axes, labels):
        axis.set_ylabel(label)
        axis.grid(True, linestyle="--", alpha=0.45)
        axis.legend(loc="best")
    axes[0].set_title("Pile-head displacement for boundary treatments")
    axes[-1].set_xlabel("Time (s)")
    figure.savefig(output_file, dpi=180, bbox_inches="tight")
    plt.close(figure)
    return (output_file, *artifacts)


if __name__ == "__main__":
    for result in generate_results():
        print(f"Generated: {result.resolve()}")
