"""Concrete layer definitions for fiber sections."""

from typing import Dict, Union

import matplotlib.pyplot as plt
import numpy as np

from femora.core.material_base import Material
from femora.components.section.fiber._base import LayerBase


class StraightLayer(LayerBase):
    """Straight layer of fibers between two points."""

    def __init__(self, material: Union[int, str, Material], num_fibers: int, area_per_fiber: float,
                 y1: float, z1: float, y2: float, z2: float):
        try:
            self.num_fibers = int(num_fibers)
            self.area_per_fiber = float(area_per_fiber)
            self.y1 = float(y1)
            self.z1 = float(z1)
            self.y2 = float(y2)
            self.z2 = float(z2)
        except (ValueError, TypeError):
            raise ValueError("Invalid numeric values for straight layer parameters")
        super().__init__(material)

    def plot(self, ax: plt.Axes, material_colors: Dict[str, str],
             show_layer_line: bool = True, show_fibers: bool = True) -> None:
        color = material_colors.get(self.material.user_name, "blue")
        if show_layer_line:
            ax.plot([self.y1, self.y2], [self.z1, self.z2], color=color, linewidth=2, alpha=0.8, linestyle="--")
        if show_fibers:
            if self.num_fibers == 1:
                y_pos = (self.y1 + self.y2) / 2
                z_pos = (self.z1 + self.z2) / 2
                ax.plot(y_pos, z_pos, "s", color=color, markersize=6, alpha=0.8)
            else:
                y_positions = np.linspace(self.y1, self.y2, self.num_fibers)
                z_positions = np.linspace(self.z1, self.z2, self.num_fibers)
                for y_pos, z_pos in zip(y_positions, z_positions):
                    ax.plot(y_pos, z_pos, "s", color=color, markersize=6, alpha=0.8)

    def validate(self) -> None:
        if self.num_fibers <= 0:
            raise ValueError("Number of fibers must be positive")
        if self.area_per_fiber <= 0:
            raise ValueError("Area per fiber must be positive")
        if abs(self.y1 - self.y2) < 1e-12 and abs(self.z1 - self.z2) < 1e-12:
            raise ValueError("Start and end points must be different")

    def to_tcl(self) -> str:
        return f"    layer straight {self.material.tag} {self.num_fibers} {self.area_per_fiber} {self.y1} {self.z1} {self.y2} {self.z2}"

    def get_layer_type(self) -> str:
        return "Straight"


class CircularLayer(LayerBase):
    """Circular layer of fibers along an arc."""

    def __init__(self, material: Union[int, str, Material], num_fibers: int, area_per_fiber: float,
                 y_center: float, z_center: float, radius: float,
                 start_ang: float = 0.0, end_ang: float = None):
        try:
            self.num_fibers = int(num_fibers)
            self.area_per_fiber = float(area_per_fiber)
            self.y_center = float(y_center)
            self.z_center = float(z_center)
            self.radius = float(radius)
            self.end_ang = 360.0 - 360.0 / self.num_fibers if end_ang is None else float(end_ang)
            self.start_ang = float(start_ang)
        except (ValueError, TypeError):
            raise ValueError("Invalid numeric values for circular layer parameters")
        super().__init__(material)

    def plot(self, ax: plt.Axes, material_colors: Dict[str, str],
             show_layer_line: bool = True, show_fibers: bool = True) -> None:
        color = material_colors.get(self.material.user_name, "blue")
        if show_layer_line:
            angles = np.linspace(np.radians(self.start_ang), np.radians(self.end_ang), 100)
            y_arc = self.y_center + self.radius * np.cos(angles)
            z_arc = self.z_center + self.radius * np.sin(angles)
            ax.plot(y_arc, z_arc, color=color, linewidth=2, alpha=0.8, linestyle="--")
        if show_fibers:
            angles = [np.radians(self.start_ang)] if self.num_fibers == 1 else np.linspace(np.radians(self.start_ang), np.radians(self.end_ang), self.num_fibers)
            for angle in angles:
                y_fiber = self.y_center + self.radius * np.cos(angle)
                z_fiber = self.z_center + self.radius * np.sin(angle)
                ax.plot(y_fiber, z_fiber, "s", color=color, markersize=6, alpha=0.8)

    def validate(self) -> None:
        if self.num_fibers <= 0:
            raise ValueError("Number of fibers must be positive")
        if self.area_per_fiber <= 0:
            raise ValueError("Area per fiber must be positive")
        if self.radius <= 0:
            raise ValueError("Radius must be positive")
        self.start_ang = self.start_ang % 360.0
        self.end_ang = self.end_ang % 360.0
        if abs(self.start_ang - self.end_ang) < 1e-12:
            raise ValueError("Start and end angles cannot be the same")

    def to_tcl(self) -> str:
        if abs(self.start_ang) < 1e-12 and abs(self.end_ang - (360.0 - 360.0 / self.num_fibers)) < 1e-12:
            return f"    layer circ {self.material.tag} {self.num_fibers} {self.area_per_fiber} {self.y_center} {self.z_center} {self.radius}"
        return f"    layer circ {self.material.tag} {self.num_fibers} {self.area_per_fiber} {self.y_center} {self.z_center} {self.radius} {self.start_ang} {self.end_ang}"

    def get_layer_type(self) -> str:
        return "Circular"

    def get_arc_length(self) -> float:
        angle_diff = abs(self.end_ang - self.start_ang)
        if angle_diff > 180:
            angle_diff = 360 - angle_diff
        return self.radius * np.radians(angle_diff)

    def is_full_circle(self) -> bool:
        angle_span = abs(self.end_ang - self.start_ang)
        return abs(angle_span - 360.0) < 1e-6 or abs(angle_span) < 1e-6

    def __str__(self) -> str:
        arc_length = self.get_arc_length()
        shape_desc = "Full Circle" if self.is_full_circle() else f"Arc ({self.start_ang:.1f} to {self.end_ang:.1f})"
        return f"Circular Layer: {shape_desc}, R={self.radius}, {self.num_fibers} fibers, arc length={arc_length:.3f}, material '{self.material.user_name}'"
