from typing import Optional

import numpy as np
import pyvista as pv

from femora.constants import FEMORA_MAX_NDF
from femora.core.element_base import Element
from femora.core.meshpart_base import MeshPart
from femora.core.region_base import RegionBase


class StructuredLineMesh(MeshPart):
    """Parametric structured grid of 1D line elements generated along a plane normal.

    This mesh part generates a grid of parallel line elements (beams or columns)
    oriented along a specified vector normal. It is highly useful for structural
    sub-assemblies such as pile group configurations or multi-column bridge piers,
    automatically compiling connectivity and calculating mass distributions.

    Note:
        - Requires a compatible beam element that possesses both a defined cross-section and a coordinate transformation.
        - Rotational and translational masses are integrated per unit length and lumped onto point Mass arrays.

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        sec = model.section.beam.elastic(
            user_name="beam_sec", E=29000.0, A=10.0, Iz=100.0, Iy=100.0
        )
        transf = model.transformation.transformation3d("Linear", 0.0, 1.0, 0.0)
        beam_ele = model.element.beam.disp(ndof=6, section=sec, transformation=transf)

        # Create a 2x2 pile group of vertical structured lines
        piles = model.meshpart.line.structured_lines(
            user_name="pile_group",
            element=beam_ele,
            grid_size_1=1,
            grid_size_2=1,
            spacing_1=5.0,
            spacing_2=5.0,
            length=20.0,
            normal_x=0.0,
            normal_y=0.0,
            normal_z=1.0,
        )
        print(piles.tag)
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__", "is_element_compatible", "generate_mesh"],
    }

    _compatible_elements = ["DispBeamColumn", "ForceBeamColumn", "ElasticBeamColumn", "NonlinearBeamColumn"]

    def __init__(
        self,
        user_name: str,
        element: Element,
        region: Optional[RegionBase] = None,
        *,
        base_point_x: float = 0.0,
        base_point_y: float = 0.0,
        base_point_z: float = 0.0,
        base_vector_1_x: float = 1.0,
        base_vector_1_y: float = 0.0,
        base_vector_1_z: float = 0.0,
        base_vector_2_x: float = 0.0,
        base_vector_2_y: float = 1.0,
        base_vector_2_z: float = 0.0,
        normal_x: float = 0.0,
        normal_y: float = 0.0,
        normal_z: float = 1.0,
        grid_size_1: int = 10,
        grid_size_2: int = 10,
        spacing_1: float = 1.0,
        spacing_2: float = 1.0,
        length: float = 1.0,
        offset_1: float = 0.0,
        offset_2: float = 0.0,
        number_of_lines: int = 1,
        merge_points: bool = True,
    ) -> None:
        """Create a parametric structured grid of line elements.

        Args:
            user_name: Unique user-defined name for this mesh part.
            element: Associated Element template used for discretization.
            region: Physical Region where this mesh part is added.
            base_point_x: X-coordinate of the grid base point.
            base_point_y: Y-coordinate of the grid base point.
            base_point_z: Z-coordinate of the grid base point.
            base_vector_1_x: X-component of the first grid vector direction.
            base_vector_1_y: Y-component of the first grid vector direction.
            base_vector_1_z: Z-component of the first grid vector direction.
            base_vector_2_x: X-component of the second grid vector direction.
            base_vector_2_y: Y-component of the second grid vector direction.
            base_vector_2_z: Z-component of the second grid vector direction.
            normal_x: X-component of the line direction vector (plane normal).
            normal_y: Y-component of the line direction vector (plane normal).
            normal_z: Z-component of the line direction vector (plane normal).
            grid_size_1: Number of cell intervals along the first grid direction.
            grid_size_2: Number of cell intervals along the second grid direction.
            spacing_1: Distance between grid lines along the first direction.
            spacing_2: Distance between grid lines along the second direction.
            length: Length of each line element.
            offset_1: Position offset along the first direction.
            offset_2: Position offset along the second direction.
            number_of_lines: Number of element segments to divide each line.
            merge_points: If True, duplicate nodes at adjacent segment boundaries are merged.

        Raises:
            ValueError: If element is not compatible, grid sizes are negative, spacing or length
                are non-positive, or number_of_lines is less than 1.
            TypeError: If merge_points is not a boolean.
        """
        super().__init__(
            category='line mesh',
            mesh_type='Structured Line Grid',
            user_name=user_name,
            element=element,
            region=region,
        )

        if not self.is_element_compatible(element):
            raise ValueError(
                f"Element type '{element.element_type}' is not compatible with line mesh. "
                f"Must be a beam element with section and transformation."
            )

        self.base_point_x = float(base_point_x)
        self.base_point_y = float(base_point_y)
        self.base_point_z = float(base_point_z)
        self.base_vector_1_x = float(base_vector_1_x)
        self.base_vector_1_y = float(base_vector_1_y)
        self.base_vector_1_z = float(base_vector_1_z)
        self.base_vector_2_x = float(base_vector_2_x)
        self.base_vector_2_y = float(base_vector_2_y)
        self.base_vector_2_z = float(base_vector_2_z)
        self.normal_x = float(normal_x)
        self.normal_y = float(normal_y)
        self.normal_z = float(normal_z)
        self.grid_size_1 = int(grid_size_1)
        self.grid_size_2 = int(grid_size_2)
        self.spacing_1 = float(spacing_1)
        self.spacing_2 = float(spacing_2)
        self.length = float(length)
        self.offset_1 = float(offset_1)
        self.offset_2 = float(offset_2)
        self.number_of_lines = int(number_of_lines)
        if not isinstance(merge_points, bool):
            raise TypeError("merge_points must be a boolean")
        self.merge_points = merge_points

        if self.grid_size_1 < 0:
            raise ValueError("grid_size_1 must be non-negative")
        if self.grid_size_2 < 0:
            raise ValueError("grid_size_2 must be non-negative")
        if self.spacing_1 <= 0:
            raise ValueError("spacing_1 must be positive")
        if self.spacing_2 <= 0:
            raise ValueError("spacing_2 must be positive")
        if self.length <= 0:
            raise ValueError("length must be positive")
        if self.number_of_lines < 1:
            raise ValueError("number_of_lines must be at least 1")

        self.generate_mesh()

    def is_element_compatible(self, element: Element) -> bool:
        """Verify that the element belongs to compatible type families and has cross-section and transformation metadata.

        Args:
            element: Element template to verify.

        Returns:
            bool: True if compatible, False otherwise.
        """
        if not self.is_elemnt_compatible(element.element_type):
            return False
        if not element.get_section() or not element.get_transformation():
            return False
        return True

    def generate_mesh(self) -> pv.UnstructuredGrid:
        """Generate lines grid coordinates, compile connectivity, and compute lumped point Mass arrays.

        Returns:
            pv.UnstructuredGrid: The generated UnstructuredGrid mesh with Point Mass data.
        """
        base_point = np.array([self.base_point_x, self.base_point_y, self.base_point_z])
        base_vector_1 = np.array([
            self.base_vector_1_x,
            self.base_vector_1_y,
            self.base_vector_1_z,
        ])
        base_vector_2 = np.array([
            self.base_vector_2_x,
            self.base_vector_2_y,
            self.base_vector_2_z,
        ])
        normal = np.array([self.normal_x, self.normal_y, self.normal_z])

        base_vector_1 = base_vector_1 / np.linalg.norm(base_vector_1)
        base_vector_2 = base_vector_2 / np.linalg.norm(base_vector_2)
        normal = normal / np.linalg.norm(normal)

        points = []
        lines = []
        point_id = 0

        for i in range(self.grid_size_1 + 1):
            for j in range(self.grid_size_2 + 1):
                grid_point = (
                    base_point
                    + (i * self.spacing_1 + self.offset_1) * base_vector_1
                    + (j * self.spacing_2 + self.offset_2) * base_vector_2
                )

                for k in range(self.number_of_lines):
                    t_start = k / self.number_of_lines
                    t_end = (k + 1) / self.number_of_lines

                    line_start = grid_point + t_start * self.length * normal
                    line_end = grid_point + t_end * self.length * normal

                    points.append(line_start)
                    points.append(line_end)
                    lines.extend([2, point_id, point_id + 1])
                    point_id += 2

        if points:
            points_array = np.array(points)
            poly_mesh = pv.PolyData(points_array, lines=lines)

            if self.merge_points:
                poly_mesh = poly_mesh.merge_points(
                    tolerance=1e-4,
                    inplace=False,
                    progress_bar=False,
                )

            self.mesh = poly_mesh.cast_to_unstructured_grid()
        else:
            self.mesh = pv.PolyData().cast_to_unstructured_grid()

        mass_per_length = self.element.get_mass_per_length()
        Mass = np.zeros((self.mesh.n_points, FEMORA_MAX_NDF), dtype=np.float32)

        if mass_per_length > 0.0 and self.mesh.n_cells > 0:
            section = getattr(self.element, '_section', None)
            transf = getattr(self.element, '_transformation', None)

            for cell_idx in range(self.mesh.n_cells):
                start = self.mesh.offset[cell_idx]
                end = self.mesh.offset[cell_idx + 1]
                point_ids = self.mesh.cell_connectivity[start:end]
                if len(point_ids) != 2:
                    continue

                pid1, pid2 = int(point_ids[0]), int(point_ids[1])
                p1 = self.mesh.points[pid1]
                p2 = self.mesh.points[pid2]
                direction = p2 - p1
                L = float(np.linalg.norm(direction))
                if L <= 0.0:
                    continue

                m = mass_per_length * L / 2.0
                Mass[pid1, :3] += m
                Mass[pid2, :3] += m

                m_rot = m * (L**2) / 4.0
                m_rx, m_ry, m_rz = m_rot, m_rot, m_rot

                if section and hasattr(section, 'get_area') and hasattr(section, 'get_Iy') and hasattr(section, 'get_Iz'):
                    A = section.get_area()
                    if A > 0:
                        rho = mass_per_length / A
                        Iy = section.get_Iy()
                        Iz = section.get_Iz()
                        J = section.get_J() if hasattr(section, 'get_J') and section.get_J() is not None else (Iy + Iz)

                        m_rot_torsion = rho * J * L / 2.0
                        m_rot_iy = rho * Iy * L / 2.0
                        m_rot_iz = rho * Iz * L / 2.0

                        dir_norm = direction / L
                        if transf and hasattr(transf, 'vecxz_x'):
                            x_axis = dir_norm
                            vecxz = np.array([transf.vecxz_x, transf.vecxz_y, transf.vecxz_z], dtype=float)
                            vecxz_norm = np.linalg.norm(vecxz)
                            vecxz = vecxz / vecxz_norm if vecxz_norm > 1e-12 else np.array([0.0, 0.0, 1.0])

                            y_axis = np.cross(vecxz, x_axis)
                            y_axis_norm = np.linalg.norm(y_axis)
                            y_axis = y_axis / y_axis_norm if y_axis_norm > 1e-12 else np.array([0.0, 1.0, 0.0])

                            z_axis = np.cross(x_axis, y_axis)
                            z_axis_norm = np.linalg.norm(z_axis)
                            z_axis = z_axis / z_axis_norm if z_axis_norm > 1e-12 else np.array([0.0, 0.0, 1.0])

                            m_rx = (x_axis[0]**2)*m_rot_torsion + (y_axis[0]**2)*m_rot_iy + (z_axis[0]**2)*m_rot_iz
                            m_ry = (x_axis[1]**2)*m_rot_torsion + (y_axis[1]**2)*m_rot_iy + (z_axis[1]**2)*m_rot_iz
                            m_rz = (x_axis[2]**2)*m_rot_torsion + (y_axis[2]**2)*m_rot_iy + (z_axis[2]**2)*m_rot_iz
                        else:
                            if abs(dir_norm[2]) >= max(abs(dir_norm[0]), abs(dir_norm[1])):
                                m_rx, m_ry, m_rz = m_rot_iz, m_rot_iy, m_rot_torsion
                            elif abs(dir_norm[0]) >= max(abs(dir_norm[1]), abs(dir_norm[2])):
                                m_rx, m_ry, m_rz = m_rot_torsion, m_rot_iy, m_rot_iz
                            else:
                                m_rx, m_ry, m_rz = m_rot_iy, m_rot_torsion, m_rot_iz

                Mass[pid1, 3] += m_rx
                Mass[pid1, 4] += m_ry
                Mass[pid1, 5] += m_rz
                Mass[pid2, 3] += m_rx
                Mass[pid2, 4] += m_ry
                Mass[pid2, 5] += m_rz

        self.mesh.point_data['Mass'] = Mass
        return self.mesh


class SingleLineMesh(MeshPart):
    """Parametric 1D line mesh part defined between two points in 3D space.

    This mesh part discretizes a straight line between a start point `(x0, y0, z0)`
    and an end point `(x1, y1, z1)` into a specified number of segments, automatically
    assigning physical beam element templates and computing consistent lumped point Mass data.

    Note:
        - Requires a compatible beam element that has a valid cross-section and coordinate transformation.
        - Total element mass and rotational inertia are lumped and assigned to generated point arrays.

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        sec = model.section.beam.elastic(
            user_name="column_sec", E=29000.0, A=10.0, Iz=100.0, Iy=100.0
        )
        transf = model.transformation.transformation3d("Linear", 0.0, 1.0, 0.0)
        beam_ele = model.element.beam.disp(ndof=6, section=sec, transformation=transf)

        # Discretize a single vertical column
        column = model.meshpart.line.single_line(
            user_name="pier_column",
            element=beam_ele,
            x0=0.0, y0=0.0, z0=0.0,
            x1=0.0, y1=0.0, z1=15.0,
            number_of_lines=5,
        )
        print(column.tag)
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__", "is_element_compatible", "generate_mesh"],
    }

    _compatible_elements = ["DispBeamColumn", "ForceBeamColumn", "ElasticBeamColumn", "NonlinearBeamColumn"]

    def __init__(
        self,
        user_name: str,
        element: Element,
        region: Optional[RegionBase] = None,
        *,
        x0: float = 0.0,
        y0: float = 0.0,
        z0: float = 0.0,
        x1: float = 1.0,
        y1: float = 0.0,
        z1: float = 0.0,
        number_of_lines: int = 1,
        merge_points: bool = True,
    ) -> None:
        """Create a parametric single line mesh part.

        Args:
            user_name: Unique user-defined name for this mesh part.
            element: Associated Element template used for discretization.
            region: Physical Region where this mesh part is added.
            x0: Start point X-coordinate.
            y0: Start point Y-coordinate.
            z0: Start point Z-coordinate.
            x1: End point X-coordinate.
            y1: End point Y-coordinate.
            z1: End point Z-coordinate.
            number_of_lines: Number of element segments along the line.
            merge_points: If True, duplicate nodes at segment boundaries are merged.

        Raises:
            ValueError: If element is not compatible, start and end points are identical,
                or number_of_lines is less than 1.
            TypeError: If merge_points is not a boolean.
        """
        super().__init__(
            category='line mesh',
            mesh_type='Single Line',
            user_name=user_name,
            element=element,
            region=region,
        )

        if not self.is_element_compatible(element):
            raise ValueError(
                f"Element type '{element.element_type}' is not compatible with line mesh. "
                f"Must be a beam element with section and transformation."
            )

        self.x0 = float(x0)
        self.y0 = float(y0)
        self.z0 = float(z0)
        self.x1 = float(x1)
        self.y1 = float(y1)
        self.z1 = float(z1)
        self.number_of_lines = int(number_of_lines)
        if not isinstance(merge_points, bool):
            raise TypeError("merge_points must be a boolean")
        self.merge_points = merge_points

        if self.number_of_lines < 1:
            raise ValueError("number_of_lines must be at least 1")

        start_point = np.array([self.x0, self.y0, self.z0])
        end_point = np.array([self.x1, self.y1, self.z1])
        if np.allclose(start_point, end_point):
            raise ValueError("Start and end points cannot be the same")

        self.generate_mesh()

    def is_element_compatible(self, element: Element) -> bool:
        """Verify that the element belongs to compatible type families and has cross-section and transformation metadata.

        Args:
            element: Element template to verify.

        Returns:
            bool: True if compatible, False otherwise.
        """
        if not self.is_elemnt_compatible(element.element_type):
            return False
        if not element.get_section() or not element.get_transformation():
            return False
        return True

    def generate_mesh(self) -> pv.PolyData:
        """Generate line coordinate points, connectivity indices, and point Mass data.

        Returns:
            pv.UnstructuredGrid: The generated UnstructuredGrid mesh with point Mass data.
        """
        start_point = np.array([self.x0, self.y0, self.z0])
        end_point = np.array([self.x1, self.y1, self.z1])
        direction = end_point - start_point

        points = []
        lines = []
        point_id = 0

        for i in range(self.number_of_lines):
            t_start = i / self.number_of_lines
            t_end = (i + 1) / self.number_of_lines

            line_start = start_point + t_start * direction
            line_end = start_point + t_end * direction

            points.append(line_start)
            points.append(line_end)
            lines.extend([2, point_id, point_id + 1])
            point_id += 2

        if points:
            points_array = np.array(points)
            poly_mesh = pv.PolyData(points_array, lines=lines)

            if self.merge_points:
                poly_mesh = poly_mesh.merge_points(
                    tolerance=1e-4,
                    inplace=False,
                    progress_bar=False,
                )

            self.mesh = poly_mesh.cast_to_unstructured_grid()
        else:
            self.mesh = pv.PolyData().cast_to_unstructured_grid()

        mass_per_length = self.element.get_mass_per_length()
        L = np.linalg.norm(direction) / self.number_of_lines
        m = mass_per_length * L / 2
        Mass = np.zeros((self.mesh.n_points, FEMORA_MAX_NDF), dtype=np.float32)
        Mass[:, :3] = m

        m_rot = m * (L**2) / 4.0
        m_rx, m_ry, m_rz = m_rot, m_rot, m_rot

        section = getattr(self.element, '_section', None)
        transf = getattr(self.element, '_transformation', None)

        if section and hasattr(section, 'get_area') and hasattr(section, 'get_Iy') and hasattr(section, 'get_Iz'):
            A = section.get_area()
            if A > 0:
                rho = mass_per_length / A
                Iy = section.get_Iy()
                Iz = section.get_Iz()
                J = section.get_J() if hasattr(section, 'get_J') and section.get_J() is not None else (Iy + Iz)

                m_rot_torsion = rho * J * L / 2.0
                m_rot_iy = rho * Iy * L / 2.0
                m_rot_iz = rho * Iz * L / 2.0

                dir_norm = direction / np.linalg.norm(direction)

                if transf and hasattr(transf, 'vecxz_x'):
                    x_axis = dir_norm
                    vecxz = np.array([transf.vecxz_x, transf.vecxz_y, transf.vecxz_z])
                    vecxz_norm = np.linalg.norm(vecxz)
                    if vecxz_norm > 1e-12:
                        vecxz = vecxz / vecxz_norm
                    else:
                        vecxz = np.array([0.0, 0.0, 1.0])

                    y_axis = np.cross(vecxz, x_axis)
                    y_axis_norm = np.linalg.norm(y_axis)
                    if y_axis_norm > 1e-12:
                        y_axis = y_axis / y_axis_norm
                    else:
                        y_axis = np.array([0.0, 1.0, 0.0])

                    z_axis = np.cross(x_axis, y_axis)
                    z_axis_norm = np.linalg.norm(z_axis)
                    if z_axis_norm > 1e-12:
                        z_axis = z_axis / z_axis_norm
                    else:
                        z_axis = np.array([0.0, 0.0, 1.0])

                    m_rx = (x_axis[0]**2)*m_rot_torsion + (y_axis[0]**2)*m_rot_iy + (z_axis[0]**2)*m_rot_iz
                    m_ry = (x_axis[1]**2)*m_rot_torsion + (y_axis[1]**2)*m_rot_iy + (z_axis[1]**2)*m_rot_iz
                    m_rz = (x_axis[2]**2)*m_rot_torsion + (y_axis[2]**2)*m_rot_iy + (z_axis[2]**2)*m_rot_iz
                else:
                    if abs(dir_norm[2]) >= max(abs(dir_norm[0]), abs(dir_norm[1])):
                        m_rx, m_ry, m_rz = m_rot_iz, m_rot_iy, m_rot_torsion
                    elif abs(dir_norm[0]) >= max(abs(dir_norm[1]), abs(dir_norm[2])):
                        m_rx, m_ry, m_rz = m_rot_torsion, m_rot_iy, m_rot_iz
                    else:
                        m_rx, m_ry, m_rz = m_rot_iy, m_rot_torsion, m_rot_iz

        Mass[:, 3] = m_rx
        Mass[:, 4] = m_ry
        Mass[:, 5] = m_rz
        if self.merge_points:
            start_ind = pv.UnstructuredGrid(self.mesh).find_closest_point(start_point)
            end_ind = pv.UnstructuredGrid(self.mesh).find_closest_point(end_point)
            Mass = 2 * Mass
            Mass[start_ind] /= 2.
            Mass[end_ind] /= 2.
        self.mesh.point_data['Mass'] = Mass
        return self.mesh

    @classmethod
    def is_elemnt_compatible(cls, element: str) -> bool:
        """Check if the given element type name is compatible with line meshes.

        Args:
            element: Type name of the element.

        Returns:
            bool: True if compatible, False otherwise.
        """
        return element.lower() in [elem.lower() for elem in cls._compatible_elements]
