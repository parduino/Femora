# =============================================================================
# Femora: Fast Efficient Meta-modeling for OpenSees-based Resilience Analysis
# Copyright 2026 Amin Pakzad and Pedro Arduino
# Developed at the UW Geotechnical Lab
# SPDX-License-Identifier: Apache-2.0
# =============================================================================

"""Extract bent histories, pile deformation/forces, and a remote cutaway movie."""

from __future__ import annotations

import json
import io
from pathlib import Path
from xml.etree import ElementTree

import matplotlib.pyplot as plt
import numpy as np

import femora as fm


RESPONSE_GLOB = "two_pile_bent_response*.vtkhdf"
FINAL_TIME = 4.0
RECORDER_DT = 0.005
TOLERANCE = 1.0e-6
POINTS = {
    "left_head": np.array([-2.5, 0.0, 3.0]),
    "right_head": np.array([2.5, 0.0, 3.0]),
    "cap_center": np.array([0.0, 0.0, 3.0]),
}
POINT_LABELS = {
    "left_head": "Left pile head (-2.5, 0, 3)",
    "right_head": "Right pile head (2.5, 0, 3)",
    "cap_center": "Cap center (0, 0, 3)",
}
PILE_NAMES = ("pile_left", "pile_right")
FORCE_COMPONENTS = ("Px", "Py", "Pz", "Mx", "My", "Mz")


def read_pile_geometry(results_root):
    """Use exported element tags and oriented endpoints, never file ordering."""
    path = Path(results_root) / "bent/pile_geometry.json"
    geometry = json.loads(path.read_text(encoding="utf-8"))
    tags = set()
    for name in PILE_NAMES:
        elements = geometry[name]
        if len(elements) != 16:
            raise ValueError(f"{name}: expected 16 pile elements")
        for element in elements:
            ends = np.asarray(element["ends_m"], dtype=float)
            if (ends.shape != (2, 3) or not np.isfinite(ends).all()
                    or not np.allclose(ends[0, :2], ends[1, :2], atol=TOLERANCE)
                    or ends[0, 2] >= ends[1, 2]):
                raise ValueError(f"{name}: expected vertical bottom-to-top endpoints")
            if element["tag"] in tags:
                raise ValueError("Duplicate pile element tag in geometry")
            tags.add(element["tag"])
        ordered = sorted(elements, key=lambda item: item["ends_m"][0][2])
        for lower, upper in zip(ordered, ordered[1:]):
            if not np.allclose(lower["ends_m"][1], upper["ends_m"][0], atol=TOLERANCE):
                raise ValueError(f"{name}: disconnected pile geometry")
    return geometry


def read_pile_forces(results_root, reference_time):
    """Read global resisting end forces, including all MPI partitions."""
    geometry = read_pile_geometry(results_root)
    expected_labels = [f"{name}_{end}" for end in (1, 2) for name in FORCE_COMPONENTS]
    histories = {}
    for pile in PILE_NAMES:
        expected = {item["tag"]: item for item in geometry[pile]}
        paths = sorted((Path(results_root) / "bent/results").glob(
            f"pile_force_{pile}_Core*_globalForce.xml"
        ))
        if not paths:
            raise FileNotFoundError(f"Missing force recorder for {pile}; rerun with beam_force")
        found = {}
        for path in paths:
            root = ElementTree.parse(path).getroot()
            outputs = root.findall(".//ElementOutput")
            data = root.find(".//Data")
            if not outputs or data is None or not data.text:
                raise ValueError(f"Incomplete force recorder: {path}")
            rows = np.loadtxt(io.StringIO(data.text), ndmin=2)
            if rows.shape != (len(reference_time), 1 + 12 * len(outputs)):
                raise ValueError(f"Incorrect force recorder shape: {path}")
            if not np.isfinite(rows).all():
                raise ValueError(f"Non-finite force recorder: {path}")
            if not np.allclose(rows[:, 0], reference_time, rtol=0, atol=1e-8):
                raise ValueError(f"Force/displacement times disagree: {path}")
            for index, output in enumerate(outputs):
                tag = int(output.attrib["eleTag"])
                labels = [item.text for item in output.findall("ResponseType")]
                if labels != expected_labels:
                    raise ValueError(f"Element {tag}: unexpected global force components")
                if tag not in expected or tag in found:
                    raise ValueError(f"Unexpected or duplicate force element {tag}")
                if f"_Core{expected[tag]['core']}_" not in path.name:
                    raise ValueError(f"Element {tag}: force file core does not match geometry")
                found[tag] = rows[:, 1 + 12 * index:1 + 12 * (index + 1)].copy()
        if set(found) != set(expected):
            raise ValueError(f"{pile}: missing force element tags")
        histories[pile] = found
    return geometry, histories


def generate_pile_force_results(results_root, output_dir, reference_time):
    """Keep raw end actions and plot time envelopes of averaged nodal moments."""
    geometry, histories = read_pile_forces(results_root, reference_time)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    artifacts = []
    figure, axes = plt.subplots(1, 2, figsize=(9, 6), sharey=True)
    try:
        for axis, pile in zip(axes, PILE_NAMES):
            force_rows, envelope_rows = [], []
            ordered = sorted(geometry[pile], key=lambda item: item["ends_m"][0][2])
            nodal_values = [[] for _ in range(len(ordered) + 1)]
            elevations = [ordered[0]["ends_m"][0][2]]
            for index, element in enumerate(ordered):
                tag = element["tag"]
                forces = histories[pile][tag]
                z = np.asarray(element["ends_m"])[:, 2]
                minimum = np.min(forces[:, [4, 10]], axis=0) / 1000
                maximum = np.max(forces[:, [4, 10]], axis=0) / 1000
                # Average signed moments in a common face convention at EACH time.
                # This deliberately smooths interface-induced end-action jumps.
                nodal_values[index].append(-forces[:, [3, 4]])
                nodal_values[index + 1].append(forces[:, [9, 10]])
                elevations.append(z[1])
                for end in (0, 1):
                    block = forces[:, 6 * end:6 * (end + 1)]
                    force_rows.append(np.column_stack((
                        reference_time, np.full(len(reference_time), tag),
                        np.full(len(reference_time), end + 1),
                        np.full(len(reference_time), z[end]), block,
                    )))
                    envelope_rows.append((tag, end + 1, z[end], minimum[end], maximum[end]))
            force_csv = output_dir / f"{pile}_end_forces.csv"
            np.savetxt(force_csv, np.vstack(force_rows), delimiter=",", comments="",
                       header="time_s,element_tag,end,z_m,Px_N,Py_N,Pz_N,Mx_Nm,My_Nm,Mz_Nm")
            envelope_csv = output_dir / f"{pile}_moment_envelope.csv"
            np.savetxt(envelope_csv, envelope_rows, delimiter=",", comments="",
                       header="element_tag,end,z_m,min_My_kNm,max_My_kNm")
            artifacts.extend((force_csv, envelope_csv))
            nodal = np.stack([np.mean(values, axis=0) for values in nodal_values], axis=1) / 1000
            minimum = np.min(nodal, axis=0)
            maximum = np.max(nodal, axis=0)
            averaged_csv = output_dir / f"{pile}_averaged_moment_envelope.csv"
            np.savetxt(averaged_csv, np.column_stack((elevations, minimum, maximum)),
                       delimiter=",", comments="",
                       header="z_m,min_averaged_Mx_kNm,min_averaged_My_kNm,max_averaged_Mx_kNm,max_averaged_My_kNm")
            artifacts.append(averaged_csv)
            for values, label, style, color in (
                    (minimum[:, 0], "Min Mx", "--", "#d64545"),
                    (maximum[:, 0], "Max Mx", "-", "#d64545"),
                    (minimum[:, 1], "Min My", "--", "#2b6cb0"),
                    (maximum[:, 1], "Max My", "-", "#2b6cb0")):
                axis.plot(values, elevations, style, color=color, linewidth=1.7, label=label)
            axis.axvline(0, color="#888888", linewidth=0.8)
            axis.legend(fontsize=8)
            axis.set(title=pile.replace("_", " ").title(), xlabel="Bending moment envelope (kN m)")
            axis.axhline(0, color="#555555", linestyle="--", linewidth=0.8)
            axis.grid(alpha=0.25)
        axes[0].set_ylabel("Elevation z (m)")
        figure.suptitle("Pile bending envelopes: signed minimum and maximum")
        figure.text(0.5, 0.01, "Shared-node end moments averaged at each time before taking extrema; interface jumps smoothed",
                    ha="center", fontsize=8)
        figure.tight_layout(rect=(0, 0.035, 1, 0.96))
        for suffix in ("png", "pdf"):
            path = output_dir / f"pile_moment_envelopes.{suffix}"
            figure.savefig(path, dpi=180, bbox_inches="tight")
            artifacts.append(path)
    finally:
        plt.close(figure)
    settings = output_dir / "moment_envelope_settings.json"
    settings.write_text(json.dumps({
        "method": "end 1 sign reversed, end 2 unchanged; adjacent Mx and My averaged at each shared node at each recorded time",
        "envelopes": "separate signed minimum and maximum over all recorded times; no absolute values or artificial mirroring",
        "warning": "smoothed visualization, not a unique section force or interface equilibrium check",
        "raw_end_actions": "preserved unchanged in pile_*_end_forces.csv",
    }, indent=2), encoding="utf-8")
    artifacts.append(settings)
    return tuple(artifacts)


def generate_pile_moment_snapshot(results_root, output_dir, reference_time, peak_step):
    """Compare signed end moments at one time, without averaging joint jumps."""
    if not isinstance(peak_step, (int, np.integer)) or not 0 <= peak_step < len(reference_time):
        raise ValueError("Moment snapshot step is outside the recorded history")
    geometry, histories = read_pile_forces(results_root, reference_time)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    artifacts = []
    figure, axes = plt.subplots(1, 2, figsize=(9, 6), sharex=True, sharey=True)
    try:
        for axis, pile in zip(axes, PILE_NAMES):
            rows = []
            for element in sorted(geometry[pile], key=lambda item: item["ends_m"][0][2]):
                tag = element["tag"]
                z = np.asarray(element["ends_m"])[:, 2]
                # Opposite element faces have opposite resisting-action signs.
                # This orients the END values alike, not an interior section recovery.
                moment = histories[pile][tag][peak_step, [4, 10]] * [-1, 1] / 1000
                axis.plot(moment, z, "o-", color="#2b6cb0", markersize=3)
                rows.extend((reference_time[peak_step], tag, end + 1, z[end], moment[end])
                            for end in (0, 1))
            path = output_dir / f"{pile}_moment_snapshot.csv"
            np.savetxt(path, rows, delimiter=",", comments="",
                       header="time_s,element_tag,end,z_m,section_oriented_My_kNm")
            artifacts.append(path)
            axis.axvline(0, color="#888888", linewidth=0.8)
            axis.axhline(0, color="#555555", linestyle="--", linewidth=0.8)
            axis.set(title=pile.replace("_", " ").title(), xlabel="Signed end My (kN m)")
            axis.grid(alpha=0.25)
        axes[0].set_ylabel("Elevation z (m)")
        figure.suptitle(f"Pile end moments at {reference_time[peak_step]:.3f} s")
        figure.text(0.5, 0.01, "Common face convention; joint jumps retained, no section interpolation",
                    ha="center", fontsize=9)
        figure.tight_layout(rect=(0, 0.035, 1, 0.96))
        for suffix in ("png", "pdf"):
            path = output_dir / f"pile_moment_snapshot.{suffix}"
            figure.savefig(path, dpi=180, bbox_inches="tight")
            artifacts.append(path)
    finally:
        plt.close(figure)
    return tuple(artifacts)


def generate_pile_deformation_results(results_root, output_dir, reference_time, peak_step):
    """Select structural beam nodes even when soil nodes share coordinates."""
    import pyvista as pv

    geometry = read_pile_geometry(results_root)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    artifacts = []
    figure, axes = plt.subplots(1, 2, figsize=(9, 6), sharey=True)
    envelope_figure, envelope_axes = plt.subplots(1, 2, figsize=(9, 6), sharex=True, sharey=True)
    try:
        with fm.results.open(str(Path(results_root) / "bent/results" / RESPONSE_GLOB)) as results:
            if not np.allclose(results.times, reference_time, rtol=0, atol=1e-8):
                raise ValueError("Pile deformation times disagree with point histories")
            candidates = []
            for reader in results.readers:
                mesh = reader.mesh
                line_cells = np.flatnonzero(mesh.celltypes == pv.CellType.LINE)
                ids = sorted({point for cell in line_cells for point in mesh.get_cell(int(cell)).point_ids})
                candidates.append((reader, np.asarray(ids, dtype=int), mesh.points[ids]))
            for axis, envelope_axis, pile in zip(axes, envelope_axes, PILE_NAMES):
                points = np.unique(np.asarray([e["ends_m"] for e in geometry[pile]]).reshape(-1, 3), axis=0)
                points = points[np.argsort(points[:, 2])]
                curves = []
                for point in points:
                    copies = []
                    for reader, ids, coords in candidates:
                        hits = np.flatnonzero(np.linalg.norm(coords - point, axis=1) <= TOLERANCE)
                        for hit in hits:
                            values = np.asarray(reader.point_history("displacement", int(ids[hit])))
                            if values.shape != (len(reference_time), 3) or not np.isfinite(values).all():
                                raise ValueError(f"Invalid structural history at {point}")
                            copies.append(values)
                    if not copies:
                        raise ValueError(f"Missing structural pile node at {point}")
                    if any(not np.allclose(copies[0], copy, rtol=1e-5, atol=1e-9) for copy in copies[1:]):
                        raise ValueError(f"Partition copies disagree at pile node {point}")
                    curves.append(copies[0])
                displacement = np.stack(curves, axis=1) * 1000
                dx = displacement[:, :, 0]
                z = points[:, 2]
                snapshot = dx[peak_step]
                minimum_dx = np.min(dx, axis=0)
                maximum_dx = np.max(dx, axis=0)
                axis.plot(snapshot, z, label=f"dx at {reference_time[peak_step]:.3f} s")
                axis.plot(minimum_dx, z, "--", label="Min dx over time")
                axis.plot(maximum_dx, z, "--", label="Max dx over time")
                axis.axvline(0, color="#888888", linewidth=0.8)
                axis.axhline(0, color="#555555", linestyle="--", linewidth=0.8)
                axis.set(title=pile.replace("_", " ").title(), xlabel="Horizontal displacement (mm)")
                axis.grid(alpha=0.25)
                axis.legend(fontsize=8)
                path = output_dir / f"{pile}_deformation.csv"
                np.savetxt(path, np.column_stack((z, snapshot, minimum_dx, maximum_dx)), delimiter=",", comments="",
                           header=f"z_m,dx_at_{reference_time[peak_step]:.6f}s_mm,min_dx_mm,max_dx_mm")
                artifacts.append(path)
                minimum_displacement = np.min(displacement, axis=0)
                maximum_displacement = np.max(displacement, axis=0)
                for values, label, style, color in (
                        (minimum_displacement[:, 0], "Min ux", "--", "#2b6cb0"),
                        (maximum_displacement[:, 0], "Max ux", "-", "#2b6cb0"),
                        (minimum_displacement[:, 1], "Min uy", "--", "#d64545"),
                        (maximum_displacement[:, 1], "Max uy", "-", "#d64545")):
                    envelope_axis.plot(values, z, style, color=color, linewidth=1.7, label=label)
                envelope_axis.axvline(0, color="#888888", linewidth=0.8)
                envelope_axis.axhline(0, color="#555555", linestyle="--", linewidth=0.8)
                envelope_axis.set(title=pile.replace("_", " ").title(), xlabel="Displacement envelope (mm)")
                envelope_axis.grid(alpha=0.25)
                envelope_axis.legend(fontsize=8)
                path = output_dir / f"{pile}_displacement_envelope.csv"
                np.savetxt(path, np.column_stack((z, minimum_displacement, maximum_displacement)),
                           delimiter=",", comments="",
                           header="z_m,min_ux_mm,min_uy_mm,min_uz_mm,max_ux_mm,max_uy_mm,max_uz_mm")
                artifacts.append(path)
        axes[0].set_ylabel("Elevation z (m)")
        figure.suptitle("Pile deformation: common-time profile and nodal envelope")
        figure.tight_layout()
        for suffix in ("png", "pdf"):
            path = output_dir / f"pile_deformation_profiles.{suffix}"
            figure.savefig(path, dpi=180, bbox_inches="tight")
            artifacts.append(path)
        envelope_axes[0].set_ylabel("Elevation z (m)")
        envelope_figure.suptitle("Pile displacement envelopes: signed minimum and maximum")
        envelope_figure.tight_layout()
        for suffix in ("png", "pdf"):
            path = output_dir / f"pile_displacement_envelopes.{suffix}"
            envelope_figure.savefig(path, dpi=180, bbox_inches="tight")
            artifacts.append(path)
    finally:
        plt.close(figure)
        plt.close(envelope_figure)
    return tuple(artifacts)


def movie_timeline(times, frame_rate=24, slow_down=2.0, end_time=None):
    """Interpolate for presentation only; never modify response data."""
    times = np.asarray(times, dtype=float)
    if (times.ndim != 1 or len(times) < 2 or not np.isfinite(times).all()
            or np.any(np.diff(times) <= 0)):
        raise ValueError("Movie needs finite strictly increasing times")
    if (not np.isfinite(frame_rate) or not np.isfinite(slow_down)
            or frame_rate <= 0 or slow_down <= 0):
        raise ValueError("Movie frame rate and slow-down must be positive")
    stop = times[-1] if end_time is None else min(float(end_time), times[-1])
    if not np.isfinite(stop) or stop <= times[0]:
        raise ValueError("Movie end time must be finite and after the first recorded time")
    count = max(2, int(np.ceil((stop - times[0]) * slow_down * frame_rate)))
    targets = np.linspace(times[0], stop, count)
    right = np.searchsorted(times, targets, side="right").clip(1, len(times) - 1)
    left = right - 1
    weights = (targets - times[left]) / (times[right] - times[left])
    return targets, left, right, weights


def movie_soil_masks(celltypes, centers):
    """Start the front-right notch one soil cell in front of the right pile."""
    import pyvista as pv

    centers = np.asarray(centers)
    physical = ((np.asarray(celltypes) == pv.CellType.HEXAHEDRON)
                & (np.abs(centers[:, 0]) < 8 + TOLERANCE)
                & (np.abs(centers[:, 1]) < 3 + TOLERANCE)
                & (centers[:, 2] >= -8 - TOLERANCE) & (centers[:, 2] <= 0))
    removed = physical & (centers[:, 0] >= 2.0) & (centers[:, 1] < 0)
    return physical & ~removed, removed


def render_bent_movie(results_root, output_dir, frame_rate=48, slow_down=2.0,
                      deformation_scale=120.0, window_size=(1280, 720), end_time=2.0):
    """Perspective cutaway of homogeneous soil, bent and symbolic center mass."""
    import pyvista as pv

    if not np.isfinite(deformation_scale) or deformation_scale <= 0:
        raise ValueError("Movie deformation scale must be finite and positive")
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    movie = output_dir / "two_pile_bent.mp4"
    preview = output_dir / "two_pile_bent_preview.png"
    metadata = output_dir / "movie_settings.json"
    with fm.results.open(str(Path(results_root) / "bent/results" / RESPONSE_GLOB)) as results:
        times = results.times
        targets, left, right, weights = movie_timeline(times, frame_rate, slow_down, end_time)
        center = results.nearest_point(POINTS["cap_center"], tolerance=TOLERANCE)
        motion = np.asarray(results.point_history("displacement", center))
        if motion.shape != (len(times), 3) or not np.isfinite(motion).all():
            raise ValueError("Invalid center-mass displacement history")
        plotter = pv.Plotter(off_screen=True, window_size=window_size)
        try:
            animated = []
            beam_cells = soil_cells = removed_soil_cells = 0
            for reader in results.readers:
                mesh = reader.mesh.copy(deep=True)
                mesh.point_data["movie_id"] = np.arange(mesh.n_points)
                centers = mesh.cell_centers().points
                beam = mesh.celltypes == pv.CellType.LINE
                soil, removed = movie_soil_masks(mesh.celltypes, centers)
                removed_soil_cells += int(removed.sum())
                for mask, is_beam in ((soil, False), (beam, True)):
                    visible = mesh.extract_cells(np.flatnonzero(mask))
                    if not visible.n_cells:
                        continue
                    ids = np.asarray(visible.point_data["movie_id"], dtype=int)
                    animated.append((reader, visible, ids, visible.points.copy()))
                    if is_beam:
                        beam_cells += visible.n_cells
                        plotter.add_mesh(visible, color="#303030", line_width=5,
                                         render_lines_as_tubes=True)
                    else:
                        soil_cells += visible.n_cells
                        plotter.add_mesh(visible, color="#c7ab80", show_edges=True,
                                         edge_color="#55504a", line_width=0.5)
            if not beam_cells or not soil_cells:
                raise ValueError("Movie needs structural lines and physical soil cells")
            mass = pv.Sphere(radius=0.4, center=POINTS["cap_center"])
            original_mass = mass.points.copy()
            plotter.add_mesh(mass, color="#d7191c", smooth_shading=True)
            plotter.set_background("white")
            plotter.disable_parallel_projection()
            plotter.camera_position = [(21, -29, 16), (0, 0, -2), (0, 0, 1)]
            plotter.open_movie(str(movie), framerate=frame_rate, quality=7)
            shown_steps = np.flatnonzero(times <= targets[-1])
            peak_time = times[shown_steps[np.argmax(np.abs(motion[shown_steps, 0]))]]
            preview_index = int(np.argmin(np.abs(targets - peak_time)))
            for index, (time, a, b, weight) in enumerate(zip(targets, left, right, weights)):
                frames = {}
                for reader, visible, ids, points in animated:
                    if id(reader) not in frames:
                        first = np.asarray(reader.point_frame("displacement", int(a)))
                        second = np.asarray(reader.point_frame("displacement", int(b)))
                        if (first.shape != (reader.mesh.n_points, 3) or second.shape != first.shape
                                or not np.isfinite(first).all() or not np.isfinite(second).all()):
                            raise ValueError("Invalid movie displacement frame")
                        frames[id(reader)] = (1 - weight) * first + weight * second
                    visible.points = points + deformation_scale * frames[id(reader)][ids]
                mass.points = original_mass + deformation_scale * ((1 - weight) * motion[a] + weight * motion[b])
                plotter.add_text(f"Two-pile bent | {time:.3f} s", name="time", font_size=14, color="black")
                plotter.write_frame()
                if index == preview_index:
                    plotter.screenshot(str(preview))
        finally:
            plotter.close()
    metadata.write_text(json.dumps({
        "deformation_scale": deformation_scale, "parallel_projection": False,
        "soil_cutaway": "pile-aligned front-right notch: x >= 2.0 and y < 0 removed; PML hidden",
        "cut_corner_m": [2.0, 0.0],
        "soil": "homogeneous, one color", "mass_sphere_radius_m": 0.4,
        "retained_physical_soil_cells": soil_cells,
        "removed_physical_soil_cells": removed_soil_cells,
        "left_pile_visibility": "partly occluded by retained opaque soil",
        "mass_size_is_symbolic": True, "frame_rate": frame_rate,
        "frames": len(targets), "playback_seconds": len(targets) / frame_rate,
        "slow_down": slow_down, "interpolation": "linear, visualization only",
        "recorded_time_range_s": [float(times[0]), float(times[-1])],
        "rendered_time_range_s": [float(targets[0]), float(targets[-1])],
    }, indent=2), encoding="utf-8")
    return movie, preview, metadata


def read_point_response(results_root) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    """Read displacement histories; fail when files or points are missing."""
    results_dir = Path(results_root) / "bent" / "results"
    matches = sorted(results_dir.glob(RESPONSE_GLOB))
    if not matches:
        raise FileNotFoundError(
            f"No bent responses matching {RESPONSE_GLOB} below {results_dir}. "
            "Run the bent case first."
        )
    pattern = str(results_dir / RESPONSE_GLOB)
    responses: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    with fm.results.open(pattern) as results:
        if results.times is None:
            raise ValueError("Recorder output has no physical time values")
        time = np.asarray(results.times, dtype=float)
        if time.ndim != 1 or time.size < 2 or not np.all(np.isfinite(time)):
            raise ValueError("Recorder times must be a finite one-dimensional history")
        if np.any(np.diff(time) <= 0.0):
            raise ValueError("Recorder times must be strictly increasing")
        # A recorder may omit the initial or last solver step by one interval.
        if time[0] < -1.0e-9 or time[0] > RECORDER_DT + 1.0e-9:
            raise ValueError("Response does not begin near the start of the analysis")
        if not FINAL_TIME - RECORDER_DT - 1.0e-9 <= time[-1] <= FINAL_TIME + 1.0e-9:
            raise ValueError(f"Response ends at {time[-1]:.6f} s, expected {FINAL_TIME} s")
        for key, coords in POINTS.items():
            point = results.nearest_point(coords, tolerance=TOLERANCE)
            displacement = np.asarray(results.point_history("displacement", point), dtype=float)
            if displacement.ndim != 2 or displacement.shape != (time.size, 3):
                raise ValueError(f"{key}: expected displacement shape ({time.size}, 3)")
            if not np.all(np.isfinite(displacement)):
                raise ValueError(f"{key}: non-finite response values")
            responses[key] = (time.copy(), displacement.copy())
    return responses


def plot_bent_comparison(responses, output_file):
    """Plot x-displacement histories for the three probe points."""
    figure, axes = plt.subplots(3, 1, figsize=(9.0, 7.5), sharex=True)
    colors = {"left_head": "#2b6cb0", "right_head": "#d64545", "cap_center": "#2f855a"}
    for axis, key in zip(axes, ("left_head", "cap_center", "right_head")):
        time, displacement = responses[key]
        axis.plot(time, 1000.0 * displacement[:, 0], color=colors[key], linewidth=1.1)
        axis.set_title(POINT_LABELS[key])
        axis.set_ylabel("dx (mm)")
        axis.grid(True, linestyle="--", alpha=0.3)
    axes[-1].set_xlabel("Time (s)")
    figure.suptitle("Two-pile bent x-displacement histories")
    figure.tight_layout()
    figure.savefig(output_file, dpi=180, bbox_inches="tight")
    pdf_file = Path(output_file).with_suffix(".pdf")
    figure.savefig(pdf_file, bbox_inches="tight")
    plt.close(figure)
    return output_file, pdf_file


def generate_results(results_root, output_dir=None, *, profiles=False, forces=False) -> tuple[Path, ...]:
    """Write per-point CSVs, comparison plot, and a summary JSON."""
    responses = read_point_response(results_root)

    output_dir = Path(output_dir) if output_dir is not None else Path(results_root) / "post_processing"
    output_dir.mkdir(parents=True, exist_ok=True)
    artifacts: list[Path] = []
    summary: dict = {"final_time": FINAL_TIME, "tolerance": TOLERANCE, "points": {}}
    for key, (time, displacement) in responses.items():
        history_file = output_dir / f"{key}.csv"
        np.savetxt(
            history_file,
            np.column_stack((time, displacement)),
            delimiter=",",
            header="time_s,dx_m,dy_m,dz_m",
            comments="",
        )
        artifacts.append(history_file)
        summary["points"][key] = {
            "coords_m": [float(v) for v in POINTS[key]],
            "n_steps": int(len(time)),
            "end_time_s": float(time[-1]),
            "max_abs_dx_mm": float(np.max(np.abs(displacement[:, 0])) * 1000.0),
            "csv": history_file.name,
        }
    plot_png = output_dir / "bent_comparison.png"
    png, pdf = plot_bent_comparison(responses, plot_png)
    artifacts.extend([png, pdf])
    summary_file = output_dir / "summary.json"
    summary_file.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    artifacts.append(summary_file)
    time, center = responses["cap_center"]
    if profiles:
        artifacts.extend(generate_pile_deformation_results(
            results_root, output_dir, time, int(np.argmax(np.abs(center[:, 0]))),
        ))
    if forces:
        artifacts.extend(generate_pile_force_results(results_root, output_dir, time))
        artifacts.extend(generate_pile_moment_snapshot(
            results_root, output_dir, time, int(np.argmax(np.abs(center[:, 0]))),
        ))
    return tuple(artifacts)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("results_root", type=Path, help="Workflow build directory containing bent/results")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--profiles", action="store_true")
    parser.add_argument("--forces", action="store_true")
    parser.add_argument("--movie", action="store_true")
    args = parser.parse_args()
    output = args.output or args.results_root / "post_processing"
    for result in generate_results(args.results_root, output, profiles=args.profiles, forces=args.forces):
        print(f"Generated: {result.resolve()}")
    if args.movie:
        for result in render_bent_movie(args.results_root, output):
            print(f"Generated: {result.resolve()}")
