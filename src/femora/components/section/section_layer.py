import numpy as np
from abc import ABC, abstractmethod
from typing import Union, Dict
import matplotlib.pyplot as plt
from femora.components.Material.materialBase import Material
from femora.components.section.section_base import Section


class LayerBase(ABC):
    """
    Abstract base class for layer definitions in fiber sections with enhanced material handling
    """
    
    def __init__(self, material: Union[int, str, Material]):
        self.material = Section.resolve_material(material)
        if self.material is None:
            raise ValueError("Layer requires a valid material")
        self.validate()

    @abstractmethod
    def plot(self, ax: plt.Axes, material_colors: Dict[str, str], 
             show_layer_line: bool = True, show_fibers: bool = True) -> None:
        """Plot the layer on matplotlib axes"""
        pass
    
    @abstractmethod
    def to_tcl(self) -> str:
        """Generate OpenSees TCL command for this layer"""
        pass
    
    @abstractmethod
    def validate(self) -> None:
        """Validate layer parameters"""
        pass
    
    @abstractmethod
    def get_layer_type(self) -> str:
        """Return the layer type name"""
        pass


class StraightLayer(LayerBase):
    """
    Straight layer of fibers between two points with enhanced material handling
    """
    
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
        """Plot straight layer"""
        color = material_colors.get(self.material.user_name, 'blue')
        
        if show_layer_line:
            ax.plot([self.y1, self.y2], [self.z1, self.z2], 
                   color=color, linewidth=2, alpha=0.8, linestyle='--')
        
        if show_fibers:
            if self.num_fibers == 1:
                y_pos = (self.y1 + self.y2) / 2
                z_pos = (self.z1 + self.z2) / 2
                ax.plot(y_pos, z_pos, 's', color=color, markersize=6, alpha=0.8)
            else:
                y_positions = np.linspace(self.y1, self.y2, self.num_fibers)
                z_positions = np.linspace(self.z1, self.z2, self.num_fibers)
                
                for y_pos, z_pos in zip(y_positions, z_positions):
                    ax.plot(y_pos, z_pos, 's', color=color, markersize=6, alpha=0.8)
    
    def validate(self) -> None:
        """Validate straight layer parameters"""
        if self.num_fibers <= 0:
            raise ValueError("Number of fibers must be positive")
        if self.area_per_fiber <= 0:
            raise ValueError("Area per fiber must be positive")
        
        # Check that start and end points are different
        if abs(self.y1 - self.y2) < 1e-12 and abs(self.z1 - self.z2) < 1e-12:
            raise ValueError("Start and end points must be different")
    
    def to_tcl(self) -> str:
        """Generate OpenSees TCL command for straight layer"""
        return f"    layer straight {self.material.tag} {self.num_fibers} {self.area_per_fiber} {self.y1} {self.z1} {self.y2} {self.z2}"
    
    def get_layer_type(self) -> str:
        return "Straight"



class CircularLayer(LayerBase):
    """
    Circular layer of fibers along a circular arc with enhanced material handling
    """
    def __init__(self, material: Union[int, str, Material], num_fibers: int, area_per_fiber: float,
                 y_center: float, z_center: float, radius: float,
                 start_ang: float = 0.0, end_ang: float = None):
        try:
            self.num_fibers = int(num_fibers)
            self.area_per_fiber = float(area_per_fiber)
            self.y_center = float(y_center)
            self.z_center = float(z_center)
            self.radius = float(radius)
            if end_ang is None:
                self.end_ang = 360.0 - 360.0/self.num_fibers
            else:
                self.end_ang = float(end_ang)
            self.start_ang = float(start_ang)
        except (ValueError, TypeError):
            raise ValueError("Invalid numeric values for circular layer parameters")
        super().__init__(material)

    def plot(self, ax: plt.Axes, material_colors: Dict[str, str], 
             show_layer_line: bool = True, show_fibers: bool = True) -> None:
        color = material_colors.get(self.material.user_name, 'blue')
        if show_layer_line:
            angles = np.linspace(np.radians(self.start_ang), np.radians(self.end_ang), 100)
            y_arc = self.y_center + self.radius * np.cos(angles)
            z_arc = self.z_center + self.radius * np.sin(angles)
            ax.plot(y_arc, z_arc, color=color, linewidth=2, alpha=0.8, linestyle='--')
        if show_fibers:
            if self.num_fibers == 1:
                angles = [np.radians(self.start_ang)]
            else:
                angles = np.linspace(np.radians(self.start_ang), np.radians(self.end_ang), self.num_fibers)
            for angle in angles:
                y_fiber = self.y_center + self.radius * np.cos(angle)
                z_fiber = self.z_center + self.radius * np.sin(angle)
                ax.plot(y_fiber, z_fiber, 's', color=color, markersize=6, alpha=0.8)

    def validate(self) -> None:
        if self.num_fibers <= 0:
            raise ValueError("Number of fibers must be positive")
        if self.area_per_fiber <= 0:
            raise ValueError("Area per fiber must be positive")
        if self.radius <= 0:
            raise ValueError("Radius must be positive")
        # Normalize angles
        self.start_ang = self.start_ang % 360.0
        self.end_ang = self.end_ang % 360.0
        if abs(self.start_ang - self.end_ang) < 1e-12:
            raise ValueError("Start and end angles cannot be the same")

    def to_tcl(self) -> str:
        # Use default angles if appropriate
        if abs(self.start_ang) < 1e-12 and abs(self.end_ang - (360.0 - 360.0/self.num_fibers)) < 1e-12:
            return f"    layer circ {self.material.tag} {self.num_fibers} {self.area_per_fiber} {self.y_center} {self.z_center} {self.radius}"
        else:
            return f"    layer circ {self.material.tag} {self.num_fibers} {self.area_per_fiber} {self.y_center} {self.z_center} {self.radius} {self.start_ang} {self.end_ang}"

    def get_layer_type(self) -> str:
        return "Circular"


    def get_arc_length(self) -> float:
        """Calculate arc length of the layer"""
        angle_diff = abs(self.end_ang - self.start_ang)


        if angle_diff > 180:  # Handle wrap-around case


            angle_diff = 360 - angle_diff


        return self.radius * np.radians(angle_diff)


    def is_full_circle(self) -> bool:
        """Check if this layer forms a complete circle"""


        angle_span = abs(self.end_ang - self.start_ang)


        return abs(angle_span - 360.0) < 1e-6 or abs(angle_span) < 1e-6


    def __str__(self) -> str:
        arc_length = self.get_arc_length()
        shape_desc = "Full Circle" if self.is_full_circle() else f"Arc ({self.start_ang:.1f}° to {self.end_ang:.1f}°)"
        return f"Circular Layer: {shape_desc}, R={self.radius}, {self.num_fibers} fibers, arc length={arc_length:.3f}, material '{self.material.user_name}'"