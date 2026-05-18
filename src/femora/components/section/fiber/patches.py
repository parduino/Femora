"""Concrete patch definitions for fiber sections."""

from typing import Dict, List, Optional, Tuple, Union

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Polygon, Rectangle, Wedge

from femora.core.material_base import Material
from femora.components.section.fiber._base import PatchBase


class RectangularPatch(PatchBase):
    """Rectangular patch for fiber sections.

    This class defines a rectangular region in a fiber section. The region is
    discretized into a grid of fibers with uniform area and material.

    Tcl form:
        ``patch rect <matTag> <numSubdivY> <numSubdivZ> <yStart> <zStart> <yEnd> <zEnd>``

    Attributes:
        num_subdiv_y: Number of subdivisions along the local y-axis.
        num_subdiv_z: Number of subdivisions along the local z-axis.
        y1: Local y-coordinate of the bottom-left corner.
        z1: Local z-coordinate of the bottom-left corner.
        y2: Local y-coordinate of the top-right corner.
        z2: Local z-coordinate of the top-right corner.

    Example:
        ```python
        import femora as fm

        model = fm.MeshMaker()
        mat = model.material.create_material("Uniaxial", "Steel01", user_name="S", Fy=50.0, E=29000.0, b=0.01)
        
        # FiberSection uses RectangularPatch internally via add_rectangular_patch
        section = model.section.create_section("Fiber", user_name="MyFiberSection")
        section.add_rectangular_patch(
            material=mat,
            num_subdiv_y=4, num_subdiv_z=8,
            y1=-5.0, z1=-10.0,
            y2=5.0, z2=10.0
        )
        ```
    """

    def __init__(self, material: Union[int, str, Material], num_subdiv_y: int, num_subdiv_z: int,
                 y1: float, z1: float, y2: float, z2: float):
        """Create a RectangularPatch with validated geometry.

        Args:
            material: Uniaxial material reference (object, tag, or name).
            num_subdiv_y: Number of fibers along y.
            num_subdiv_z: Number of fibers along z.
            y1: Minimum local y.
            z1: Minimum local z.
            y2: Maximum local y.
            z2: Maximum local z.

        Raises:
            ValueError: If parameters are not numeric, if counts are non-positive,
                or if coordinates are inconsistent (y1 >= y2 or z1 >= z2).
        """
        try:
            self.num_subdiv_y = int(num_subdiv_y)
            self.num_subdiv_z = int(num_subdiv_z)
            self.y1 = float(y1)
            self.z1 = float(z1)
            self.y2 = float(y2)
            self.z2 = float(z2)
        except (ValueError, TypeError):
            raise ValueError("Invalid numeric values for rectangular patch parameters")
        super().__init__(material)

    def plot(self, ax: plt.Axes, material_colors: Dict[str, str],
             show_patch_outline: bool = True, show_fiber_grid: bool = False) -> None:
        """Plot the rectangular patch on matplotlib axes.

        Args:
            ax: Matplotlib axes to plot on.
            material_colors: Dictionary mapping material names to colors.
            show_patch_outline: Whether to draw the rectangle boundary.
            show_fiber_grid: Whether to draw the internal subdivision grid.
        """
        color = material_colors.get(self.material.user_name, "blue")
        if show_patch_outline:
            rect = Rectangle((self.y1, self.z1), self.y2 - self.y1, self.z2 - self.z1,
                             linewidth=2, edgecolor=color, facecolor="none", alpha=0.8)
            ax.add_patch(rect)
        ax.add_patch(Rectangle((self.y1, self.z1), self.y2 - self.y1, self.z2 - self.z1,
                               facecolor=color, edgecolor="none", alpha=0.3))
        if show_fiber_grid:
            y_edges = np.linspace(self.y1, self.y2, self.num_subdiv_y + 1)
            z_edges = np.linspace(self.z1, self.z2, self.num_subdiv_z + 1)
            for y in y_edges:
                ax.plot([y, y], [self.z1, self.z2], color="white", linewidth=0.8, alpha=0.7)
            for z in z_edges:
                ax.plot([self.y1, self.y2], [z, z], color="white", linewidth=0.8, alpha=0.7)

    def validate(self) -> None:
        """Validate the rectangular patch parameters.

        Raises:
            ValueError: If parameters are logically invalid.
        """
        if self.num_subdiv_y <= 0:
            raise ValueError("Number of subdivisions in y-direction must be positive")
        if self.num_subdiv_z <= 0:
            raise ValueError("Number of subdivisions in z-direction must be positive")
        if self.y1 >= self.y2:
            raise ValueError("y1 must be less than y2 for rectangular patch")
        if self.z1 >= self.z2:
            raise ValueError("z1 must be less than z2 for rectangular patch")

    def to_tcl(self) -> str:
        """Render the patch as an OpenSees Tcl command.

        Returns:
            Tcl command string.
        """
        return f"    patch rect {self.material.tag} {self.num_subdiv_y} {self.num_subdiv_z} {self.y1} {self.z1} {self.y2} {self.z2}"

    def get_patch_type(self) -> str:
        """Return the patch type name.

        Returns:
            'Rectangular'.
        """
        return "Rectangular"

    def estimate_fiber_count(self) -> int:
        """Calculate the total number of fibers in this patch.

        Returns:
            Total fiber count.
        """
        return self.num_subdiv_y * self.num_subdiv_z


class QuadrilateralPatch(PatchBase):
    """Quadrilateral patch for fiber sections.

    This class defines a four-sided region in a fiber section. The region is
    discretized into a grid of quadrilateral fibers.

    Tcl form:
        ``patch quad <matTag> <numSubdivIJ> <numSubdivJK> <yI> <zI> <yJ> <zJ> <yK> <zK> <yL> <zL>``

    Attributes:
        num_subdiv_ij: Number of subdivisions along the first edge (I-J).
        num_subdiv_jk: Number of subdivisions along the second edge (J-K).
        vertices: List of 4 (y, z) vertex coordinates in counter-clockwise order.

    Example:
        ```python
        import femora as fm

        model = fm.MeshMaker()
        mat = model.material.create_material("Uniaxial", "Steel01", user_name="S", Fy=50.0, E=29000.0, b=0.01)
        
        # FiberSection uses QuadrilateralPatch internally via add_quadrilateral_patch
        section = model.section.create_section("Fiber", user_name="MyFiberSection")
        section.add_quadrilateral_patch(
            material=mat,
            num_subdiv_ij=4, num_subdiv_jk=4,
            vertices=[(0,0), (10,0), (10,10), (0,10)]
        )
        ```
    """

    def __init__(self, material: Union[int, str, Material], num_subdiv_ij: int, num_subdiv_jk: int,
                 vertices: List[Tuple[float, float]]):
        """Create a QuadrilateralPatch with validated vertices.

        Args:
            material: Uniaxial material reference (object, tag, or name).
            num_subdiv_ij: Subdivisions along the first direction.
            num_subdiv_jk: Subdivisions along the second direction.
            vertices: Exactly 4 vertex coordinates as (y, z) pairs.

        Raises:
            ValueError: If vertices count is not 4 or if parameters are not numeric.
        """
        try:
            self.num_subdiv_ij = int(num_subdiv_ij)
            self.num_subdiv_jk = int(num_subdiv_jk)
            if len(vertices) != 4:
                raise ValueError("Quadrilateral patch requires exactly 4 vertices")
            self.vertices = [(float(y), float(z)) for y, z in vertices]
        except (ValueError, TypeError):
            raise ValueError("Invalid parameters for quadrilateral patch")
        super().__init__(material)

    def plot(self, ax: plt.Axes, material_colors: Dict[str, str],
             show_patch_outline: bool = True, show_fiber_grid: bool = False) -> None:
        """Plot the quadrilateral patch on matplotlib axes.

        Args:
            ax: Matplotlib axes to plot on.
            material_colors: Dictionary mapping material names to colors.
            show_patch_outline: Whether to draw the quadrilateral boundary.
            show_fiber_grid: Whether to draw the internal subdivision grid.
        """
        color = material_colors.get(self.material.user_name, "blue")
        if show_patch_outline:
            quad = Polygon(self.vertices, linewidth=2, edgecolor=color, facecolor="none", alpha=0.8, closed=True)
            ax.add_patch(quad)
        ax.add_patch(Polygon(self.vertices, facecolor=color, edgecolor="none", alpha=0.3, closed=True))
        if show_fiber_grid:
            y_s = np.array([v[0] for v in self.vertices])
            z_s = np.array([v[1] for v in self.vertices])
            edge1y = np.linspace(y_s[0], y_s[1], self.num_subdiv_ij + 1)[1:-1]
            edge2y = np.linspace(y_s[1], y_s[2], self.num_subdiv_jk + 1)[1:-1]
            edge3y = np.linspace(y_s[2], y_s[3], self.num_subdiv_ij + 1)[1:-1][::-1]
            edge4y = np.linspace(y_s[3], y_s[0], self.num_subdiv_jk + 1)[1:-1][::-1]
            edge1z = np.linspace(z_s[0], z_s[1], self.num_subdiv_ij + 1)[1:-1]
            edge2z = np.linspace(z_s[1], z_s[2], self.num_subdiv_jk + 1)[1:-1]
            edge3z = np.linspace(z_s[2], z_s[3], self.num_subdiv_ij + 1)[1:-1][::-1]
            edge4z = np.linspace(z_s[3], z_s[0], self.num_subdiv_jk + 1)[1:-1][::-1]
            for i in range(self.num_subdiv_ij - 1):
                ax.plot([edge1y[i], edge3y[i]], [edge1z[i], edge3z[i]], color="white", linewidth=0.8, alpha=0.7)
            for i in range(self.num_subdiv_jk - 1):
                ax.plot([edge2y[i], edge4y[i]], [edge2z[i], edge4z[i]], color="white", linewidth=0.8, alpha=0.7)

    def validate(self) -> None:
        """Validate the quadrilateral patch parameters.

        Raises:
            ValueError: If subdivisions are non-positive or vertices count is wrong.
        """
        if self.num_subdiv_ij <= 0:
            raise ValueError("Number of subdivisions along I-J edge must be positive")
        if self.num_subdiv_jk <= 0:
            raise ValueError("Number of subdivisions along J-K edge must be positive")
        if len(self.vertices) != 4:
            raise ValueError("Quadrilateral patch requires exactly 4 vertices")

    def to_tcl(self) -> str:
        """Render the patch as an OpenSees Tcl command.

        Returns:
            Tcl command string.
        """
        coords = []
        for y, z in self.vertices:
            coords.extend([str(y), str(z)])
        return f"    patch quad {self.material.tag} {self.num_subdiv_ij} {self.num_subdiv_jk} {' '.join(coords)}"

    def get_patch_type(self) -> str:
        """Return the patch type name.

        Returns:
            'Quadrilateral'.
        """
        return "Quadrilateral"

    def estimate_fiber_count(self) -> int:
        """Calculate the total number of fibers in this patch.

        Returns:
            Total fiber count.
        """
        return self.num_subdiv_ij * self.num_subdiv_jk


class CircularPatch(PatchBase):
    """Circular patch for fiber sections.

    This class defines a circular or arc-shaped region in a fiber section. The
    region is discretized into fibers using polar subdivisions.

    Tcl form:
        ``patch circ <matTag> <numSubdivCirc> <numSubdivRad> <yCenter> <zCenter> <intRad> <extRad> <startAng> <endAng>``

    Attributes:
        num_subdiv_circ: Number of subdivisions in the circumferential direction.
        num_subdiv_rad: Number of subdivisions in the radial direction.
        y_center: Local y-coordinate of the center point.
        z_center: Local z-coordinate of the center point.
        int_rad: Inner radius (0.0 for solid circular patch).
        ext_rad: Outer radius.
        start_ang: Starting angle in degrees.
        end_ang: Ending angle in degrees.

    Example:
        ```python
        import femora as fm

        model = fm.MeshMaker()
        mat = model.material.create_material("Uniaxial", "Concrete01", user_name="C", fpc=-4.0, epsc0=-0.002, fpcu=0.0, epscu=-0.005)
        
        # FiberSection uses CircularPatch internally via add_circular_patch
        section = model.section.create_section("Fiber", user_name="MyFiberSection")
        section.add_circular_patch(
            material=mat,
            num_subdiv_circ=8, num_subdiv_rad=4,
            y_center=0.0, z_center=0.0,
            int_rad=0.0, ext_rad=10.0
        )
        ```
    """

    def __init__(self, material: Union[int, str, Material], num_subdiv_circ: int, num_subdiv_rad: int,
                 y_center: float, z_center: float, int_rad: float, ext_rad: float,
                 start_ang: Optional[float] = 0.0, end_ang: Optional[float] = 360.0):
        """Create a CircularPatch with validated geometry.

        Args:
            material: Uniaxial material reference (object, tag, or name).
            num_subdiv_circ: Subdivisions around the circle.
            num_subdiv_rad: Subdivisions along the radius.
            y_center: Y-coordinate of center.
            z_center: Z-coordinate of center.
            int_rad: Inner radius.
            ext_rad: Outer radius.
            start_ang: Optional starting angle in degrees (default 0.0).
            end_ang: Optional ending angle in degrees (default 360.0).

        Raises:
            ValueError: If parameters are not numeric, if counts/radii are
                non-positive/negative, or if angles are inconsistent.
        """
        try:
            self.num_subdiv_circ = int(num_subdiv_circ)
            self.num_subdiv_rad = int(num_subdiv_rad)
            self.y_center = float(y_center)
            self.z_center = float(z_center)
            self.int_rad = float(int_rad)
            self.ext_rad = float(ext_rad)
            self.start_ang = float(start_ang) if start_ang is not None else 0.0
            self.end_ang = float(end_ang) if end_ang is not None else 360.0
        except (ValueError, TypeError):
            raise ValueError("Invalid parameters for circular patch")
        super().__init__(material)

    def plot(self, ax: plt.Axes, material_colors: Dict[str, str],
             show_patch_outline: bool = True, show_fiber_grid: bool = False) -> None:
        """Plot the circular patch on matplotlib axes.

        Args:
            ax: Matplotlib axes to plot on.
            material_colors: Dictionary mapping material names to colors.
            show_patch_outline: Whether to draw the wedge/circle boundary.
            show_fiber_grid: Whether to draw the internal polar grid.
        """
        color = material_colors.get(self.material.user_name, "blue")
        if show_patch_outline:
            wedge = Wedge((self.y_center, self.z_center), self.ext_rad, self.start_ang, self.end_ang,
                          width=self.ext_rad - self.int_rad, linewidth=2, edgecolor=color, facecolor="none", alpha=0.8)
            ax.add_patch(wedge)
        ax.add_patch(Wedge((self.y_center, self.z_center), self.ext_rad, self.start_ang, self.end_ang,
                           width=self.ext_rad - self.int_rad, facecolor=color, edgecolor="none", alpha=0.3))
        if show_fiber_grid:
            angles = np.linspace(np.radians(self.start_ang), np.radians(self.end_ang), self.num_subdiv_circ + 1)
            yinner = self.int_rad * np.cos(angles) + self.y_center
            zinner = self.int_rad * np.sin(angles) + self.z_center
            youter = self.ext_rad * np.cos(angles) + self.y_center
            zouter = self.ext_rad * np.sin(angles) + self.z_center
            if self.is_solid():
                for i in range(len(angles) - 1):
                    ax.plot([self.y_center, youter[i]], [self.z_center, zouter[i]], color="white", linewidth=0.5, alpha=0.5)
                    ax.plot([self.y_center, youter[i + 1]], [self.z_center, zouter[i + 1]], color="white", linewidth=0.5, alpha=0.5)
            else:
                for i in range(len(yinner) - 1):
                    ax.plot([yinner[i], youter[i]], [zinner[i], zouter[i]], color="white", linewidth=0.5, alpha=0.5)
                    ax.plot([yinner[i + 1], youter[i + 1]], [zinner[i + 1], zouter[i + 1]], color="white", linewidth=0.5, alpha=0.5)
            for r in np.linspace(self.int_rad, self.ext_rad, self.num_subdiv_rad):
                if r < 1e-12:
                    continue
                ax.add_patch(Wedge((self.y_center, self.z_center), r, self.start_ang, self.end_ang,
                                   width=0.0, linewidth=0.5, edgecolor="white", facecolor="none", alpha=1.0))

    def validate(self) -> None:
        """Validate the circular patch parameters.

        Raises:
            ValueError: If parameters are logically invalid (e.g., inner rad > outer rad).
        """
        if self.num_subdiv_circ <= 0:
            raise ValueError("Number of circumferential subdivisions must be positive")
        if self.num_subdiv_rad <= 0:
            raise ValueError("Number of radial subdivisions must be positive")
        if self.int_rad < 0:
            raise ValueError("Inner radius cannot be negative")
        if self.ext_rad <= 0:
            raise ValueError("Outer radius must be positive")
        if self.int_rad >= self.ext_rad:
            raise ValueError("Inner radius must be less than outer radius")
        if self.start_ang >= self.end_ang:
            raise ValueError("Start angle must be less than end angle")
        if self.end_ang - self.start_ang > 360:
            raise ValueError("Angular span cannot exceed 360 degrees")

    def to_tcl(self) -> str:
        """Render the patch as an OpenSees Tcl command.

        Returns:
            Tcl command string.
        """
        cmd = f"    patch circ {self.material.tag} {self.num_subdiv_circ} {self.num_subdiv_rad} "
        cmd += f"{self.y_center} {self.z_center} {self.int_rad} {self.ext_rad} {self.start_ang} {self.end_ang}"
        cmd += f"; # CircularPatch using material {self.material.user_name}"
        return cmd

    def get_patch_type(self) -> str:
        """Return the patch type name.

        Returns:
            'Circular'.
        """
        return "Circular"

    def estimate_fiber_count(self) -> int:
        """Calculate the total number of fibers in this patch.

        Returns:
            Total fiber count.
        """
        return self.num_subdiv_circ * self.num_subdiv_rad

    def is_solid(self) -> bool:
        """Check if the patch is a solid circle (no inner hole).

        Returns:
            True if inner radius is effectively zero.
        """
        return abs(self.int_rad) < 1e-12
