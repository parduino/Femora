# =============================================================================
# Femora: Fast Efficient Meta-modeling for OpenSees-based Resilience Analysis
# Copyright 2026 Amin Pakzad and Pedro Arduino
# Developed at the UW Geotechnical Lab
# SPDX-License-Identifier: Apache-2.0
# =============================================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence

import numpy as np
import pyvista as pv
from scipy.spatial import cKDTree

from femora.core.interface_base import InterfaceBase
from femora.components.event.mixins import HandlesDecompositionMixin
from femora.core.meshpart_base import MeshPart
from femora.components.mesh.line_meshparts import SingleLineMesh, StructuredLineMesh
from femora.core.event_bus import FemoraEvent
from femora.components.interface.embedded_info import EmbeddedInfo
from femora.core.region_base import RegionBase


@dataclass
class _SolidSearchContext:
    """Cached solid-cell geometry for beam-solid neighborhood search."""

    cell_ids: np.ndarray
    centers: np.ndarray
    search_radii: np.ndarray
    tree: cKDTree


class EmbeddedBeamSolidInterface(InterfaceBase, HandlesDecompositionMixin):
    """Embedded beam-solid contact interface.

    EmbeddedBeamSolidInterface models the kinematic and force contact interaction 
    between line elements (e.g. beam-column piles) and 3D solid elements (e.g. soil). 
    It enforces matching partition cores between the embedded beam elements and 
    overlapping solid elements.

    Tcl form:
        None (renders internally via OpenSees interface-specific TCL commands).

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        # Create an interface for a piles meshpart within the soil domain
        interface = model.interface.beam_solid_interface(
            name="pile_soil_interface",
            beam_part="piles",
            radius=0.25,
            n_peri=8,
            n_long=5,
            penalty_param=1.0e12,
            g_penalty=True,
        )
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__", "plot"],
    }

    _SOLID_CELL_TYPES = {
        pv.CellType.HEXAHEDRON,
        pv.CellType.VOXEL,
        pv.CellType.TETRA,
        pv.CellType.WEDGE,
        pv.CellType.PYRAMID,
    }

    @staticmethod
    def _meshpart_has_line_cells(meshpart: MeshPart) -> bool:
        """Return True when a meshpart contains line cells."""
        mesh = getattr(meshpart, "mesh", None)
        return mesh is not None and np.any(mesh.celltypes == pv.CellType.LINE)

    @staticmethod
    def _extract_surface_compat(mesh: pv.DataSet) -> pv.PolyData:
        """Return a surface mesh across PyVista versions.

        Newer PyVista versions support the ``algorithm`` keyword, while older
        versions raise ``TypeError`` for it. This helper keeps current behavior
        explicit when supported and falls back cleanly otherwise.
        """
        try:
            return mesh.extract_surface(algorithm="dataset_surface")
        except TypeError:
            return mesh.extract_surface()

    @staticmethod
    def _find_line_path_endpoints(
        mesh: pv.UnstructuredGrid,
        line_cell_ids: np.ndarray,
    ) -> tuple[int, int, np.ndarray, np.ndarray]:
        """Return endpoints for one open path of selected line cells.

        Connectivity is computed only from ``line_cell_ids``. Other elements in
        the assembled mesh that share the same physical nodes are intentionally
        ignored, so this finds the endpoints of the selected beam path itself.
        """
        line_cell_ids = np.asarray(line_cell_ids, dtype=int)
        if line_cell_ids.size == 0:
            raise ValueError("No line cells were provided.")

        degrees: dict[int, int] = {}
        for cell_id in line_cell_ids:
            if mesh.celltypes[cell_id] != pv.CellType.LINE:
                raise ValueError(f"Cell {cell_id} is not a line cell.")

            start = mesh.offset[cell_id]
            end = mesh.offset[cell_id + 1]
            point_ids = mesh.cell_connectivity[start:end]
            if point_ids.size != 2:
                raise ValueError(f"Line cell {cell_id} does not have exactly two points.")

            point_a = int(point_ids[0])
            point_b = int(point_ids[1])
            degrees[point_a] = degrees.get(point_a, 0) + 1
            degrees[point_b] = degrees.get(point_b, 0) + 1

        endpoint_ids = [point_id for point_id, degree in degrees.items() if degree == 1]
        if len(endpoint_ids) != 2:
            raise ValueError(
                f"Expected exactly two endpoints for one open line path, found {len(endpoint_ids)}. "
                "The selected cells may be branched, disconnected, or closed."
            )

        start_id, end_id = endpoint_ids
        return start_id, end_id, mesh.points[start_id].copy(), mesh.points[end_id].copy()

    @staticmethod
    def _order_line_path_segments(
        mesh: pv.UnstructuredGrid,
        line_cell_ids: np.ndarray,
    ) -> list[tuple[int, int, int, float, float]]:
        """Order one open line-cell path and assign global path coordinates.

        Returns:
            Tuples of ``(cell_id, start_point_id, end_point_id, s0, s1)``.
            The coordinate ``s`` runs from 0 to 1 over the full connected path.
        """
        line_cell_ids = np.asarray(line_cell_ids, dtype=int)
        start_endpoint, end_endpoint, _, _ = EmbeddedBeamSolidInterface._find_line_path_endpoints(
            mesh,
            line_cell_ids,
        )

        edge_by_cell: dict[int, tuple[int, int]] = {}
        node_to_cells: dict[int, list[int]] = {}
        for cell_id in line_cell_ids:
            start = mesh.offset[cell_id]
            end = mesh.offset[cell_id + 1]
            point_a, point_b = [int(point_id) for point_id in mesh.cell_connectivity[start:end]]
            edge_by_cell[int(cell_id)] = (point_a, point_b)
            node_to_cells.setdefault(point_a, []).append(int(cell_id))
            node_to_cells.setdefault(point_b, []).append(int(cell_id))

        ordered_edges: list[tuple[int, int, int]] = []
        visited_cells: set[int] = set()
        current_point = start_endpoint
        while len(visited_cells) < len(line_cell_ids):
            next_cell = None
            for cell_id in node_to_cells.get(current_point, []):
                if cell_id not in visited_cells:
                    next_cell = cell_id
                    break
            if next_cell is None:
                raise ValueError(
                    "Selected line cells are disconnected or cannot be ordered as one path."
                )

            point_a, point_b = edge_by_cell[next_cell]
            next_point = point_b if point_a == current_point else point_a
            ordered_edges.append((next_cell, current_point, next_point))
            visited_cells.add(next_cell)
            current_point = next_point

        if current_point != end_endpoint:
            raise ValueError("Selected line path did not terminate at the expected endpoint.")

        lengths = []
        for _, point_a, point_b in ordered_edges:
            length = float(np.linalg.norm(mesh.points[point_b] - mesh.points[point_a]))
            if length <= 0.0:
                raise ValueError("Selected line path contains a zero-length segment.")
            lengths.append(length)

        total_length = float(sum(lengths))
        if total_length <= 0.0:
            raise ValueError("Selected line path has zero total length.")

        ordered_segments: list[tuple[int, int, int, float, float]] = []
        cumulative = 0.0
        for (cell_id, point_a, point_b), length in zip(ordered_edges, lengths):
            s0 = cumulative / total_length
            cumulative += length
            s1 = cumulative / total_length
            ordered_segments.append((cell_id, point_a, point_b, s0, s1))
        return ordered_segments

    def _scale_at_path_coordinate(self, s: float) -> float:
        """Return the interface envelope scale at global path coordinate ``s``."""
        return self.scale_start + np.asarray(s, dtype=float) * (self.scale_end - self.scale_start)

    @staticmethod
    def _orthonormal_basis_from_axis(axis: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Return two unit vectors perpendicular to ``axis``."""
        axis = np.asarray(axis, dtype=float)
        axis_norm = np.linalg.norm(axis)
        if axis_norm <= 0.0:
            raise ValueError("Cannot create a local basis from a zero-length axis.")
        axis = axis / axis_norm

        reference = np.array([0.0, 0.0, 1.0])
        if abs(float(np.dot(axis, reference))) > 0.9:
            reference = np.array([0.0, 1.0, 0.0])

        basis_y = np.cross(axis, reference)
        basis_y = basis_y / np.linalg.norm(basis_y)
        basis_z = np.cross(axis, basis_y)
        basis_z = basis_z / np.linalg.norm(basis_z)
        return basis_y, basis_z

    @staticmethod
    def _create_lofted_section_surface(
        start_point: np.ndarray,
        end_point: np.ndarray,
        section_points: np.ndarray,
        start_scale: float,
        end_scale: float,
    ) -> pv.PolyData:
        """Create a capped lofted surface between scaled cross-sections."""
        if start_scale <= 0.0 or end_scale <= 0.0:
            raise ValueError("Section scales must be positive.")
        section_points = np.asarray(section_points, dtype=float)
        if section_points.ndim != 2 or section_points.shape[1] != 2 or section_points.shape[0] < 3:
            raise ValueError("section_points must be an array of at least three (y, z) points.")

        axis = np.asarray(end_point, dtype=float) - np.asarray(start_point, dtype=float)
        basis_y, basis_z = EmbeddedBeamSolidInterface._orthonormal_basis_from_axis(axis)

        start_ring = []
        end_ring = []
        for y, z in section_points:
            local_direction = y * basis_y + z * basis_z
            start_ring.append(start_point + start_scale * local_direction)
            end_ring.append(end_point + end_scale * local_direction)

        resolution = len(section_points)
        center_start_id = 2 * resolution
        center_end_id = center_start_id + 1
        points = np.vstack((start_ring, end_ring, start_point, end_point))

        faces = []
        for i in range(resolution):
            j = (i + 1) % resolution
            faces.extend([4, i, j, resolution + j, resolution + i])
            faces.extend([3, center_start_id, j, i])
            faces.extend([3, center_end_id, resolution + i, resolution + j])

        return pv.PolyData(points, np.asarray(faces, dtype=np.int64))

    def _base_section_points(self) -> np.ndarray:
        """Return the unscaled local section envelope points for this interface."""
        shape = self.shape.lower()
        if shape == "circle":
            angles = np.linspace(0.0, 2.0 * np.pi, self.n_peri, endpoint=False)
            return np.column_stack((self.radius * np.cos(angles), self.radius * np.sin(angles)))
        if shape == "ellipse":
            angles = np.linspace(0.0, 2.0 * np.pi, self.n_peri, endpoint=False)
            return np.column_stack((self.radius_y * np.cos(angles), self.radius_z * np.sin(angles)))
        if shape == "rectangle":
            half_width = self.width / 2.0
            half_height = self.height / 2.0
            return np.array(
                [
                    [-half_width, -half_height],
                    [half_width, -half_height],
                    [half_width, half_height],
                    [-half_width, half_height],
                ],
                dtype=float,
            )
        if shape == "polygon":
            return self.section_points.copy()
        raise ValueError(f"Unsupported shape '{self.shape}'.")

    def _section_search_radius(self, section_points: np.ndarray, scale: float) -> float:
        """Return a conservative radial search distance for section points."""
        return float(np.max(np.linalg.norm(section_points, axis=1)) * scale)

    @staticmethod
    def _solid_cell_mask(mesh: pv.UnstructuredGrid) -> np.ndarray:
        """Return a mask for supported 3D solid cells."""
        return np.isin(mesh.celltypes, list(EmbeddedBeamSolidInterface._SOLID_CELL_TYPES))

    @staticmethod
    def _build_solid_search_context(mesh: pv.UnstructuredGrid) -> _SolidSearchContext:
        """Build a reusable spatial index for solid cells in ``mesh``."""
        solid_mask = EmbeddedBeamSolidInterface._solid_cell_mask(mesh)
        solid_cell_ids = np.where(solid_mask)[0].astype(int)
        if solid_cell_ids.size == 0:
            return _SolidSearchContext(
                cell_ids=solid_cell_ids,
                centers=np.empty((0, 3), dtype=float),
                search_radii=np.empty(0, dtype=float),
                tree=cKDTree(np.empty((1, 3), dtype=float)),
            )

        starts = mesh.offset[solid_cell_ids]
        sizes = mesh.offset[solid_cell_ids + 1] - starts
        if np.all(sizes == sizes[0]):
            local_offsets = starts[:, None] + np.arange(int(sizes[0]))[None, :]
            cell_point_ids = mesh.cell_connectivity[local_offsets]
            cell_points = mesh.points[cell_point_ids]
            centers = np.mean(cell_points, axis=1)
            search_radii = np.max(np.linalg.norm(cell_points - centers[:, None, :], axis=2), axis=1)
        else:
            centers = np.zeros((solid_cell_ids.size, 3), dtype=float)
            search_radii = np.zeros(solid_cell_ids.size, dtype=float)
            for local_index, cell_id in enumerate(solid_cell_ids):
                start = mesh.offset[cell_id]
                end = mesh.offset[cell_id + 1]
                ids = np.asarray(mesh.cell_connectivity[start:end], dtype=int)
                if ids.size:
                    points = mesh.points[ids]
                    centers[local_index] = np.mean(points, axis=0)
                    search_radii[local_index] = float(
                        np.max(np.linalg.norm(points - centers[local_index], axis=1))
                    )

        return _SolidSearchContext(
            cell_ids=solid_cell_ids,
            centers=centers,
            search_radii=search_radii,
            tree=cKDTree(centers),
        )

    def _solid_part_cell_mask(self, mesh: pv.UnstructuredGrid) -> np.ndarray:
        """Return mask for solid cells belonging to this interface's selected solid parts."""
        solid_mask = self._solid_cell_mask(mesh)
        if self.solid_parts is None:
            return solid_mask

        meshpart_tags = mesh.cell_data.get("MeshPartTag_celldata")
        if meshpart_tags is None:
            raise ValueError(
                "Assembled mesh is missing 'MeshPartTag_celldata'; cannot filter solid_parts."
            )

        selected_tags = np.asarray([part.tag for part in self.solid_parts], dtype=meshpart_tags.dtype)
        return solid_mask & np.isin(meshpart_tags, selected_tags)

    def _build_selected_solid_search_context(self, mesh: pv.UnstructuredGrid) -> _SolidSearchContext:
        """Build a spatial index for only the relevant solid cells."""
        mask = self._solid_part_cell_mask(mesh)
        selected_cell_ids = np.where(mask)[0].astype(int)
        if selected_cell_ids.size == 0:
            part_names = (
                "all solid meshparts"
                if self.solid_parts is None
                else ", ".join(part.user_name for part in self.solid_parts)
            )
            raise ValueError(
                f"EmbeddedBeamSolidInterface '{self.name}' found no solid cells for {part_names}."
            )

        subset = mesh.extract_cells(selected_cell_ids, progress_bar=False)
        context = self._build_solid_search_context(subset)
        context.cell_ids = selected_cell_ids[context.cell_ids]
        return context

    @staticmethod
    def _candidate_cells_for_segment(
        context: _SolidSearchContext,
        segment_center: np.ndarray,
        segment_length: float,
        envelope_radius: float,
    ) -> np.ndarray:
        """Return broad-phase candidate local indices for one beam segment."""
        if context.cell_ids.size == 0:
            return np.empty(0, dtype=int)
        max_cell_radius = float(np.max(context.search_radii)) if context.search_radii.size else 0.0
        query_radius = segment_length / 2.0 + envelope_radius + max_cell_radius
        candidate_local_ids = context.tree.query_ball_point(segment_center, r=query_radius)
        return np.asarray(candidate_local_ids, dtype=int)

    @staticmethod
    def _points_inside_polygon(points: np.ndarray, polygon: np.ndarray) -> np.ndarray:
        """Vectorized 2D point-in-polygon test."""
        x = points[:, 0]
        y = points[:, 1]
        poly_x = polygon[:, 0]
        poly_y = polygon[:, 1]
        inside = np.zeros(points.shape[0], dtype=bool)
        j = polygon.shape[0] - 1
        for i in range(polygon.shape[0]):
            crosses = ((poly_y[i] > y) != (poly_y[j] > y)) & (
                x < (poly_x[j] - poly_x[i]) * (y - poly_y[i]) / (poly_y[j] - poly_y[i] + 1e-30) + poly_x[i]
            )
            inside ^= crosses
            j = i
        return inside

    def _local_points_inside_section(
        self,
        local_yz: np.ndarray,
        scale: np.ndarray,
    ) -> np.ndarray:
        """Return mask for local section points inside the tapered envelope."""
        shape = self.shape.lower()
        if shape == "circle":
            radius = self.radius * scale
            return np.sum(local_yz**2, axis=1) <= radius**2
        if shape == "ellipse":
            radius_y = self.radius_y * scale
            radius_z = self.radius_z * scale
            return (local_yz[:, 0] / radius_y) ** 2 + (local_yz[:, 1] / radius_z) ** 2 <= 1.0
        if shape == "rectangle":
            half_width = 0.5 * self.width * scale
            half_height = 0.5 * self.height * scale
            return (np.abs(local_yz[:, 0]) <= half_width) & (np.abs(local_yz[:, 1]) <= half_height)
        if shape == "polygon":
            result = np.zeros(local_yz.shape[0], dtype=bool)
            unique_scales = np.unique(scale)
            for value in unique_scales:
                mask = scale == value
                result[mask] = self._points_inside_polygon(local_yz[mask], self.section_points * value)
            return result
        raise ValueError(f"Unsupported shape '{self.shape}'.")

    def _filter_candidate_cells_for_segment(
        self,
        mesh: pv.UnstructuredGrid,
        context: _SolidSearchContext,
        candidate_local_ids: np.ndarray,
        tail: np.ndarray,
        head: np.ndarray,
        s0: float,
        s1: float,
    ) -> np.ndarray:
        """Narrow broad-phase candidates with analytic tapered-section checks."""
        if candidate_local_ids.size == 0:
            return np.empty(0, dtype=int)

        axis = head - tail
        length = float(np.linalg.norm(axis))
        if length <= 0.0:
            return np.empty(0, dtype=int)
        axis_unit = axis / length

        centers = context.centers[candidate_local_ids]
        rel = centers - tail
        axial = rel @ axis_unit
        closest_axial = np.clip(axial, 0.0, length)
        closest_points = tail + closest_axial[:, None] * axis_unit
        center_distance_to_segment = np.linalg.norm(centers - closest_points, axis=1)

        closest_s = s0 + (closest_axial / length) * (s1 - s0)
        section_points = self._base_section_points()
        envelope_radius = np.asarray(
            [
                self._section_search_radius(section_points, scale)
                for scale in self._scale_at_path_coordinate(closest_s)
            ],
            dtype=float,
        )
        cell_margin = self.selection_margin * context.search_radii[candidate_local_ids]
        axial_overlap = (axial >= -cell_margin) & (axial <= length + cell_margin)
        radial_overlap = center_distance_to_segment <= envelope_radius + cell_margin
        selected = axial_overlap & radial_overlap
        return context.cell_ids[candidate_local_ids[selected]]

    def _find_nearby_cells_for_line_path(
        self,
        assembled_mesh: pv.UnstructuredGrid,
        line_cell_ids: np.ndarray,
    ) -> tuple[np.ndarray, list[tuple[int, int, int, float, float]]]:
        """Find cells near a possibly curved selected line path.

        The search is segment-based. Each selected line cell gets a circular
        envelope using the maximum tapered scale over that segment.
        """
        ordered_segments = self._order_line_path_segments(assembled_mesh, line_cell_ids)
        selected_cell_ids: set[int] = set()
        section_points = self._base_section_points()
        search_context = self._build_selected_solid_search_context(assembled_mesh)

        for _, point_a, point_b, s0, s1 in ordered_segments:
            tail = assembled_mesh.points[point_a]
            head = assembled_mesh.points[point_b]
            segment_vector = head - tail
            segment_length = float(np.linalg.norm(segment_vector))
            if segment_length <= 0.0:
                continue

            scale_start = self._scale_at_path_coordinate(s0)
            scale_end = self._scale_at_path_coordinate(s1)
            search_radius = max(
                self._section_search_radius(section_points, scale_start),
                self._section_search_radius(section_points, scale_end),
            )
            segment_center = (tail + head) / 2.0
            candidate_local_ids = self._candidate_cells_for_segment(
                search_context,
                segment_center,
                segment_length,
                search_radius,
            )
            selected_cell_ids.update(
                int(cell_id)
                for cell_id in self._filter_candidate_cells_for_segment(
                    assembled_mesh,
                    search_context,
                    candidate_local_ids,
                    tail,
                    head,
                    s0,
                    s1,
                )
            )

            segment_intersections = assembled_mesh.find_cells_intersecting_line(
                tail,
                head,
                tolerance=search_radius,
            )
            if len(segment_intersections) > 0:
                selected_cell_ids.update(int(cell_id) for cell_id in segment_intersections)

        selected = np.asarray(sorted(selected_cell_ids), dtype=int)
        if selected.size == 0:
            return selected, ordered_segments

        allowed_mask = self._solid_part_cell_mask(assembled_mesh)
        selected = selected[allowed_mask[selected]]
        return selected, ordered_segments

    def __init__(
        self,
        name: str,
        beam_part: 'MeshPart | str | int',
        solid_parts: 'List[MeshPart | str | int] | None' = None,
        shape: str = "circle",
        radius: float = 0.5,
        radius_y: float | None = None,
        radius_z: float | None = None,
        width: float | None = None,
        height: float | None = None,
        section_points: Sequence[Sequence[float]] | None = None,
        n_peri: int = 8,
        n_long: int = 10,
        penalty_param: float = 1.0e12,
        g_penalty: bool = True,
        scale_start: float = 1.0,
        scale_end: float = 1.0,
        selection_margin: float = 0.35,
        _diagnostic_geometry: bool = False,
        _diagnostic_line_mesh: bool = False,
        region: 'RegionBase | None' = None,
        write_connectivity: bool = False,
        write_interface: bool = False,
        *,
        meshpart,
    ) -> None:
        """Create an EmbeddedBeamSolidInterface.

        Args:
            name: Unique name of the contact interface.
            beam_part: The beam part instance, name, or tag.
            solid_parts: Optional list of solid part instances, names, or tags.
            shape: Shape profile of the beam cross-section. Production OpenSees
                export currently supports only "circle". Defaults to "circle".
            radius: Radius of the circular beam interface geometry. Defaults to 0.5.
            radius_y: Internal diagnostic ellipse semi-axis in the local section y direction.
            radius_z: Internal diagnostic ellipse semi-axis in the local section z direction.
            width: Internal diagnostic rectangle width in the local section y direction.
            height: Internal diagnostic rectangle height in the local section z direction.
            section_points: Internal diagnostic polygon vertices as local ``(y, z)`` pairs.
            n_peri: Number of points along the perimeter of the circular section. Defaults to 8.
            n_long: Number of points along the longitudinal axis of the beam. Defaults to 10.
            penalty_param: Penalty stiffness parameter for the constraint. Defaults to 1.0e12.
            g_penalty: If True, uses the geometric penalty formulation. Defaults to True.
            scale_start: Internal diagnostic interface envelope scale at the first
                endpoint of the beam path. Production export requires 1.0.
            scale_end: Internal diagnostic interface envelope scale at the second
                endpoint of the beam path. Production export requires 1.0.
            selection_margin: Fraction of each candidate solid cell bounding radius
                allowed outside the interface envelope during fast solid discovery.
                Smaller values select tighter neighborhoods. Defaults to 0.35.
            _diagnostic_geometry: Internal flag used by visual diagnostics to
                exercise non-exported envelope shapes and tapered discovery.
            _diagnostic_line_mesh: Internal flag used by visual diagnostics to
                allow generic line-cell meshparts that are not export-ready.
            region: Optional region bounding the interface. Not implemented yet.
            write_connectivity: If True, outputs boundary connectivity maps to file. Defaults to False.
            write_interface: If True, outputs boundary mesh surfaces to file. Defaults to False.
            meshpart: MeshPart registry manager from the parent model.

        Raises:
            ValueError: If `beam_part` cannot be resolved or if shape is unsupported.
            TypeError: If argument types are invalid (e.g. `beam_part` is not a line mesh).
            NotImplementedError: If unsupported parameter configurations are provided.
        """
        resolved_beam = meshpart.resolve(beam_part)
        if resolved_beam is None:
            raise ValueError(f"Could not retrieve beam_part '{beam_part}' to a MeshPart.")
        is_standard_line_mesh = isinstance(resolved_beam, (SingleLineMesh, StructuredLineMesh))
        is_diagnostic_line_mesh = _diagnostic_line_mesh and self._meshpart_has_line_cells(resolved_beam)
        if not is_standard_line_mesh and not is_diagnostic_line_mesh:
            raise TypeError(
                "beam_part must be a SingleLineMesh or StructuredLineMesh instance."
            )
        
        resolved_soild_parts = []
        if solid_parts is not None:
            if not isinstance(solid_parts, list):
                raise TypeError("soild_parts must be a list of MeshPart instances or their user_names.")
            for part in solid_parts:
                resolved_part = meshpart.resolve(part)
                if resolved_part is None:
                    raise ValueError(f"Could not retrieve solid_part '{part}' to a MeshPart.")
                resolved_soild_parts.append(resolved_part)

        super().__init__(name=name, owners=[resolved_beam.user_name])

        # store references
        self.beam_part = resolved_beam
        self.solid_parts = resolved_soild_parts if len(resolved_soild_parts) > 0 else None
        self.shape = shape.lower()
        supported_shapes = {"circle", "ellipse", "rectangle", "polygon"}
        if self.shape not in supported_shapes:
            supported = ", ".join(sorted(supported_shapes))
            raise ValueError(f"Unsupported shape '{shape}'. Supported shapes: {supported}.")
        if not _diagnostic_geometry and self.shape != "circle":
            raise ValueError(
                "EmbeddedBeamSolidInterface currently exports only circular OpenSees interfaces. "
                "Non-circular envelopes are available only for internal diagnostics."
            )

        if radius <= 0.0:
            raise ValueError("radius must be a positive number.")
        self.radius = float(radius)
        self.radius_y = float(radius if radius_y is None else radius_y)
        self.radius_z = float(radius if radius_z is None else radius_z)
        if self.radius_y <= 0.0 or self.radius_z <= 0.0:
            raise ValueError("radius_y and radius_z must be positive numbers.")

        self.width = float(2.0 * radius if width is None else width)
        self.height = float(2.0 * radius if height is None else height)
        if self.width <= 0.0 or self.height <= 0.0:
            raise ValueError("width and height must be positive numbers.")

        if section_points is None:
            self.section_points = np.empty((0, 2), dtype=float)
        else:
            self.section_points = np.asarray(section_points, dtype=float)
            if (
                self.section_points.ndim != 2
                or self.section_points.shape[1] != 2
                or self.section_points.shape[0] < 3
            ):
                raise ValueError("section_points must contain at least three (y, z) pairs.")
        if self.shape == "polygon" and self.section_points.size == 0:
            raise ValueError("section_points must be provided when shape='polygon'.")

        self.n_peri = int(n_peri)
        if self.n_peri < 3:
            raise ValueError("n_peri must be at least 3.")
        self.n_long = n_long
        self.penalty_param = penalty_param
        self.g_penalty = g_penalty
        if scale_start <= 0.0 or scale_end <= 0.0:
            raise ValueError("scale_start and scale_end must be positive numbers.")
        self.scale_start = float(scale_start)
        self.scale_end = float(scale_end)
        if not _diagnostic_geometry and (
            self.scale_start != 1.0 or self.scale_end != 1.0
        ):
            raise ValueError(
                "EmbeddedBeamSolidInterface currently exports a constant circular radius. "
                "Tapered envelopes are available only for internal diagnostics."
            )
        if selection_margin < 0.0:
            raise ValueError("selection_margin must be non-negative.")
        self.selection_margin = float(selection_margin)
        self._instance_embeddedinfo_list: List[EmbeddedInfo] = [] # Instance-level list to store per-instance EmbeddedInfo
        if region is not None and not isinstance(region, RegionBase):
            raise TypeError("region must be an instance of RegionBase or None.")
        elif region is None:
            self.region = region
        else:
            raise NotImplementedError("Region handling is not implemented yet. Please do not use region parameter for now.")
        self.write_connectivity = write_connectivity
        self.write_interface = write_interface

    def plot(
        self,
        *,
        show_mesh: bool = True,
        show_envelope: bool = True,
        show_edges: bool = True,
        mesh_opacity: float = 0.08,
        selected_opacity: float = 0.65,
        envelope_opacity: float = 0.35,
        beam_color: str = "black",
        selected_color: str = "orange",
        envelope_color: str = "steelblue",
        off_screen: bool = False,
        screenshot: str | None = None,
        window_size: tuple[int, int] = (1400, 900),
        return_plotter: bool = False,
    ) -> pv.Plotter | None:
        """Plot the assembled beam-solid interface selection.

        The plot shows the assembled model as a faint reference mesh, the beam
        cells owned by this interface, the selected surrounding solid cells, and
        the circular radius envelope used by Femora-side discovery.

        Args:
            show_mesh: If True, draw the whole assembled mesh as a faint wireframe.
            show_envelope: If True, draw the radius envelope around each beam segment.
            show_edges: If True, draw edges on selected solid cells.
            mesh_opacity: Opacity of the assembled reference mesh.
            selected_opacity: Opacity of selected solid cells.
            envelope_opacity: Opacity of the radius envelope.
            beam_color: Color used for beam cells.
            selected_color: Color used for selected solid cells.
            envelope_color: Color used for the radius envelope.
            off_screen: If True, render without opening an interactive window.
            screenshot: Optional image path to write a screenshot.
            window_size: PyVista window size in pixels.
            return_plotter: If True, return the configured plotter instead of
                calling ``show()``.

        Returns:
            A PyVista plotter when ``return_plotter`` is True; otherwise None.

        Raises:
            RuntimeError: If the interface is unmanaged, the model is not assembled,
                or no embedded interface data has been collected yet.
        """
        if self._owner is None:
            raise RuntimeError(
                f"EmbeddedBeamSolidInterface '{self.name}' must be managed before plotting."
            )
        if not self._instance_embeddedinfo_list:
            raise RuntimeError(
                f"EmbeddedBeamSolidInterface '{self.name}' has no collected interface data. "
                "Assemble the model before calling plot()."
            )

        mesh = self._owner._mesh_maker.assembler.get_mesh()
        if mesh is None:
            raise RuntimeError("The model must be assembled before plotting an interface.")

        beam_ids: set[int] = set()
        solid_ids: set[int] = set()
        for info in self._instance_embeddedinfo_list:
            beam_ids.update(int(cell_id) for cell_id in info.beams)
            for _, solids in info.beams_solids:
                solid_ids.update(int(cell_id) for cell_id in solids)

        if not beam_ids or not solid_ids:
            raise RuntimeError(
                f"EmbeddedBeamSolidInterface '{self.name}' did not collect beam/solid cells."
            )

        beam_cell_ids = np.asarray(sorted(beam_ids), dtype=int)
        solid_cell_ids = np.asarray(sorted(solid_ids), dtype=int)
        beam_mesh = mesh.extract_cells(beam_cell_ids, progress_bar=False)
        selected_solids = mesh.extract_cells(solid_cell_ids, progress_bar=False)

        plotter = pv.Plotter(off_screen=off_screen, window_size=window_size)
        plotter.add_text(
            (
                f"{self.name}: beams={beam_cell_ids.size}, "
                f"selected solids={solid_cell_ids.size}, radius={self.radius:g}"
            ),
            font_size=12,
        )

        if show_mesh:
            plotter.add_mesh(
                mesh,
                style="wireframe",
                color="lightgray",
                opacity=mesh_opacity,
            )
        plotter.add_mesh(
            selected_solids,
            color=selected_color,
            opacity=selected_opacity,
            show_edges=show_edges,
        )
        plotter.add_mesh(beam_mesh, color=beam_color, line_width=8)

        if show_envelope:
            section_points = self._base_section_points()
            for info in self._instance_embeddedinfo_list:
                ordered_segments = self._order_line_path_segments(
                    mesh,
                    np.asarray(sorted(info.beams), dtype=int),
                )
                for _, point_a, point_b, s0, s1 in ordered_segments:
                    envelope = self._create_lofted_section_surface(
                        mesh.points[point_a],
                        mesh.points[point_b],
                        section_points,
                        self._scale_at_path_coordinate(s0),
                        self._scale_at_path_coordinate(s1),
                    )
                    plotter.add_mesh(
                        envelope,
                        color=envelope_color,
                        opacity=envelope_opacity,
                        show_edges=False,
                    )

        plotter.view_isometric()
        if screenshot:
            plotter.screenshot(screenshot)
        if return_plotter:
            return plotter
        plotter.show()
        plotter.close()
        return None

    def _collect_embedded_info_for_beam_path(self, assembled_mesh: pv.UnstructuredGrid, beam_cells_idx: np.ndarray):
        """Collect embedded beam-solid connectivity for one connected beam path.

        This method intentionally builds ``EmbeddedInfo`` only. Final ``Core``
        changes are applied later by ``InterfaceManager._resolve_beam_solid_conflicts``
        during the ``RESOLVE_CORE_CONFLICTS`` assembly event.

        Args:
            assembled_mesh: The main assembled PyVista grid.
            beam_cells_idx: Array of cell indices for the connected beam path.

        Raises:
            ValueError: If no beams or solids are found during implicit distance calculations.
            RuntimeError: If this interface is not managed by InterfaceManager.
        """
        # t_start_total = time.time()
        # Work on a local copy so discovery can safely annotate/extract meshes.
        # The real assembled mesh is updated only after all embedded interfaces
        # have reported their EmbeddedInfo records and conflicts are resolved.
        assembled_mesh = assembled_mesh.copy()
        beam_core_array = assembled_mesh.cell_data["Core"][beam_cells_idx]
        unique_cores = np.unique(beam_core_array)
        # sort the unique cores from smallest to largest
        unique_cores = np.sort(unique_cores)
        target_core = int(unique_cores[0])


        nearby_cell_ids, ordered_segments = self._find_nearby_cells_for_line_path(
            assembled_mesh,
            beam_cells_idx,
        )

                

        # t_start_section = time.time()
        inner_cell_ids = np.unique(
            np.concatenate((nearby_cell_ids, np.asarray(beam_cells_idx, dtype=int)))
        )
        inner = assembled_mesh.extract_cells(
            inner_cell_ids,
            progress_bar=False
        )
        # print(f"--- Time for inner mesh extraction: {time.time() - t_start_section:.4f}s")



        beam_elements = inner.celltypes == pv.CellType.LINE
        solid_elements = self._solid_part_cell_mask(inner)
        beam_ind = inner.cell_data["vtkOriginalCellIds"][beam_elements]
        solid_ind = inner.cell_data["vtkOriginalCellIds"][solid_elements]


        # save the assembeled mesh indexes to the inner mesh
        inner.cell_data["mesh_ind"] = np.zeros(inner.n_cells, dtype=np.int32)
        inner.cell_data["mesh_ind"][solid_elements] = solid_ind
        inner.cell_data["mesh_ind"][beam_elements] = beam_ind


        # Do a for loop and in every iteration pop up the largest solid mesh from the inner mesh
        solid_mesh = inner.extract_cells(solid_elements, progress_bar=False)
        beam_mesh  = inner.extract_cells(beam_elements, progress_bar=False)
        beams_solids = []
        # t_start_loop = time.time()
        while solid_mesh.n_cells > 0:
            solid_mesh_largest = solid_mesh.extract_largest()
            surf = self._extract_surface_compat(solid_mesh_largest)
            beam_mesh.compute_implicit_distance(surf,inplace=True)
            beams = beam_mesh.point_data["implicit_distance"] <= 0
            beams = beam_mesh.extract_points(beams, include_cells=True, adjacent_cells=True, progress_bar=False)

            if beams.n_cells < 1:
                if solid_mesh_largest.n_cells < 1:
                    raise ValueError("No beams and solids found in the solid mesh.")
                else:
                    # # plot for debugging
                    # pl = pv.Plotter()
                    # pl.add_mesh(solid_mesh_largest, color="blue", opacity=0.5, show_edges=True)
                    # pl.add_mesh(beam_mesh, color="red", opacity=1.0, line_width=5)
                    # pl.show()
                    intersects_path = False
                    for _, point_a, point_b, _, _ in ordered_segments:
                        ind = solid_mesh_largest.find_cells_intersecting_line(
                            assembled_mesh.points[point_a],
                            assembled_mesh.points[point_b],
                            tolerance=0,
                        )
                        if len(ind) > 0:
                            intersects_path = True
                            break
                    if not intersects_path:
                        pass
                    else:
                        raise ValueError(f"[EmbeddedBeamSolidInterface:{self.name}]: No beams found in the solid mesh, but solids are present. This is unexpected. \
                        probably the beam mesh size is too small. \
                        please increase the number of points in the beam mesh.")
            else:
                if solid_mesh_largest.n_cells < 1:
                    raise ValueError("No solids found in the solid mesh, but beams are present. This is unexpected. contact the developers.")
                

            if beams.n_cells > 0 and solid_mesh_largest.n_cells > 0:
                beams = beams.cell_data["mesh_ind"]
                solids = solid_mesh_largest.cell_data["mesh_ind"]

                if len(beams) > 0 and len(solids) > 0:
                    beams_solids.append((beams, solids))

            # now remove the largset solid mesh from the solid_mesh
            solid_mesh = solid_mesh.extract_values(solid_mesh_largest.cell_data["mesh_ind"] , invert=True, scalars="mesh_ind")
        # print(f"--- Time for while loop: {time.time() - t_start_loop:.4f}s")
      
        
        
        # print("num cells:", assembled_mesh.n_cells)
        # print("num points:", assembled_mesh.n_points)


        if len(beams_solids) == 0:
            return
        

        ef = EmbeddedInfo(beams=beam_ind,
                     core_number= target_core,
                     beams_solids=beams_solids)
        if self._owner is None:
            raise RuntimeError(
                f"EmbeddedBeamSolidInterface '{self.name}' must be managed by InterfaceManager "
                "before recording EmbeddedInfo"
            )
        self._owner._embeddedinfo_list.append(ef)
        self._instance_embeddedinfo_list.append(ef)


        # print(f"--- Total time for _collect_embedded_info_for_beam_path: {time.time() - t_start_total:.4f}s")

    def _on_post_assemble(self, assembled_mesh: pv.UnstructuredGrid, **kwargs):
        """Post-assemble event listener to map core partitions between beams and solids.

        Args:
            assembled_mesh: The assembled PyVista grid.
            **kwargs: Extra event payload.

        Raises:
            ValueError: If no beam elements are found or structured mesh length is missing.
            TypeError: If `beam_part` is of an invalid mesh type.
        """
        # Collect beam cells indices & compute their mean location
        beam_cells_idx = np.where(assembled_mesh.cell_data["MeshPartTag_celldata"] == self.beam_part.tag)[0]
        if beam_cells_idx.size == 0:
            raise ValueError("No beam elements found in assembled mesh for provided MeshPart")
        
        if isinstance(self.beam_part, StructuredLineMesh):
            # Type hint for IDE auto-complete
            beam_mesh: pv.UnstructuredGrid = self.beam_part.mesh.copy()
            norm_x = self.beam_part.normal_x
            norm_y = self.beam_part.normal_y
            norm_z = self.beam_part.normal_z
            offset_1 = self.beam_part.offset_1
            offset_2 = self.beam_part.offset_2
            base_point_x = self.beam_part.base_point_x
            base_point_y = self.beam_part.base_point_y
            base_point_z = self.beam_part.base_point_z
            base_vector_1_x = self.beam_part.base_vector_1_x
            base_vector_1_y = self.beam_part.base_vector_1_y
            base_vector_1_z = self.beam_part.base_vector_1_z
            base_vector_2_x = self.beam_part.base_vector_2_x
            base_vector_2_y = self.beam_part.base_vector_2_y
            base_vector_2_z = self.beam_part.base_vector_2_z
            grid_size_1 = self.beam_part.grid_size_1
            grid_size_2 = self.beam_part.grid_size_2
            spacing_1 = self.beam_part.spacing_1
            spacing_2 = self.beam_part.spacing_2
            length = self.beam_part.length

            if length is None:
                raise ValueError("StructuredLineMesh must have length defined.")

            if grid_size_1 is None or grid_size_2 is None:
                raise ValueError("StructuredLineMesh must have grid_size_1 and grid_size_2 defined.")
            
            if spacing_1 is None or spacing_2 is None:
                raise ValueError("StructuredLineMesh must have spacing_1 and spacing_2 defined.")

            if base_vector_1_x is None or base_vector_1_y is None or base_vector_1_z is None:
                raise ValueError(
                    "StructuredLineMesh must have base_vector_1_x, base_vector_1_y, and base_vector_1_z defined."
                )
            
            if base_vector_2_x is None or base_vector_2_y is None or base_vector_2_z is None:
                raise ValueError(
                    "StructuredLineMesh must have base_vector_2_x, base_vector_2_y, and base_vector_2_z defined."
                )

            if base_point_x is None or base_point_y is None or base_point_z is None:
                raise ValueError(
                    "StructuredLineMesh must have base_point_x, base_point_y, and base_point_z defined."
                )
            
            if offset_1 is None or offset_2 is None:
                raise ValueError("StructuredLineMesh must have offset_1 and offset_2 defined.")

            if norm_x is None or norm_y is None or norm_z is None:
                raise ValueError("StructuredLineMesh must have normal_x, normal_y, and normal_z defined.")

            i_size = int(grid_size_1 * spacing_1 + 2*offset_1) * 1.2 # 1.2 to make sure the plane is larger than the mesh
            j_size = int(grid_size_2 * spacing_2 + 2*offset_2) * 1.2 # 1.2 to make sure the plane is larger than the mesh


            project_beam = pv.PolyData(beam_mesh.points).project_points_to_plane(origin=beam_mesh.center_of_mass(),
                                                                                 normal=(norm_x, norm_y, norm_z))
            project_beam.merge_points(tolerance=1e-3, inplace=True)
            normal = np.array([norm_x, norm_y, norm_z])
            normal = normal / np.linalg.norm(normal)  # Normalize the normal vector
            beamindxes = np.where(assembled_mesh.cell_data["MeshPartTag_celldata"] == self.beam_part.tag)[0]
            for projected_point in project_beam.points:
                point_a = projected_point - 1.1 * normal * length / 2 # 1.1 to make sure the line is longer than the mesh
                point_b = projected_point + 1.1 * normal * length / 2 # 1.1 to make sure the line is longer than the mesh
                indxes = assembled_mesh.find_cells_along_line(point_a, point_b, tolerance=1e-3)
                indxes = np.intersect1d(indxes, beamindxes, assume_unique=True)  # Only keep beam indices
                if indxes.shape[0] == 0:
                    raise ValueError(
                        f"No beam elements found in assembled mesh for projected point {projected_point}."
                    )
                else:
                    # add interface
                    self._collect_embedded_info_for_beam_path(assembled_mesh, indxes)
            
        else:
            self._collect_embedded_info_for_beam_path(assembled_mesh, beam_cells_idx)

    # ------------------------------------------------------------------
    # Event subscription
    # ------------------------------------------------------------------
    def _subscribe_events(self):  # type: ignore[override]
        """Subscribe this interface to model assembly and TCL export events."""
        events = self._model_events()
        events.subscribe(FemoraEvent.PRE_ASSEMBLE, self._on_pre_assemble)
        events.subscribe(FemoraEvent.POST_ASSEMBLE, self._on_post_assemble)
        events.subscribe(FemoraEvent.EMBEDDED_BEAM_SOLID_TCL, self._on_embedded_beam_solid_tcl_export)

    def _unsubscribe_events(self):  # type: ignore[override]
        """Unsubscribe this interface from all model events."""
        events = self._model_events()
        events.unsubscribe(FemoraEvent.PRE_ASSEMBLE, self._on_pre_assemble)
        events.unsubscribe(FemoraEvent.POST_ASSEMBLE, self._on_post_assemble)
        events.unsubscribe(
            FemoraEvent.EMBEDDED_BEAM_SOLID_TCL, self._on_embedded_beam_solid_tcl_export
        )

    def _on_embedded_beam_solid_tcl_export(self, file_handle, **kwargs):
        """Export OpenSees TCL generation commands for this interface.

        Args:
            file_handle: File-like object to write Tcl script commands to.
            **kwargs: Extra event payload.

        Raises:
            RuntimeError: If the interface is not registered in the manager.
        """
        # print(f"[EmbeddedBeamSolidInterface:{self.name}] Exporting TCL commands.")
        if self._owner is None:
            raise RuntimeError(
                f"EmbeddedBeamSolidInterface '{self.name}' must be managed by InterfaceManager "
                "before TCL export"
            )
        if self.shape != "circle":
            raise NotImplementedError(
                "Tcl export for EmbeddedBeamSolidInterface currently supports only shape='circle'. "
                "Non-circular envelopes are available for Femora-side solid discovery, but the "
                "OpenSees generateInterfacePoints arguments for ellipse/rectangle/polygon are not wired yet."
            )
        if self.beam_part.element is None or not hasattr(self.beam_part.element, "get_transformation"):
            raise NotImplementedError(
                "Tcl export for EmbeddedBeamSolidInterface requires a beam meshpart with "
                "a managed beam element and geometric transformation."
            )
        mesh_maker = self._owner._mesh_maker
        crd_transf_tag = self.beam_part.element.get_transformation().tag
        file_handle.write("set Femora_embeddedBeamSolidStartTag [getFemoraMax eleTag]\n")
        file_handle.write("set Femora_embeddedBeamSolidStartTag [expr $Femora_embeddedBeamSolidStartTag + 1]\n")
        ele_start_tag = mesh_maker._start_ele_tag
        core_start_tag = mesh_maker._start_core_tag
        for ii, info in enumerate(self._instance_embeddedinfo_list):
            core = info.core_number + core_start_tag
            file_handle.write("if {$pid == %d} {\n" % core)
            # for beams, solids in info.beams_solids:
            for jj, (beams, solids) in enumerate(info.beams_solids):
                # handle if elements tags are not starting from 1
                beams_str = " -beamEle ".join(str(b + ele_start_tag) for b in beams)
                solids_str = " -solidEle ".join(str(s + ele_start_tag) for s in solids)
                connect_file = f"EmbeddedBeamSolidConnect_{self.name}_beam{ii}_part{jj}.dat"
                interface_file = f"EmbeddedBeamSolidInterface_{self.name}_beam{ii}_part{jj}.dat"
                connect_file = mesh_maker.get_results_folder() + "/" + connect_file
                interface_file = mesh_maker.get_results_folder() + "/" + interface_file
                if self.write_connectivity:
                    file_handle.write("\tif {[file exists %s] == 1} {file delete %s}\n" % (connect_file, connect_file))
                if self.write_interface:
                    file_handle.write("\tif {[file exists %s] == 1} {file delete %s}\n" % (interface_file, interface_file))
                file_handle.write(
                    f"\tset maxEleTag [generateInterfacePoints -beamEle {beams_str} -solidEle {solids_str} {'-gPenalty' if self.g_penalty else ''} " +
                    f"-shape {self.shape}  -nP {self.n_peri} -nL {self.n_long} -crdTransf {crd_transf_tag} -radius {self.radius} " +
                    f"-penaltyParam {self.penalty_param} -startTag $Femora_embeddedBeamSolidStartTag" +
                    f"{f' -connectivity {connect_file}' if self.write_connectivity else ''}" +
                    f"{f' -file {interface_file}' if self.write_interface else ''}]\n"
                    f"\tset EmbeddedBeamSolid_{self.name}_beam{ii}_part{jj}_startTag $Femora_embeddedBeamSolidStartTag\n"
                    f"\tset EmbeddedBeamSolid_{self.name}_beam{ii}_part{jj}_endTag $maxEleTag\n"
                    # f"\tputs \"EmbeddedBeamSolid_{self.name}_beam{ii}_part{jj} startTag: $EmbeddedBeamSolid_{self.name}_beam{ii}_part{jj}_startTag\"\n"
                    # f"\tputs \"EmbeddedBeamSolid_{self.name}_beam{ii}_part{jj}_endTag: $EmbeddedBeamSolid_{self.name}_beam{ii}_part{jj}_endTag\"\n"
                    f"\tset Femora_embeddedBeamSolidStartTag [expr $maxEleTag + 1]\n"
                    # f"\tputs $Femora_embeddedBeamSolidStartTag\n"
                )
            file_handle.write("}\n")
            file_handle.write("barrier\n")

    def _get_recorder(self, 
                      res_type: list[str],
                      dt: 'float | None' = None,
                      results_folder: str = "",
                      ) -> str:
        """Helper method to construct the OpenSees recorder command for the interface.

        Args:
            res_type: List of response variables to record. Supported variables include
                "displacement", "localDisplacement", "axialDisp", "radialDisp", 
                "tangentialDisp", "globalForce", "localForce", "axialForce",
                "radialForce", "tangentialForce", "solidForce", "beamForce", "beamLocalForce".
            dt: Optional time step interval for recording.
            results_folder: Destination folder for output files.

        Returns:
            The OpenSees Tcl recorder command string.

        Raises:
            RuntimeError: If the interface is not registered in the manager.
        """
        if self._owner is None:
            raise RuntimeError(
                f"EmbeddedBeamSolidInterface '{self.name}' must be managed by InterfaceManager "
                "before recorder export"
            )
        mesh_maker = self._owner._mesh_maker
        core_start_tag = mesh_maker._start_core_tag

        cmd = ""
        for ii, info in enumerate(self._instance_embeddedinfo_list):
            core = info.core_number + core_start_tag
            cmd += "if {$pid == %d} {\n" % core
            for jj, (beams, solids) in enumerate(info.beams_solids):
                startEle = f"EmbeddedBeamSolid_{self.name}_beam{ii}_part{jj}_startTag"
                endEle = f"EmbeddedBeamSolid_{self.name}_beam{ii}_part{jj}_endTag"
                for res in res_type:
                    fileName = f"EmbeddedBeamSolid_{self.name}_beam{ii}_part{jj}_{res}.out"
                    fileName = results_folder + fileName
                    deltaT = "-dT %f" % dt if dt is not None else ""
                    cmd += f"\trecorder Element -file {fileName} -time {deltaT} -eleRange ${startEle} ${endEle} {res}\n"
            cmd += "}\n"
        return cmd

    def _on_pre_assemble(self, **payload):
        """Pre-assemble event listener to reset collected EmbeddedInfo objects.

        Args:
            **payload: Event payload.

        Raises:
            RuntimeError: If the interface is not registered in the manager.
        """
        if self._owner is None:
            raise RuntimeError(
                f"EmbeddedBeamSolidInterface '{self.name}' must be managed by InterfaceManager "
                "before pre-assemble handling"
            )
        self._owner._embeddedinfo_list.clear()
        self._instance_embeddedinfo_list.clear()


if __name__ == "__main__":
    """Quick demo â€“ builds a cube soil mesh and a central pile, then creates
    the EmbeddedBeamSolidInterface and exports a TCL file named
    `embedded_demo.tcl`.
    """
    from femora.core.model import Model
    model = Model()

    # ------------------------------------------------------------------
    # 1. Create materials and elements
    # ------------------------------------------------------------------
    soil_mat = model.material.nd.elastic_isotropic(user_name="Soil", E=30e6, nu=0.3, rho=2000)
    brick_ele = model.element.brick.std(ndof=3, material=soil_mat)

    # Beam â€“ needs section + transformation
    beam_sec = model.section.beam.elastic(user_name="PileSection", E=2e11, A=0.05, Iz=1e-4, Iy=1e-4)
    transf = model.transformation.transformation3d("Linear", 0, 1, 0)  # Local y-axis as vecXZ
    beam_ele = model.element.beam.disp(ndof=6, section=beam_sec, transformation=transf)

    # ------------------------------------------------------------------
    # 2. Create mesh parts
    # ------------------------------------------------------------------
    dx = 0.5
    Nx = int((10 - (-10)) / dx)
    Ny = Nx
    Nz = int((0 - (-20)) / dx)

    model.meshpart.volume.uniform_rectangular_grid(
        user_name="soil",
        element=brick_ele,
        region=None,
        x_min=-10, x_max=10, y_min=-10, y_max=10, z_min=-20, z_max=0,
        nx=Nx, ny=Ny, nz=Nz
    )

    model.meshpart.volume.uniform_rectangular_grid(
        user_name="cap",
        element=brick_ele,
        region=None,
        x_min=-5, x_max=5, y_min=-5, y_max=5, z_min=1, z_max=2,
        nx=10//0.25, ny=10//0.25, nz=1//0.25
    )

    piles = model.meshpart.line.structured_lines(
        user_name="piles",
        element=beam_ele,
        base_point_x=-4,
        base_point_y=-4,
        base_point_z=-8,
        base_vector_1_x=1,
        base_vector_1_y=0,
        base_vector_1_z=0,
        base_vector_2_x=0,
        base_vector_2_y=1,
        base_vector_2_z=0,
        normal_x=0,
        normal_y=0,
        normal_z=1,
        grid_size_1=8,
        grid_size_2=8,
        spacing_1=1.0,
        spacing_2=1.0,
        number_of_lines=10,
        length=10, 
        offset_1=0,
        offset_2=0,
    )

    # ------------------------------------------------------------------
    # 3. Make assembly & interface
    # ------------------------------------------------------------------
    model.assembler.create_section(["soil"], num_partitions=8, merge_points=False)
    model.assembler.create_section(["cap", "piles"], num_partitions=4, merge_points=False)
    interface_radius = 0.25  # Radius for the embedded beam-solid interface
    model.interface.beam_solid_interface(
        name="EmbedTest",
        beam_part="piles",
        radius=interface_radius,
        n_peri=8,
        n_long=5,
        penalty_param=1.0e12,
        g_penalty=True,
    )
    
    model.assembler.assemble()

    import os 
    # change the directory to the current directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # Export TCL (interface will inject its command)
    model.export_to_tcl("embedded_demo.tcl")
    model.assembler.plot(
        show_edges=True, 
        scalars="Core",
        show_grid=True,
    )

    # print("Demo finished â†’ embedded_demo.tcl generated.")
