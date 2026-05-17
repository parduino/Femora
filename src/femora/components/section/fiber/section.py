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
    """Fiber-discretized section for nonlinear analysis."""

    def __init__(
        self,
        user_name: str = "Unnamed",
        GJ: Optional[float] = None,
        components: Optional[List[Union[FiberElement, PatchBase, LayerBase]]] = None,
    ) -> None:
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
        """Add an individual fiber to the section."""
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
        """Add a rectangular patch to the section."""
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
        """Add a quadrilateral patch to the section."""
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
        """Add a circular patch to the section."""
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
        """Add a straight layer of fibers to the section."""
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
        """Add a circular layer of fibers to the section."""
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
        """Generate complete OpenSees Tcl command for the section."""
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
        """Get all materials used by this section."""
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
        """Return list of ``(area, y, z)`` contributions for section properties."""
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
        """Compute total area by summing discretized contributions."""
        return float(sum(a for a, _, _ in self._discretize_to_fibers()))

    def get_Iy(self) -> float:
        """Compute the centroidal second moment about the local y-axis."""
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
        """Compute the centroidal second moment about the local z-axis."""
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
        """Approximate the polar moment as ``Iy + Iz``."""
        return float(self.get_Iy() + self.get_Iz())

    def clear_fibers(self) -> None:
        """Remove all individual fibers."""
        self.fibers.clear()

    def clear_patches(self) -> None:
        """Remove all patches."""
        self.patches.clear()

    def clear_layers(self) -> None:
        """Remove all layers."""
        self.layers.clear()

    def clear_all(self) -> None:
        """Remove all fibers, patches, and layers."""
        self.clear_fibers()
        self.clear_patches()
        self.clear_layers()

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
        """Plot the complete fiber section."""
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
        """Static method to plot fiber section components."""
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

    def _generate_material_colors(self) -> Dict[str, str]:
        """Generate color mapping for materials."""
        return self.generate_material_colors(self.fibers, self.patches, self.layers)

    @staticmethod
    def generate_material_colors(
        fibers: List[FiberElement],
        patches: List[PatchBase],
        layers: List[LayerBase],
    ) -> Dict[str, str]:
        """Generate a material-to-color mapping."""
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

    def _calculate_scale_factor(self) -> float:
        """Calculate appropriate scale factor for fiber visualization."""
        return self.calculate_scale_factor(self.fibers)

    @staticmethod
    def calculate_scale_factor(fibers: List[FiberElement]) -> float:
        """Calculate a display scale factor for fiber markers."""
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

    def _add_legend(self, ax: plt.Axes, material_colors: Dict[str, str]) -> None:
        """Add legend showing materials."""
        self._add_legend_to_axes(ax, material_colors)

    @staticmethod
    def _add_legend_to_axes(ax: plt.Axes, material_colors: Dict[str, str]) -> None:
        """Add legend showing materials."""
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

    def _add_section_info(self, ax: plt.Axes) -> None:
        """Add section information text."""
        self._add_section_info_to_axes(ax, self.fibers, self.patches, self.layers)

    @staticmethod
    def _add_section_info_to_axes(
        ax: plt.Axes,
        fibers: List[FiberElement],
        patches: List[PatchBase],
        layers: List[LayerBase],
    ) -> None:
        """Add section information text to the axes."""
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
