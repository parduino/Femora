"""Fiber section implementation."""

from __future__ import annotations

import math
from typing import Dict, List, Optional, Tuple, Union

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np

from femora.core.material_base import Material
from femora.core.section_base import Section
from femora.components.section.fiber._base import LayerBase, PatchBase
from femora.components.section.fiber.element import FiberElement
from femora.components.section.fiber.layers import CircularLayer, StraightLayer
from femora.components.section.fiber.patches import (
    CircularPatch,
    QuadrilateralPatch,
    RectangularPatch,
)


class FiberSection(Section):
    """General cross-section discretized into a collection of fibers.

    The Fiber section is the most general section type in Femora. It allows
    modeling arbitrary geometries by defining individual fibers, patches (grids),
    or layers (lines/arcs) of uniaxial materials. The section response is
    obtained by integrating the response of each fiber over the area.

    Tcl form:
        ``section Fiber <tag> [-GJ <gj>] { <fiber/patch/layer commands> }``

    Note:
        - Geometric properties (Area, Iy, Iz, J) are computed automatically by
          discretizing all components into individual fibers and summing their
          contributions.
        - OpenSees does not prevent overlapping fibers; if two fibers occupy the
          same space, their contributions are summed, effectively doubling the
          stiffness and strength at that location.
        - The `GJ` parameter provides a linear torsional stiffness that is
          independent of the fibers.

    Tip:
        - Use the `plot()` method frequently during model development to verify
          that your fibers and patches are correctly positioned.
        - For large models, be mindful of the total fiber count. While more
          fibers increase accuracy, they also increase computation time.
        - If your section only needs flexure in one plane, consider
          [WFSection2d][femora.components.section.beam.wf2d.WFSection2d] for
          simplicity.

    Example:
        ```python
        from femora.core.model import Model
        import femora.components.section.fiber  # noqa: F401

        model = Model()
        concr = model.material.uniaxial.elastic(user_name="Concrete", E=3600.0)
        steel = model.material.uniaxial.steel01(
            user_name="Steel",
            Fy=60.0,
            E0=29000.0,
            b=0.01,
        )
        sec = model.section.fiber.section(user_name="RC_Beam", GJ=1000.0)
        sec.add_rectangular_patch(
            material=concr,
            num_subdiv_y=10,
            num_subdiv_z=10,
            y1=-5,
            z1=-5,
            y2=5,
            z2=5,
        )
        sec.add_fiber(y_loc=-4.5, z_loc=-4.5, area=0.44, material=steel)
        print(sec.tag)
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": [
            "__init__",
            "add_fiber",
            "add_rectangular_patch",
            "add_quadrilateral_patch",
            "add_circular_patch",
            "add_straight_layer",
            "add_circular_layer",
            "get_area",
            "get_Iy",
            "get_Iz",
            "get_J",
            "plot",
            "clear_all",
        ],
    }

    def __init__(
        self,
        user_name: str = "Unnamed",
        GJ: Optional[float] = None,
        components: Optional[List[Union[FiberElement, PatchBase, LayerBase]]] = None,
    ) -> None:
        """Create a FiberSection with optional initial components.

        Args:
            user_name: Unique identifier for the section.
            GJ: Optional linear torsional stiffness constant. If provided,
                this stiffness is added to the section's torsional response.
            components: Optional list of pre-created fiber elements, patches,
                or layers to populate the section.

        Raises:
            ValueError: If GJ is not numeric or is non-positive.
        """
        if GJ is not None:
            try:
                GJ = float(GJ)
            except (TypeError, ValueError) as exc:
                raise ValueError("GJ must be a positive number") from exc
            if GJ <= 0:
                raise ValueError("GJ must be a positive number")

        super().__init__("section", "Fiber", user_name)

        self.fibers: List[FiberElement] = []
        self.patches: List[PatchBase] = []
        self.layers: List[LayerBase] = []
        self.GJ = GJ

        if components is not None:
            for i, component in enumerate(components):
                if isinstance(component, FiberElement):
                    self.fibers.append(component)
                elif isinstance(component, PatchBase):
                    self.patches.append(component)
                elif isinstance(component, LayerBase):
                    self.layers.append(component)
                else:
                    raise ValueError(
                        f"Item {i} in components list is not a valid fiber section component",
                    )

        all_materials = self.get_materials()
        self.material = all_materials[0] if all_materials else None

    def add_fiber(
        self,
        y_loc: float,
        z_loc: float,
        area: float,
        material: Union[int, str, Material],
    ) -> None:
        """Add an individual fiber at a specific (y, z) location.

        Args:
            y_loc: Local y-coordinate of the fiber center.
            z_loc: Local z-coordinate of the fiber center.
            area: Cross-sectional area of the fiber.
            material: Uniaxial material reference for the fiber.
        """
        fiber = FiberElement(y_loc, z_loc, area, material)
        self.fibers.append(fiber)
        if self.material is None:
            self.material = fiber.material

    def add_rectangular_patch(
        self,
        material: Union[int, str, Material],
        num_subdiv_y: int,
        num_subdiv_z: int,
        y1: float,
        z1: float,
        y2: float,
        z2: float,
    ) -> None:
        """Add a rectangular patch discretized into a grid of fibers.

        Args:
            material: Uniaxial material reference for all fibers in the patch.
            num_subdiv_y: Number of fibers along the local y-axis.
            num_subdiv_z: Number of fibers along the local z-axis.
            y1: Minimum local y-coordinate of the rectangle.
            z1: Minimum local z-coordinate of the rectangle.
            y2: Maximum local y-coordinate of the rectangle.
            z2: Maximum local z-coordinate of the rectangle.
        """
        patch = RectangularPatch(material, num_subdiv_y, num_subdiv_z, y1, z1, y2, z2)
        self.patches.append(patch)
        if self.material is None:
            self.material = patch.material

    def add_quadrilateral_patch(
        self,
        material: Union[int, str, Material],
        num_subdiv_ij: int,
        num_subdiv_jk: int,
        vertices: list,
    ) -> None:
        """Add a four-sided patch discretized into fibers.

        Args:
            material: Uniaxial material reference.
            num_subdiv_ij: Subdivisions along the first direction (edge 1-2).
            num_subdiv_jk: Subdivisions along the second direction (edge 2-3).
            vertices: Exactly 4 (y, z) vertex pairs defining the boundary.
        """
        patch = QuadrilateralPatch(material, num_subdiv_ij, num_subdiv_jk, vertices)
        self.patches.append(patch)
        if self.material is None:
            self.material = patch.material

    def add_circular_patch(
        self,
        material: Union[int, str, Material],
        num_subdiv_circ: int,
        num_subdiv_rad: int,
        y_center: float,
        z_center: float,
        int_rad: float,
        ext_rad: float,
        start_ang: float = 0.0,
        end_ang: float = 360.0,
    ) -> None:
        """Add a circular or arc-shaped patch.

        Args:
            material: Uniaxial material reference.
            num_subdiv_circ: Circumferential subdivisions.
            num_subdiv_rad: Radial subdivisions.
            y_center: Y-coordinate of the circle center.
            z_center: Z-coordinate of the circle center.
            int_rad: Inner radius (0 for solid circle).
            ext_rad: Outer radius.
            start_ang: Starting angle in degrees.
            end_ang: Ending angle in degrees.
        """
        patch = CircularPatch(
            material,
            num_subdiv_circ,
            num_subdiv_rad,
            y_center,
            z_center,
            int_rad,
            ext_rad,
            start_ang,
            end_ang,
        )
        self.patches.append(patch)
        if self.material is None:
            self.material = patch.material

    def add_straight_layer(
        self,
        material: Union[int, str, Material],
        num_fibers: int,
        area_per_fiber: float,
        y1: float,
        z1: float,
        y2: float,
        z2: float,
    ) -> None:
        """Add a straight line of fibers.

        Args:
            material: Uniaxial material reference.
            num_fibers: Number of fibers along the line.
            area_per_fiber: Cross-sectional area of each fiber.
            y1: Y-coordinate of start point.
            z1: Z-coordinate of start point.
            y2: Y-coordinate of end point.
            z2: Z-coordinate of end point.
        """
        layer = StraightLayer(material, num_fibers, area_per_fiber, y1, z1, y2, z2)
        self.layers.append(layer)
        if self.material is None:
            self.material = layer.material

    def add_circular_layer(
        self,
        material: Union[int, str, Material],
        num_fibers: int,
        area_per_fiber: float,
        y_center: float,
        z_center: float,
        radius: float,
        start_ang: float = 0.0,
        end_ang: Optional[float] = None,
    ) -> None:
        """Add a circular arc of fibers.

        Args:
            material: Uniaxial material reference.
            num_fibers: Number of fibers along the arc.
            area_per_fiber: Cross-sectional area of each fiber.
            y_center: Y-coordinate of arc center.
            z_center: Z-coordinate of arc center.
            radius: Arc radius.
            start_ang: Optional starting angle in degrees.
            end_ang: Optional ending angle in degrees.
        """
        layer = CircularLayer(
            material,
            num_fibers,
            area_per_fiber,
            y_center,
            z_center,
            radius,
            start_ang,
            end_ang,
        )
        self.layers.append(layer)
        if self.material is None:
            self.material = layer.material

    def to_tcl(self) -> str:
        """Render the complete Fiber section command block.

        Returns:
            str: Tcl command block including nested fiber, patch, and layer commands.

        Raises:
            ValueError: If this section has not been added to a manager.
        """
        cmd = f"section Fiber {self._require_tag()}"
        if self.GJ is not None:
            cmd += f" -GJ {self.GJ}"
        cmd += " {\n"
        for fiber in self.fibers:
            cmd += fiber.to_tcl() + "\n"
        for patch in self.patches:
            cmd += patch.to_tcl() + "\n"
        for layer in self.layers:
            cmd += layer.to_tcl() + "\n"
        cmd += f"}}; # {self.user_name}"
        return cmd

    def get_materials(self) -> List[Material]:
        """Return all unique materials used in the section.

        Returns:
            List of unique Material objects found in any component.
        """
        materials: List[Material] = []
        for fiber in self.fibers:
            if fiber.material not in materials:
                materials.append(fiber.material)
        for patch in self.patches:
            if patch.material not in materials:
                materials.append(patch.material)
        for layer in self.layers:
            if layer.material not in materials:
                materials.append(layer.material)
        return materials

    def _discretize_to_fibers(self) -> List[tuple]:
        """Convert all high-level components into explicit (area, y, z) points.

        This method is used internally to calculate aggregate section properties
        like Area and Inertia.

        Returns:
            List of tuples: (area, y, z).
        """
        fibers = []
        for fiber in self.fibers:
            fibers.append((fiber.area, fiber.y_loc, fiber.z_loc))

        for layer in self.layers:
            if isinstance(layer, StraightLayer):
                if layer.num_fibers <= 0:
                    continue
                ys = [
                    layer.y1 + (i + 0.5) * (layer.y2 - layer.y1) / layer.num_fibers
                    for i in range(layer.num_fibers)
                ]
                zs = [
                    layer.z1 + (i + 0.5) * (layer.z2 - layer.z1) / layer.num_fibers
                    for i in range(layer.num_fibers)
                ]
                for y, z in zip(ys, zs):
                    fibers.append((layer.area_per_fiber, y, z))
            elif isinstance(layer, CircularLayer):
                if layer.num_fibers <= 0:
                    continue
                if layer.num_fibers == 1:
                    angles = [math.radians(layer.start_ang)]
                else:
                    angles = list(
                        np.linspace(
                            math.radians(layer.start_ang),
                            math.radians(layer.end_ang),
                            layer.num_fibers,
                        ),
                    )
                for ang in angles:
                    y = layer.y_center + layer.radius * math.cos(ang)
                    z = layer.z_center + layer.radius * math.sin(ang)
                    fibers.append((layer.area_per_fiber, y, z))

        for patch in self.patches:
            if isinstance(patch, RectangularPatch):
                ny = patch.num_subdiv_y
                nz = patch.num_subdiv_z
                dy = (patch.y2 - patch.y1) / ny
                dz = (patch.z2 - patch.z1) / nz
                for i in range(ny):
                    y = patch.y1 + (i + 0.5) * dy
                    for j in range(nz):
                        z = patch.z1 + (j + 0.5) * dz
                        fibers.append((dy * dz, y, z))
            elif isinstance(patch, QuadrilateralPatch):
                ni = patch.num_subdiv_ij
                nj = patch.num_subdiv_jk
                vertices = patch.vertices
                for i in range(ni):
                    s0 = i / ni
                    s1 = (i + 1) / ni
                    for j in range(nj):
                        t0 = j / nj
                        t1 = (j + 1) / nj

                        def bilinear(s: float, t: float) -> Tuple[float, float]:
                            x = (
                                (1 - s) * (1 - t) * vertices[0][0]
                                + s * (1 - t) * vertices[1][0]
                                + s * t * vertices[2][0]
                                + (1 - s) * t * vertices[3][0]
                            )
                            y = (
                                (1 - s) * (1 - t) * vertices[0][1]
                                + s * (1 - t) * vertices[1][1]
                                + s * t * vertices[2][1]
                                + (1 - s) * t * vertices[3][1]
                            )
                            return x, y

                        c00 = bilinear(s0, t0)
                        c10 = bilinear(s1, t0)
                        c11 = bilinear(s1, t1)
                        c01 = bilinear(s0, t1)
                        xs = [c00[0], c10[0], c11[0], c01[0]]
                        ys = [c00[1], c10[1], c11[1], c01[1]]
                        area = 0.0
                        for k in range(4):
                            k1 = (k + 1) % 4
                            area += xs[k] * ys[k1] - xs[k1] * ys[k]
                        area = 0.5 * abs(area)
                        yc = sum(xs) / 4.0
                        zc = sum(ys) / 4.0
                        fibers.append((area, yc, zc))
            elif isinstance(patch, CircularPatch):
                nr = patch.num_subdiv_rad
                nc = patch.num_subdiv_circ
                theta0 = math.radians(patch.start_ang)
                theta1 = math.radians(patch.end_ang)
                if theta1 <= theta0:
                    theta1 += 2 * math.pi
                dtheta = (theta1 - theta0) / nc
                for ir in range(nr):
                    r_in = patch.int_rad + ir * (patch.ext_rad - patch.int_rad) / nr
                    r_out = patch.int_rad + (ir + 1) * (patch.ext_rad - patch.int_rad) / nr
                    for ic in range(nc):
                        th0 = theta0 + ic * dtheta
                        th1 = theta0 + (ic + 1) * dtheta
                        area = 0.5 * (th1 - th0) * (r_out * r_out - r_in * r_in)
                        if abs(r_out - r_in) < 1e-12:
                            r_cent = 0.5 * (r_in + r_out)
                        else:
                            r_cent = (2.0 / 3.0) * (r_out**3 - r_in**3) / (r_out**2 - r_in**2)
                        th_cent = 0.5 * (th0 + th1)
                        y = patch.y_center + r_cent * math.cos(th_cent)
                        z = patch.z_center + r_cent * math.sin(th_cent)
                        fibers.append((area, y, z))

        return fibers

    def get_area(self) -> float:
        """Calculate the total cross-sectional area from fibers.

        Returns:
            The sum of all fiber areas.
        """
        return float(sum(a for a, _, _ in self._discretize_to_fibers()))

    def get_Iy(self) -> float:
        """Calculate the second moment of area about the local y-axis.

        Returns:
            The computed Iy value.
        """
        comps = self._discretize_to_fibers()
        if not comps:
            return 0.0
        area = sum(a for a, _, _ in comps)
        if area <= 0:
            return 0.0
        z_bar = sum(a * z for a, _, z in comps) / area
        Iy = 0.0
        for a, _, z in comps:
            Iy += a * (z - z_bar) ** 2
        return float(Iy)

    def get_Iz(self) -> float:
        """Calculate the second moment of area about the local z-axis.

        Returns:
            The computed Iz value.
        """
        comps = self._discretize_to_fibers()
        if not comps:
            return 0.0
        area = sum(a for a, _, _ in comps)
        if area <= 0:
            return 0.0
        y_bar = sum(a * y for a, y, _ in comps) / area
        Iz = 0.0
        for a, y, _ in comps:
            Iz += a * (y - y_bar) ** 2
        return float(Iz)

    def get_J(self) -> float:
        """Approximate the torsional constant as Iy + Iz.

        Note:
            This is a geometric polar moment of inertia approximation. If explicit
            torsional stiffness is needed, use the `GJ` parameter in the
            constructor.

        Returns:
            Sum of Iy and Iz.
        """
        return float(self.get_Iy() + self.get_Iz())

    def clear_all(self) -> None:
        """Remove all fibers, patches, and layers from the section."""
        self.fibers.clear()
        self.patches.clear()
        self.layers.clear()

    def plot(
        self,
        ax: Optional[plt.Axes] = None,
        figsize: Tuple[float, float] = (10, 8),
        show_fibers: bool = True,
        show_patches: bool = True,
        show_layers: bool = True,
        show_patch_outline: bool = True,
        show_fiber_grid: bool = True,
        show_layer_line: bool = True,
        title: Optional[str] = None,
        material_colors: Optional[Dict[str, str]] = None,
        save_path: Optional[str] = None,
        dpi: int = 300,
    ) -> plt.Figure:
        """Visualize the fiber section geometry using Matplotlib.

        Args:
            ax: Optional Matplotlib axes. If None, a new figure is created.
            figsize: Figure size for the new plot.
            show_fibers: Whether to draw small markers at each fiber location.
            show_patches: Whether to draw filled polygons for patches.
            show_layers: Whether to draw markers/lines for layers.
            show_patch_outline: Whether to highlight the boundaries of patches.
            show_fiber_grid: Whether to draw internal grid lines for patches.
            show_layer_line: Whether to draw the center-line of layers.
            title: Optional plot title.
            material_colors: Optional map from material names to color strings.
            save_path: Optional file path to save the image.
            dpi: Resolution for the saved image.

        Returns:
            The Matplotlib Figure object.
        """
        if title is None:
            title = f"Fiber Section: {self.user_name} (Tag: {self._require_tag()})"
        all_materials = self.get_materials()
        self.material = all_materials[0] if all_materials else None
        return self.plot_components(
            fibers=self.fibers,
            patches=self.patches,
            layers=self.layers,
            ax=ax,
            figsize=figsize,
            show_fibers=show_fibers,
            show_patches=show_patches,
            show_layers=show_layers,
            show_patch_outline=show_patch_outline,
            show_fiber_grid=show_fiber_grid,
            show_layer_line=show_layer_line,
            title=title,
            material_colors=material_colors,
            save_path=save_path,
            dpi=dpi,
        )

    @staticmethod
    def plot_components(
        fibers: List[FiberElement],
        patches: List[PatchBase],
        layers: List[LayerBase],
        ax: Optional[plt.Axes] = None,
        figsize: Tuple[float, float] = (10, 8),
        show_fibers: bool = True,
        show_patches: bool = True,
        show_layers: bool = True,
        show_patch_outline: bool = True,
        show_fiber_grid: bool = True,
        show_layer_line: bool = True,
        title: Optional[str] = None,
        material_colors: Optional[Dict[str, str]] = None,
        save_path: Optional[str] = None,
        dpi: int = 300,
    ) -> plt.Figure:
        """Static utility to plot arbitrary fiber section components.

        Args:
            fibers: Individual fiber elements to draw.
            patches: Patch components to draw.
            layers: Layer components to draw.
            ax: Optional Matplotlib axes. If None, a new figure is created.
            figsize: Figure size for the new plot.
            show_fibers: Whether to draw small markers at each fiber location.
            show_patches: Whether to draw filled polygons for patches.
            show_layers: Whether to draw markers or lines for layers.
            show_patch_outline: Whether to highlight patch boundaries.
            show_fiber_grid: Whether to draw internal grid lines for patches.
            show_layer_line: Whether to draw the center-line of layers.
            title: Optional plot title.
            material_colors: Optional map from material names to color strings.
            save_path: Optional file path to save the image.
            dpi: Resolution for the saved image.

        Returns:
            The Matplotlib Figure object.
        """
        if ax is None:
            fig, ax = plt.subplots(figsize=figsize)
        else:
            fig = ax.get_figure()

        if material_colors is None:
            material_colors = FiberSection.generate_material_colors(fibers, patches, layers)

        scale_factor = FiberSection.calculate_scale_factor(fibers)

        if show_fibers:
            for fiber in fibers:
                fiber.plot(ax, material_colors, scale_factor, show_fibers=True)
        if show_patches:
            for patch in patches:
                patch.plot(ax, material_colors, show_patch_outline, show_fiber_grid)
        if show_layers:
            for layer in layers:
                layer.plot(ax, material_colors, show_layer_line, show_fibers)

        ax.set_xlabel("Y Coordinate")
        ax.set_ylabel("Z Coordinate")
        ax.set_aspect("equal")
        if title is not None:
            ax.set_title(title)

        FiberSection._add_legend_to_axes(ax, material_colors)
        FiberSection._add_section_info_to_axes(ax, fibers, patches, layers)
        fig.tight_layout()

        if save_path:
            fig.savefig(save_path, dpi=dpi, bbox_inches="tight")

        return fig

    @staticmethod
    def generate_material_colors(
        fibers: List[FiberElement],
        patches: List[PatchBase],
        layers: List[LayerBase],
    ) -> Dict[str, str]:
        """Generate a stable color mapping for materials in the section."""
        materials = []
        for fiber in fibers:
            if fiber.material not in materials:
                materials.append(fiber.material)
        for patch in patches:
            if patch.material not in materials:
                materials.append(patch.material)
        for layer in layers:
            if layer.material not in materials:
                materials.append(layer.material)
        colors = [
            "tab:blue",
            "tab:orange",
            "tab:green",
            "tab:red",
            "tab:purple",
            "tab:brown",
            "tab:pink",
            "tab:gray",
            "tab:olive",
            "tab:cyan",
        ]
        material_colors: Dict[str, str] = {}
        for i, material in enumerate(materials):
            material_colors[material.user_name] = colors[i % len(colors)]
        return material_colors

    @staticmethod
    def calculate_scale_factor(fibers: List[FiberElement]) -> float:
        """Determine a visualization scale factor based on fiber distribution."""
        if not fibers:
            return 1.0
        y_coords = [fiber.y_loc for fiber in fibers]
        z_coords = [fiber.z_loc for fiber in fibers]
        if not y_coords or not z_coords:
            return 1.0
        y_range = max(y_coords) - min(y_coords)
        z_range = max(z_coords) - min(z_coords)
        coord_range = max(y_range, z_range)
        if coord_range == 0:
            return 1.0
        return coord_range / 50.0

    @staticmethod
    def _add_legend_to_axes(ax: plt.Axes, material_colors: Dict[str, str]) -> None:
        if not material_colors:
            return
        legend_elements = [
            mpatches.Patch(color=color, label=material_name)
            for material_name, color in material_colors.items()
        ]
        if legend_elements:
            ax.legend(
                handles=legend_elements,
                loc="upper left",
                bbox_to_anchor=(1.02, 1),
                borderaxespad=0.0,
            )

    @staticmethod
    def _add_section_info_to_axes(
        ax: plt.Axes,
        fibers: List[FiberElement],
        patches: List[PatchBase],
        layers: List[LayerBase],
    ) -> None:
        total_fibers = len(fibers)
        for patch in patches:
            total_fibers += patch.estimate_fiber_count()
        for layer in layers:
            if hasattr(layer, "num_fibers"):
                total_fibers += layer.num_fibers
        info_text = (
            f"Fibers: {len(fibers)}\n"
            f"Patches: {len(patches)}\n"
            f"Layers: {len(layers)}\n"
            f"Est. Total Fibers: {total_fibers}"
        )
        ax.text(
            1.03,
            0.02,
            info_text,
            transform=ax.transAxes,
            horizontalalignment="left",
            verticalalignment="bottom",
            bbox={"boxstyle": "round", "facecolor": "white", "alpha": 0.8},
        )
