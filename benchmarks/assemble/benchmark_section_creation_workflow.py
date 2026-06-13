# =============================================================================
# Femora: Fast Efficient Meta-modeling for OpenSees-based Resilience Analysis
# Copyright 2026 Amin Pakzad and Pedro Arduino
# Developed at the UW Geotechnical Lab
# SPDX-License-Identifier: Apache-2.0
# =============================================================================

"""Benchmark AssemblySection creation using the normal Femora workflow.

This script creates a small set of touching mesh parts through the public
Femora APIs, then times only `fm.assembler.create_section(...)`.

Run from the repository root with the Femora debug environment:

    conda run -n femora_debug python benchmarks/assemble/benchmark_section_creation_workflow.py

Example larger run:

    conda run -n femora_debug python benchmarks/assemble/benchmark_section_creation_workflow.py \
        --parts 12 --cells-per-axis 30 --repeat 5
"""

from __future__ import annotations

import argparse
import time
from contextlib import contextmanager
from types import SimpleNamespace

import numpy as np
import pyvista as pv
from scipy.spatial import cKDTree
import importlib.util

if importlib.util.find_spec("numba") is not None:
    from numba import njit
    HAVE_NUMBA = True
else:
    HAVE_NUMBA = False

from femora.core.model import Model
from femora.core.assembler import Assembler, AssemblySection
from femora.components.partitioner.partitioner import PartitionerRegistry
from femora.constants import FEMORA_MAX_NDF
from femora.utils.progress import Progress

model = Model()


def reset_state() -> None:
    model.clear_model()


def build_workflow_meshparts(num_parts: int, cells_per_axis: int) -> list[str]:
    material = model.material.nd.elastic_isotropic(
        user_name="bench_material",
        E=20_000.0,
        nu=0.30,
        rho=1.9,
    )
    element = model.element.brick.std(
        ndof=3,
        material=material,
        b1=0.0,
        b2=0.0,
        b3=0.0,
        lumped=True,
    )

    names: list[str] = []
    y_min = 0.0
    y_max = float(cells_per_axis)
    z_min = 0.0
    z_max = float(cells_per_axis)

    for idx in range(num_parts):
        user_name = f"bench_part_{idx}"
        x_min = float(idx * cells_per_axis)
        x_max = float((idx + 1) * cells_per_axis)
        model.meshpart.volume.uniform_rectangular_grid(
            user_name=user_name,
            element=element,
            region=None,
            x_min=x_min,
            x_max=x_max,
            y_min=y_min,
            y_max=y_max,
            z_min=z_min,
            z_max=z_max,
            nx=cells_per_axis,
            ny=cells_per_axis,
            nz=cells_per_axis,
        )
        names.append(user_name)

    return names


def _ensure_ndf_array_demo(mesh: pv.UnstructuredGrid, default_ndf: int, element_manager) -> None:
    if "ndf" in mesh.point_data:
        return

    n_points = mesh.n_points
    if "ElementTag" not in mesh.cell_data:
        mesh.point_data["ndf"] = np.full(n_points, default_ndf, dtype=np.uint16)
        return

    ndf_values = np.full(n_points, default_ndf, dtype=np.uint16)
    element_tags = mesh.cell_data["ElementTag"]
    unique_tags = np.unique(element_tags)

    for tag in unique_tags:
        element = element_manager.get(int(tag))
        if element is None:
            continue
        ele_ndof = element.get_ndof()
        if ele_ndof == default_ndf:
            continue
        cell_indices = np.where(element_tags == tag)[0]
        for cell_idx in cell_indices:
            start = mesh.offset[cell_idx]
            end = mesh.offset[cell_idx + 1]
            pids = mesh.cell_connectivity[start:end]
            ndf_values[pids] = ele_ndof

    mesh.point_data["ndf"] = ndf_values


def _prepare_meshpart_for_demo(meshpart) -> pv.UnstructuredGrid:
    mesh = meshpart.mesh.copy()

    if meshpart.element:
        ndf = meshpart.element._ndof
        mat_tag = meshpart.element.get_material_tag()
        ele_tag = meshpart.element.tag
        section_tag = meshpart.element.get_section_tag()
    elif hasattr(meshpart, "ndof"):
        ndf = meshpart.ndof
        mat_tag = getattr(meshpart, "material_tag", 0)
        ele_tag = getattr(meshpart, "element_tag", 0)
        section_tag = getattr(meshpart, "section_tag", 0)
    else:
        ndf = FEMORA_MAX_NDF
        mat_tag = getattr(meshpart, "material_tag", 0)
        ele_tag = getattr(meshpart, "element_tag", 0)
        section_tag = getattr(meshpart, "section_tag", 0)

    region_tag = meshpart.region.tag
    mesh_tag = meshpart.tag

    n_cells = mesh.n_cells
    n_points = mesh.n_points

    if "Mass" not in mesh.point_data:
        mesh.point_data["Mass"] = np.zeros((n_points, FEMORA_MAX_NDF), dtype=np.float32)
    if "ElementTag" not in mesh.cell_data:
        mesh.cell_data["ElementTag"] = np.full(n_cells, ele_tag, dtype=np.uint16)
    if "MaterialTag" not in mesh.cell_data:
        mesh.cell_data["MaterialTag"] = np.full(n_cells, mat_tag, dtype=np.uint16)
    if "SectionTag" not in mesh.cell_data:
        mesh.cell_data["SectionTag"] = np.full(n_cells, section_tag, dtype=np.uint16)

    element_manager = meshpart._owner._mesh_maker.element if meshpart._owner else None
    if element_manager is not None:
        _ensure_ndf_array_demo(mesh, ndf, element_manager)
    else:
        mesh.point_data["ndf"] = np.full(mesh.n_points, ndf, dtype=np.uint16)

    mesh.cell_data["Region"] = np.full(n_cells, region_tag, dtype=np.uint16)
    mesh.cell_data["MeshPartTag_celldata"] = np.full(n_cells, mesh_tag, dtype=np.uint16)
    mesh.point_data["MeshPartTag_pointdata"] = np.full(n_points, mesh_tag, dtype=np.uint16)
    return mesh


def _concatenate_prepared_meshes(meshes: list[pv.UnstructuredGrid]) -> pv.UnstructuredGrid:
    if not meshes:
        raise ValueError("No meshes to concatenate")

    point_arrays = list(meshes[0].point_data.keys())
    cell_arrays = list(meshes[0].cell_data.keys())

    total_points = sum(mesh.n_points for mesh in meshes)
    total_cells = sum(mesh.n_cells for mesh in meshes)
    total_connectivity = sum(np.asarray(mesh.cell_connectivity).shape[0] for mesh in meshes)

    points = np.empty((total_points, 3), dtype=np.float64)
    celltypes = np.empty(total_cells, dtype=np.uint8)
    connectivity = np.empty(total_connectivity, dtype=np.int64)
    offsets = np.empty(total_cells + 1, dtype=np.int64)
    offsets[0] = 0

    point_data = {}
    for name in point_arrays:
        arr = np.asarray(meshes[0].point_data[name])
        shape = (total_points,) + arr.shape[1:]
        point_data[name] = np.empty(shape, dtype=arr.dtype)

    cell_data = {}
    for name in cell_arrays:
        arr = np.asarray(meshes[0].cell_data[name])
        shape = (total_cells,) + arr.shape[1:]
        cell_data[name] = np.empty(shape, dtype=arr.dtype)

    point_cursor = 0
    cell_cursor = 0
    conn_cursor = 0

    for mesh in meshes:
        n_points = mesh.n_points
        n_cells = mesh.n_cells
        conn = np.asarray(mesh.cell_connectivity, dtype=np.int64)
        offs = np.asarray(mesh.offset, dtype=np.int64)

        points[point_cursor:point_cursor + n_points] = np.asarray(mesh.points, dtype=np.float64)
        celltypes[cell_cursor:cell_cursor + n_cells] = np.asarray(mesh.celltypes, dtype=np.uint8)
        connectivity[conn_cursor:conn_cursor + conn.shape[0]] = conn + point_cursor
        offsets[cell_cursor + 1:cell_cursor + n_cells + 1] = offs[1:] + conn_cursor

        for name in point_arrays:
            point_data[name][point_cursor:point_cursor + n_points] = np.asarray(mesh.point_data[name])
        for name in cell_arrays:
            cell_data[name][cell_cursor:cell_cursor + n_cells] = np.asarray(mesh.cell_data[name])

        point_cursor += n_points
        cell_cursor += n_cells
        conn_cursor += conn.shape[0]

    cell_array = pv.CellArray.from_arrays(offsets, connectivity)
    combined = pv.UnstructuredGrid(cell_array.cells, celltypes, points)
    for name, arr in point_data.items():
        combined.point_data[name] = arr
    for name, arr in cell_data.items():
        combined.cell_data[name] = arr
    return combined


def femora_assemble_demo(
    meshpart_names: list[str],
    *,
    merge_points: bool,
    tolerance: float,
    mass_merging: str = "sum",
    num_partitions: int = 1,
    partition_algorithm: str = "kd-tree",
):
    meshpart_manager = model.meshpart
    prepared_meshes = [
        _prepare_meshpart_for_demo(meshpart_manager.get(name)) for name in meshpart_names
    ]
    mesh = _concatenate_prepared_meshes(prepared_meshes)

    if merge_points:
        mass = None
        if mass_merging == "sum":
            mass = np.asarray(mesh.point_data.pop("Mass"), dtype=np.float32)

        mesh = manual_clean_demo_jit(
            mesh,
            tolerance=tolerance,
            produce_merge_map=True,
            average_point_data=True,
        )
        mesh.point_data["ndf"] = mesh.point_data["ndf"].astype(np.uint16, copy=False)
        mesh.point_data["MeshPartTag_pointdata"] = mesh.point_data["MeshPartTag_pointdata"].astype(np.uint16, copy=False)

        if mass_merging == "sum":
            merge_map = np.asarray(mesh.field_data["PointMergeMap"]).reshape(-1)
            Mass = np.zeros((mesh.number_of_points, FEMORA_MAX_NDF), dtype=np.float32)
            if mass is not None:
                nonzero_rows = np.any(mass != 0.0, axis=1)
                if np.any(nonzero_rows):
                    np.add.at(Mass, merge_map[nonzero_rows], mass[nonzero_rows])
            mesh.point_data["Mass"] = Mass

        del mesh.field_data["PointMergeMap"]

    mesh.cell_data["Core"] = np.zeros(mesh.n_cells, dtype=int)
    if num_partitions > 1:
        core_ids = PartitionerRegistry.partition(
            mesh,
            num_partitions,
            partitioner=partition_algorithm,
        )
        mesh.cell_data["Core"] = core_ids.astype(int)

    return SimpleNamespace(mesh=mesh)


def manual_clean_demo(
    mesh: pv.UnstructuredGrid,
    tolerance: float,
    *,
    produce_merge_map: bool = True,
    average_point_data: bool = True,
) -> pv.UnstructuredGrid:
    """Experimental manual clean for benchmark comparison only.

    This uses tolerance-quantized grouping on coordinates together with `ndf`.
    It is intended only as a performance demo in the benchmark file.
    """
    points = np.asarray(mesh.points)
    ndf = np.asarray(mesh.point_data["ndf"]).reshape(-1, 1)

    if tolerance <= 0.0:
        raise ValueError("manual_clean_demo requires a positive tolerance")

    coord_keys = np.rint(points / tolerance).astype(np.int64)
    group_keys = np.hstack((coord_keys, ndf.astype(np.int64, copy=False)))

    _, merge_map, counts = np.unique(
        group_keys,
        axis=0,
        return_inverse=True,
        return_counts=True,
    )
    num_new_points = int(counts.shape[0])

    if average_point_data:
        new_points = np.zeros((num_new_points, 3), dtype=np.float64)
        np.add.at(new_points, merge_map, points)
        new_points /= counts[:, None]
    else:
        first_indices = np.full(num_new_points, -1, dtype=np.int64)
        for old_idx, new_idx in enumerate(merge_map):
            if first_indices[new_idx] == -1:
                first_indices[new_idx] = old_idx
        new_points = points[first_indices].copy()

    new_connectivity = merge_map[np.asarray(mesh.cell_connectivity)]
    cell_array = pv.CellArray.from_arrays(np.asarray(mesh.offset), new_connectivity)
    cleaned = pv.UnstructuredGrid(cell_array.cells, np.asarray(mesh.celltypes), new_points)

    for name, array in mesh.cell_data.items():
        cleaned.cell_data[name] = np.asarray(array).copy()

    for name, array in mesh.point_data.items():
        arr = np.asarray(array)
        if average_point_data:
            if arr.ndim == 1:
                reduced = np.zeros(num_new_points, dtype=np.float64)
                np.add.at(reduced, merge_map, arr.astype(np.float64, copy=False))
                reduced /= counts
            else:
                reduced = np.zeros((num_new_points, arr.shape[1]), dtype=np.float64)
                np.add.at(reduced, merge_map, arr.astype(np.float64, copy=False))
                reduced /= counts[:, None]
        else:
            first_indices = np.full(num_new_points, -1, dtype=np.int64)
            for old_idx, new_idx in enumerate(merge_map):
                if first_indices[new_idx] == -1:
                    first_indices[new_idx] = old_idx
            reduced = arr[first_indices].copy()

        if arr.dtype.kind in "iu":
            reduced = np.rint(reduced).astype(arr.dtype, copy=False)
        else:
            reduced = reduced.astype(arr.dtype, copy=False)
        cleaned.point_data[name] = reduced

    if produce_merge_map:
        cleaned.field_data["PointMergeMap"] = merge_map.astype(np.int64, copy=False)

    return cleaned


if HAVE_NUMBA:
    @njit(cache=True)
    def _group_sorted_keys_jit(sorted_keys):
        n = sorted_keys.shape[0]
        group_ids = np.empty(n, dtype=np.int64)
        if n == 0:
            return group_ids, np.zeros(0, dtype=np.int64), 0

        current_group = 0
        group_ids[0] = 0
        for i in range(1, n):
            same = True
            for j in range(sorted_keys.shape[1]):
                if sorted_keys[i, j] != sorted_keys[i - 1, j]:
                    same = False
                    break
            if not same:
                current_group += 1
            group_ids[i] = current_group

        num_groups = current_group + 1
        counts = np.zeros(num_groups, dtype=np.int64)
        for i in range(n):
            counts[group_ids[i]] += 1

        return group_ids, counts, num_groups


    @njit(cache=True)
    def _accumulate_points_sorted_jit(sorted_points, group_ids, num_groups):
        reduced = np.zeros((num_groups, sorted_points.shape[1]), dtype=np.float64)
        for i in range(sorted_points.shape[0]):
            gid = group_ids[i]
            for j in range(sorted_points.shape[1]):
                reduced[gid, j] += sorted_points[i, j]
        return reduced


    @njit(cache=True)
    def _accumulate_1d_sorted_jit(sorted_values, group_ids, num_groups):
        reduced = np.zeros(num_groups, dtype=np.float64)
        for i in range(sorted_values.shape[0]):
            reduced[group_ids[i]] += sorted_values[i]
        return reduced


    @njit(cache=True)
    def _accumulate_2d_sorted_jit(sorted_values, group_ids, num_groups):
        reduced = np.zeros((num_groups, sorted_values.shape[1]), dtype=np.float64)
        for i in range(sorted_values.shape[0]):
            gid = group_ids[i]
            for j in range(sorted_values.shape[1]):
                reduced[gid, j] += sorted_values[i, j]
        return reduced


    @njit(cache=True)
    def _first_indices_sorted_jit(group_ids, order, num_groups):
        first_indices = np.full(num_groups, -1, dtype=np.int64)
        for i in range(group_ids.shape[0]):
            gid = group_ids[i]
            if first_indices[gid] == -1:
                first_indices[gid] = order[i]
        return first_indices


    _NUMBA_WARMED = False


def _warm_manual_jit() -> None:
    global _NUMBA_WARMED
    if not HAVE_NUMBA or _NUMBA_WARMED:
        return

    dummy_keys = np.zeros((1, 4), dtype=np.int64)
    dummy_points = np.zeros((1, 3), dtype=np.float64)
    group_ids, counts, num_groups = _group_sorted_keys_jit(dummy_keys)
    _accumulate_points_sorted_jit(dummy_points, group_ids, num_groups)
    _accumulate_1d_sorted_jit(np.zeros(1, dtype=np.float64), group_ids, num_groups)
    _accumulate_2d_sorted_jit(np.zeros((1, 2), dtype=np.float64), group_ids, num_groups)
    _first_indices_sorted_jit(group_ids, np.zeros(1, dtype=np.int64), num_groups)
    _NUMBA_WARMED = True


def manual_clean_demo_jit(
    mesh: pv.UnstructuredGrid,
    tolerance: float,
    *,
    produce_merge_map: bool = True,
    average_point_data: bool = True,
) -> pv.UnstructuredGrid:
    """Experimental manual clean using sort + numba kernels."""
    if not HAVE_NUMBA:
        raise RuntimeError("manual_clean_demo_jit requires numba")
    if tolerance <= 0.0:
        raise ValueError("manual_clean_demo_jit requires a positive tolerance")

    _warm_manual_jit()

    points = np.asarray(mesh.points, dtype=np.float64)
    ndf = np.asarray(mesh.point_data["ndf"], dtype=np.int64).reshape(-1, 1)
    coord_keys = np.rint(points / tolerance).astype(np.int64)
    group_keys = np.hstack((coord_keys, ndf))

    order = np.lexsort((
        group_keys[:, 3],
        group_keys[:, 2],
        group_keys[:, 1],
        group_keys[:, 0],
    ))
    sorted_keys = group_keys[order]
    group_ids_sorted, counts, num_groups = _group_sorted_keys_jit(sorted_keys)

    merge_map = np.empty(points.shape[0], dtype=np.int64)
    merge_map[order] = group_ids_sorted

    sorted_points = points[order]
    if average_point_data:
        new_points = _accumulate_points_sorted_jit(sorted_points, group_ids_sorted, num_groups)
        new_points /= counts[:, None]
    else:
        first_indices = _first_indices_sorted_jit(group_ids_sorted, order.astype(np.int64), num_groups)
        new_points = points[first_indices].copy()

    new_connectivity = merge_map[np.asarray(mesh.cell_connectivity)]
    cell_array = pv.CellArray.from_arrays(np.asarray(mesh.offset), new_connectivity)
    cleaned = pv.UnstructuredGrid(cell_array.cells, np.asarray(mesh.celltypes), new_points)

    for name, array in mesh.cell_data.items():
        cleaned.cell_data[name] = np.asarray(array).copy()

    if not average_point_data:
        first_indices = _first_indices_sorted_jit(group_ids_sorted, order.astype(np.int64), num_groups)

    for name, array in mesh.point_data.items():
        arr = np.asarray(array)
        sorted_arr = arr[order]
        if average_point_data:
            if arr.ndim == 1:
                reduced = _accumulate_1d_sorted_jit(sorted_arr.astype(np.float64, copy=False), group_ids_sorted, num_groups)
                reduced /= counts
            else:
                reduced = _accumulate_2d_sorted_jit(sorted_arr.astype(np.float64, copy=False), group_ids_sorted, num_groups)
                reduced /= counts[:, None]
        else:
            reduced = arr[first_indices].copy()

        if arr.dtype.kind in "iu":
            reduced = np.rint(reduced).astype(arr.dtype, copy=False)
        else:
            reduced = reduced.astype(arr.dtype, copy=False)
        cleaned.point_data[name] = reduced

    if produce_merge_map:
        cleaned.field_data["PointMergeMap"] = merge_map.astype(np.int64, copy=False)

    return cleaned


@contextmanager
def profile_merge_breakdown():
    original = AssemblySection._assemble_mesh
    original_snap_points = AssemblySection._snap_points
    stats = {
        "snap_time": 0.0,
        "snap_tree_time": 0.0,
        "snap_query_time": 0.0,
        "snap_assign_time": 0.0,
        "clean_time": 0.0,
        "mass_time": 0.0,
        "snap_calls": 0,
        "clean_calls": 0,
        "mass_calls": 0,
    }

    def instrumented_assemble_mesh(self, progress_callback=None):
        if progress_callback is None:
            assembler = self._meshpart_manager._mesh_maker.assembler

            def progress_callback(v, msg=""):
                Progress.callback(
                    v,
                    msg,
                    desc=f"Assembly Section: {len(assembler._assembly_sections) + 1}",
                )

        first_meshpart = self.meshparts_list[0]
        first_mesh = first_meshpart.mesh.copy()

        ndf = 0
        if first_meshpart.element:
            ndf = first_meshpart.element._ndof
            matTag = first_meshpart.element.get_material_tag()
            EleTag = first_meshpart.element.tag
            sectionTag = first_meshpart.element.get_section_tag()
        elif hasattr(first_meshpart, "ndof"):
            ndf = first_meshpart.ndof
            matTag = getattr(first_meshpart, "material_tag", 0)
            EleTag = getattr(first_meshpart, "element_tag", 0)
            sectionTag = getattr(first_meshpart, "section_tag", 0)
        else:
            ndf = FEMORA_MAX_NDF
            matTag = getattr(first_meshpart, "material_tag", 0)
            EleTag = getattr(first_meshpart, "element_tag", 0)
            sectionTag = getattr(first_meshpart, "section_tag", 0)

        regionTag = first_meshpart.region.tag
        meshTag = first_meshpart.tag

        n_cells = first_mesh.n_cells
        n_points = first_mesh.n_points

        if "Mass" not in first_mesh.point_data:
            first_mesh.point_data["Mass"] = np.zeros((n_points, FEMORA_MAX_NDF), dtype=np.float32)

        if "ElementTag" not in first_mesh.cell_data:
            first_mesh.cell_data["ElementTag"] = np.full(n_cells, EleTag, dtype=np.uint16)
        if "MaterialTag" not in first_mesh.cell_data:
            first_mesh.cell_data["MaterialTag"] = np.full(n_cells, matTag, dtype=np.uint16)
        if "SectionTag" not in first_mesh.cell_data:
            first_mesh.cell_data["SectionTag"] = np.full(n_cells, sectionTag, dtype=np.uint16)

        self._ensure_ndf_array(first_mesh, ndf)

        first_mesh.cell_data["Region"] = np.full(n_cells, regionTag, dtype=np.uint16)
        first_mesh.cell_data["MeshPartTag_celldata"] = np.full(n_cells, meshTag, dtype=np.uint16)
        first_mesh.point_data["MeshPartTag_pointdata"] = np.full(n_points, meshTag, dtype=np.uint16)

        n_sections = len(self.meshparts_list)
        perc = 1 / n_sections * 100
        progress_callback(perc, f"merged meshpart {1}/{n_sections}")
        self.mesh = pv.MultiBlock([first_mesh])
        for idx, meshpart in enumerate(self.meshparts_list[1:], start=2):
            second_mesh = meshpart.mesh.copy()

            ndf = 0
            if meshpart.element:
                ndf = meshpart.element._ndof
                matTag = meshpart.element.get_material_tag()
                EleTag = meshpart.element.tag
                sectionTag = meshpart.element.get_section_tag()
            elif hasattr(meshpart, "ndof"):
                ndf = meshpart.ndof
                matTag = getattr(meshpart, "material_tag", 0)
                EleTag = getattr(meshpart, "element_tag", 0)
                sectionTag = getattr(meshpart, "section_tag", 0)
            else:
                ndf = FEMORA_MAX_NDF
                matTag = getattr(meshpart, "material_tag", 0)
                EleTag = getattr(meshpart, "element_tag", 0)
                sectionTag = getattr(meshpart, "section_tag", 0)

            regionTag = meshpart.region.tag
            meshTag = meshpart.tag
            n_cells_second = second_mesh.n_cells
            n_points_second = second_mesh.n_points
            if "Mass" not in second_mesh.point_data:
                second_mesh.point_data["Mass"] = np.zeros((n_points_second, FEMORA_MAX_NDF), dtype=np.float32)
            if "ElementTag" not in second_mesh.cell_data:
                second_mesh.cell_data["ElementTag"] = np.full(n_cells_second, EleTag, dtype=np.uint16)
            if "MaterialTag" not in second_mesh.cell_data:
                second_mesh.cell_data["MaterialTag"] = np.full(n_cells_second, matTag, dtype=np.uint16)
            if "SectionTag" not in second_mesh.cell_data:
                second_mesh.cell_data["SectionTag"] = np.full(n_cells_second, sectionTag, dtype=np.uint16)

            self._ensure_ndf_array(second_mesh, ndf)

            second_mesh.cell_data["Region"] = np.full(n_cells_second, regionTag, dtype=np.uint16)
            second_mesh.cell_data["MeshPartTag_celldata"] = np.full(n_cells_second, meshTag, dtype=np.uint16)
            second_mesh.point_data["MeshPartTag_pointdata"] = np.full(n_points_second, meshTag, dtype=np.uint16)
            self.mesh.append(second_mesh)
            perc = idx / n_sections * 100
            progress_callback(perc, f"merged meshpart {idx}/{n_sections}")

        self.mesh = self.mesh.combine(
            merge_points=False,
            tolerance=1e-5,
        )
        if self.merge_points:
            mass = None
            if self.mass_merging == "sum":
                mass = np.asarray(self.mesh.point_data.pop("Mass"), dtype=np.float32)

            t_snap_0 = time.perf_counter()
            points = self._snap_points(self.mesh.points, tol=self.tolerance)
            stats["snap_time"] += time.perf_counter() - t_snap_0
            stats["snap_calls"] += 1
            self.mesh.points = points

            t_clean_0 = time.perf_counter()
            self.mesh = self.mesh.clean(
                tolerance=self.tolerance,
                remove_unused_points=False,
                produce_merge_map=True,
                average_point_data=True,
                merging_array_name="ndf",
                progress_bar=False,
            )
            stats["clean_time"] += time.perf_counter() - t_clean_0
            stats["clean_calls"] += 1

            self.mesh.point_data["ndf"] = self.mesh.point_data["ndf"].astype(np.uint16, copy=False)
            self.mesh.point_data["MeshPartTag_pointdata"] = self.mesh.point_data["MeshPartTag_pointdata"].astype(np.uint16, copy=False)

            if self.mass_merging == "sum":
                t_mass_0 = time.perf_counter()
                merge_map = np.asarray(self.mesh.field_data["PointMergeMap"]).reshape(-1)
                Mass = np.zeros((self.mesh.number_of_points, FEMORA_MAX_NDF), dtype=np.float32)
                if mass is not None:
                    nonzero_rows = np.any(mass != 0.0, axis=1)
                    if np.any(nonzero_rows):
                        np.add.at(Mass, merge_map[nonzero_rows], mass[nonzero_rows])
                self.mesh.point_data["Mass"] = Mass
                stats["mass_time"] += time.perf_counter() - t_mass_0
                stats["mass_calls"] += 1

            del self.mesh.field_data["PointMergeMap"]

        self.mesh.cell_data["Core"] = np.zeros(self.mesh.n_cells, dtype=int)
        if self.num_partitions > 1:
            core_ids = PartitionerRegistry.partition(
                self.mesh,
                self.num_partitions,
                partitioner=self.partition_algorithm,
            )
            self.mesh.cell_data["Core"] = core_ids.astype(int)

    def profiled_snap_points(points, tol=1e-6):
        points = np.ascontiguousarray(points)

        t_tree_0 = time.perf_counter()
        tree = cKDTree(points)
        stats["snap_tree_time"] += time.perf_counter() - t_tree_0

        t_query_0 = time.perf_counter()
        groups = tree.query_ball_tree(tree, tol)
        stats["snap_query_time"] += time.perf_counter() - t_query_0

        t_assign_0 = time.perf_counter()
        visited = np.zeros(len(points), dtype=bool)
        snapped = points.copy()

        for i in range(len(points)):
            if visited[i]:
                continue
            cluster = np.asarray(groups[i], dtype=np.intp)
            rep = points[i]
            snapped[cluster] = rep
            visited[cluster] = True

        stats["snap_assign_time"] += time.perf_counter() - t_assign_0
        return snapped

    AssemblySection._assemble_mesh = instrumented_assemble_mesh
    AssemblySection._snap_points = staticmethod(profiled_snap_points)
    try:
        yield stats
    finally:
        AssemblySection._assemble_mesh = original
        AssemblySection._snap_points = original_snap_points


def run_case(
    num_parts: int,
    cells_per_axis: int,
    repeat: int,
    merge_points: bool,
    merge_backend: str,
) -> dict[str, float | int | bool | str]:
    times: list[float] = []
    snap_times: list[float] = []
    snap_tree_times: list[float] = []
    snap_query_times: list[float] = []
    snap_assign_times: list[float] = []
    clean_times: list[float] = []
    mass_times: list[float] = []
    snap_calls: list[int] = []
    clean_calls: list[int] = []
    mass_calls: list[int] = []
    out_cells = -1
    out_points = -1

    for _ in range(repeat):
        reset_state()
        part_names = build_workflow_meshparts(num_parts=num_parts, cells_per_axis=cells_per_axis)

        if merge_backend == "vtk":
            with profile_merge_breakdown() as merge_stats:
                t0 = time.perf_counter()
                section = model.assembler.create_section(
                    meshparts=part_names,
                    num_partitions=1,
                    merge_points=merge_points,
                    progress_callback=lambda _value, _msg="": None,
                )
                t1 = time.perf_counter()
        elif merge_backend in {"manual", "manual_jit"}:
            t0 = time.perf_counter()
                section = model.assembler.create_section(
                meshparts=part_names,
                num_partitions=1,
                merge_points=False,
                progress_callback=lambda _value, _msg="": None,
            )
            if merge_points:
                t_clean_0 = time.perf_counter()
                if merge_backend == "manual":
                    section.mesh = manual_clean_demo(
                        section.mesh,
                        tolerance=section.tolerance,
                        produce_merge_map=True,
                        average_point_data=True,
                    )
                else:
                    section.mesh = manual_clean_demo_jit(
                        section.mesh,
                        tolerance=section.tolerance,
                        produce_merge_map=True,
                        average_point_data=True,
                    )
                merge_stats = {
                    "snap_time": 0.0,
                    "snap_tree_time": 0.0,
                    "snap_query_time": 0.0,
                    "snap_assign_time": 0.0,
                    "clean_time": time.perf_counter() - t_clean_0,
                    "mass_time": 0.0,
                    "snap_calls": 0,
                    "clean_calls": 1,
                    "mass_calls": 0,
                }
            else:
                merge_stats = {
                    "snap_time": 0.0,
                    "snap_tree_time": 0.0,
                    "snap_query_time": 0.0,
                    "snap_assign_time": 0.0,
                    "clean_time": 0.0,
                    "mass_time": 0.0,
                    "snap_calls": 0,
                    "clean_calls": 0,
                    "mass_calls": 0,
                }
            t1 = time.perf_counter()
        elif merge_backend == "femora_demo":
            t0 = time.perf_counter()
            section = femora_assemble_demo(
                part_names,
                merge_points=merge_points,
                tolerance=1e-5,
                mass_merging="sum",
                num_partitions=1,
                partition_algorithm="kd-tree",
            )
            merge_stats = {
                "snap_time": 0.0,
                "snap_tree_time": 0.0,
                "snap_query_time": 0.0,
                "snap_assign_time": 0.0,
                "clean_time": time.perf_counter() - t0 if merge_points else 0.0,
                "mass_time": 0.0,
                "snap_calls": 0,
                "clean_calls": 1 if merge_points else 0,
                "mass_calls": 1 if merge_points else 0,
            }
            t1 = time.perf_counter()
        else:
            raise ValueError(f"Unsupported merge backend: {merge_backend}")

        if section.mesh is None:
            raise RuntimeError("AssemblySection benchmark produced no mesh")

        out_cells = int(section.mesh.n_cells)
        out_points = int(section.mesh.n_points)
        times.append(t1 - t0)
        snap_times.append(float(merge_stats["snap_time"]))
        snap_tree_times.append(float(merge_stats["snap_tree_time"]))
        snap_query_times.append(float(merge_stats["snap_query_time"]))
        snap_assign_times.append(float(merge_stats["snap_assign_time"]))
        clean_times.append(float(merge_stats["clean_time"]))
        mass_times.append(float(merge_stats["mass_time"]))
        snap_calls.append(int(merge_stats["snap_calls"]))
        clean_calls.append(int(merge_stats["clean_calls"]))
        mass_calls.append(int(merge_stats["mass_calls"]))

    best = float(min(times))
    median = float(np.median(times))
    snap_best = float(min(snap_times))
    snap_tree_best = float(min(snap_tree_times))
    snap_query_best = float(min(snap_query_times))
    snap_assign_best = float(min(snap_assign_times))
    clean_best = float(min(clean_times))
    mass_best = float(min(mass_times))
    merge_profile_best = snap_best + clean_best + mass_best
    throughput = (float(out_cells) / best / 1e6) if best > 0 else float("inf")
    return {
        "merge_backend": merge_backend,
        "merge_points": merge_points,
        "best": best,
        "median": median,
        "snap_best": snap_best,
        "snap_share_pct_best": (100.0 * snap_best / best) if best > 0 else 0.0,
        "snap_tree_best": snap_tree_best,
        "snap_tree_share_pct_best": (100.0 * snap_tree_best / best) if best > 0 else 0.0,
        "snap_query_best": snap_query_best,
        "snap_query_share_pct_best": (100.0 * snap_query_best / best) if best > 0 else 0.0,
        "snap_assign_best": snap_assign_best,
        "snap_assign_share_pct_best": (100.0 * snap_assign_best / best) if best > 0 else 0.0,
        "clean_best": clean_best,
        "clean_share_pct_best": (100.0 * clean_best / best) if best > 0 else 0.0,
        "mass_best": mass_best,
        "mass_share_pct_best": (100.0 * mass_best / best) if best > 0 else 0.0,
        "merge_profile_best": merge_profile_best,
        "merge_profile_share_pct_best": (100.0 * merge_profile_best / best) if best > 0 else 0.0,
        "snap_calls": max(snap_calls) if snap_calls else 0,
        "clean_calls": max(clean_calls) if clean_calls else 0,
        "mass_calls": max(mass_calls) if mass_calls else 0,
        "out_cells": out_cells,
        "out_points": out_points,
        "throughput_mcells_per_s": throughput,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Benchmark workflow-style AssemblySection creation.")
    parser.add_argument("--parts", type=int, default=8, help="Number of touching Femora mesh parts.")
    parser.add_argument("--cells-per-axis", type=int, default=20, help="Cells per axis in each mesh part.")
    parser.add_argument("--repeat", type=int, default=3, help="Number of repeats for each benchmark case.")
    parser.add_argument(
        "--merge-backend",
        choices=["vtk", "manual", "manual_jit", "femora_demo", "both", "all"],
        default="vtk",
        help="Merge backend to benchmark when merge_points=True.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    num_parts = max(2, int(args.parts))
    cells_per_axis = max(1, int(args.cells_per_axis))
    repeat = max(1, int(args.repeat))
    if args.merge_backend == "both":
        backends = ["vtk", "manual"]
    elif args.merge_backend == "all":
        backends = ["vtk", "manual", "manual_jit", "femora_demo"]
    else:
        backends = [args.merge_backend]

    print("=" * 72)
    print(
        f"Workflow AssemblySection benchmark parts={num_parts} "
        f"cells_per_axis={cells_per_axis} repeat={repeat}"
    )
    print("Mesh parts are created through standard Femora APIs.")
    print("Timing includes create_section(...) only, not mesh-part generation.")
    if args.merge_backend != "vtk":
        print("Manual backend is experimental and intended for benchmark comparison only.")
    if "manual_jit" in backends and not HAVE_NUMBA:
        raise RuntimeError("manual_jit backend requested, but numba is not available")

    try:
        for merge_backend in backends:
            for merge_points in (False, True):
                result = run_case(
                    num_parts=num_parts,
                    cells_per_axis=cells_per_axis,
                    repeat=repeat,
                    merge_points=merge_points,
                    merge_backend=merge_backend,
                )
                print(
                    f"backend={result['merge_backend']:6s}  "
                    f"merge_points={str(result['merge_points']):5s}  "
                    f"best={result['best']:8.3f}s  "
                    f"median={result['median']:8.3f}s  "
                    f"snap_best={result['snap_best']:8.3f}s  "
                    f"snap_share={result['snap_share_pct_best']:6.1f}%  "
                    f"snap_tree={result['snap_tree_best']:8.3f}s  "
                    f"tree_share={result['snap_tree_share_pct_best']:6.1f}%  "
                    f"snap_query={result['snap_query_best']:8.3f}s  "
                    f"query_share={result['snap_query_share_pct_best']:6.1f}%  "
                    f"snap_assign={result['snap_assign_best']:8.3f}s  "
                    f"assign_share={result['snap_assign_share_pct_best']:6.1f}%  "
                    f"clean_best={result['clean_best']:8.3f}s  "
                    f"clean_share={result['clean_share_pct_best']:6.1f}%  "
                    f"mass_best={result['mass_best']:8.3f}s  "
                    f"mass_share={result['mass_share_pct_best']:6.1f}%  "
                    f"merge_profile={result['merge_profile_share_pct_best']:6.1f}%  "
                    f"out_cells={result['out_cells']:8d}  "
                    f"out_points={result['out_points']:8d}  "
                    f"throughput={result['throughput_mcells_per_s']:6.2f} Mcells/s"
                )
    finally:
        reset_state()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
