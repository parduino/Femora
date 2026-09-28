# =============================================================================
# Femora: Fast Efficient Meta-modeling for OpenSees-based Resilience Analysis
# Copyright 2026 Amin Pakzad and Pedro Arduino
# Developed at the UW Geotechnical Lab
# SPDX-License-Identifier: Apache-2.0
# =============================================================================

"""Compare dynamic pile-head displacement for the available boundary cases."""

from __future__ import annotations

from pathlib import Path
from contextlib import ExitStack
import json

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


def render_comparison_movie(results_root, output_dir, stride=5):
    """Synchronized perspective views with one common color scale.

    With the 0.005 s recorder interval, stride=5 at 20 fps plays at half speed.
    """
    import pyvista as pv

    if stride < 1:
        raise ValueError("stride must be positive")
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / "boundary_comparison.mp4"
    preview = output_dir / "boundary_comparison_preview.png"
    metadata = output_dir / "movie_settings.json"
    modes = ("fixed", "rayleigh", "pml")
    with ExitStack() as stack:
        cases = [stack.enter_context(fm.results.open(str(
            Path(results_root) / mode / "results/dynamic_pile_response*.vtkhdf"
        ))) for mode in modes]
        times = cases[0].times
        if times is None or not len(times):
            raise ValueError("Movie requires recorded times")
        for case in cases[1:]:
            if case.times is None or case.times.shape != times.shape or not np.allclose(case.times, times):
                raise ValueError("Comparison movie requires matching case times")
        steps = list(range(0, len(times), stride))
        # Estimate one soil-only range across all cases and sampled movie frames.
        # Clipping the largest 1% keeps the soil wave field visible, not the head motion.
        samples = []
        prepared = []
        for case in cases:
            parts = []
            for reader in case.readers:
                mesh = reader.mesh.copy(deep=True)
                mesh.point_data["movie_point_id"] = np.arange(mesh.n_points)
                centers = mesh.cell_centers().points
                beam = mesh.celltypes == pv.CellType.LINE
                inside = ((np.abs(centers[:, 0]) < 8.0 + 1e-6)
                          & (np.abs(centers[:, 1]) < 3.0 + 1e-6)
                          & (centers[:, 2] >= -8.0 - 1e-6))
                # Remove only the front-right quarter (x > 0, y < 0), not the pile.
                soil = inside & ~beam & ~((centers[:, 0] > 0) & (centers[:, 1] < 0))
                masks = (soil & (centers[:, 2] >= -2.0),
                         soil & (centers[:, 2] < -2.0), inside & beam)
                for kind, mask in enumerate(masks):
                    visible = mesh.extract_cells(np.flatnonzero(mask))
                    if not visible.n_cells:
                        continue
                    ids = np.asarray(visible.point_data["movie_point_id"], dtype=int)
                    parts.append((reader, visible, ids, kind))
                    if kind < 2:
                        for step in steps[::10]:
                            dx = np.asarray(reader.point_frame("displacement", step))[ids[::4], 0]
                            samples.append(np.abs(dx))
            prepared.append(parts)
        if not samples:
            raise ValueError("No soil found inside the movie bounds")
        limit = max(float(np.percentile(np.concatenate(samples), 99)), 1e-12)
        metadata.write_text(json.dumps({
            "deformation_scale": 20, "mass_sphere_radius": 0.7,
            "parallel_projection": False, "show_soil_edges": True,
            "mass_sphere_size_is_symbolic": True, "layer_interface_z_m": -2,
            "removed_quarter": "x > 0 and y < 0", "contour": "horizontal displacement (m)",
            "color_limits": [-limit, limit], "range_method": "99th percentile of sampled soil |dx| across all cases; saturated outside range",
            "stride": stride, "frame_rate": 20,
        }, indent=2))
        plotter = pv.Plotter(shape=(2, 3), off_screen=True, window_size=(1536, 1024))
        try:
            animated = []
            masses = []
            for column, (case, parts) in enumerate(zip(cases, prepared)):
                head = case.nearest_point(PILE_HEAD, tolerance=1e-6)
                motion = np.asarray(case.point_history("displacement", head))[:, :3]
                for row in range(2):
                    plotter.subplot(row, column)
                    mass = pv.Sphere(radius=0.7, center=PILE_HEAD)
                    masses.append((mass, mass.points.copy(), motion))
                    plotter.add_mesh(mass, color="#d7191c", smooth_shading=True)
                    for reader, original, ids, kind in parts:
                        mesh = original.copy(deep=True)
                        mesh.point_data["dx"] = np.zeros(mesh.n_points)
                        if kind == 2:
                            plotter.add_mesh(mesh, color="#292929", line_width=5,
                                             render_lines_as_tubes=True)
                        elif row == 0:
                            plotter.add_mesh(mesh, color=("#d5b78c", "#7b9eac")[kind],
                                             show_edges=True, edge_color="#454545", line_width=0.5)
                        else:
                            soil_actor = plotter.add_mesh(mesh, scalars="dx", clim=(-limit, limit),
                                                          cmap="coolwarm", show_scalar_bar=False,
                                                          show_edges=True, edge_color="#454545", line_width=0.5)
                        animated.append((reader, mesh, ids, mesh.points.copy()))
                    if row == 1:
                        plotter.add_scalar_bar(title="dx (m)", mapper=soil_actor.mapper, fmt="%.1e", n_labels=3,
                                               title_font_size=12, label_font_size=10,
                                               color="black")
                    plotter.set_background("white")
                    plotter.disable_parallel_projection()
                    plotter.camera_position = [(24, -33, 18.5), (0, 0, -3), (0, 0, 1)]
            plotter.open_movie(str(output), framerate=20, quality=7)
            preview_step = min(steps, key=lambda i: abs(times[i] - 1.0))
            for step in steps:
                frames = {}
                for mass, points, motion in masses:
                    mass.points = points + 20.0 * motion[step]
                for reader, mesh, ids, points in animated:
                    if id(reader) not in frames:
                        frames[id(reader)] = np.asarray(reader.point_frame("displacement", step))
                    displacement = frames[id(reader)][ids, :3]
                    mesh.points = points + 20.0 * displacement
                    mesh.point_data["dx"] = displacement[:, 0]
                for column, mode in enumerate(modes):
                    for row in range(2):
                        plotter.subplot(row, column)
                        plotter.add_text(f"{mode.upper()} | {times[step]:.3f} s",
                                         name="time", font_size=12, color="black")
                plotter.write_frame()
                if step == preview_step:
                    plotter.screenshot(str(preview))
        finally:
            plotter.close()
    return output, preview, metadata


def generate_results(results_root=OUTPUT_DIR, output_dir=None, require_all=False,
                     movies=False) -> tuple[Path, ...]:
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
    if movies:
        artifacts.extend(render_comparison_movie(results_root, output_dir))
    return (output_file, *artifacts)


if __name__ == "__main__":
    for result in generate_results():
        print(f"Generated: {result.resolve()}")
