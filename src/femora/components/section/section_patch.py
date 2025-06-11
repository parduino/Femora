from abc import ABC, abstractmethod
from typing import Union, Dict, List, Tuple, Optional
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Wedge, Polygon
from femora.components.Material.materialBase import Material
from femora.components.section.section_base import Section


class PatchBase(ABC):
    """
    Abstract base class for all patch types in fiber sections with enhanced material handling
    """
    
    def __init__(self, material: Union[int, str, Material]):
        self.material = Section.resolve_material(material)
        if self.material is None:
            raise ValueError("Patch requires a valid material")
        self.validate()

    @abstractmethod
    def plot(self, ax: plt.Axes, material_colors: Dict[str, str], 
             show_patch_outline: bool = True, show_fiber_grid: bool = False) -> None:
        """Plot the patch on matplotlib axes"""
        pass
    
    @abstractmethod
    def to_tcl(self) -> str:
        """Generate OpenSees TCL command for this patch"""
        pass
    
    @abstractmethod
    def validate(self) -> None:
        """Validate patch parameters"""
        pass
    
    @abstractmethod
    def get_patch_type(self) -> str:
        """Return the patch type name"""
        pass
    
    @abstractmethod
    def estimate_fiber_count(self) -> int:
        """Estimate the number of fibers this patch will generate"""
        pass


class RectangularPatch(PatchBase):
    """
    Rectangular patch for fiber sections with enhanced material handling
    """
    
    def __init__(self, material: Union[int, str, Material], num_subdiv_y: int, num_subdiv_z: int,
                 y1: float, z1: float, y2: float, z2: float):
        # Store parameters before calling parent (which calls validate)
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
        """Plot rectangular patch"""
        color = material_colors.get(self.material.user_name, 'blue')
        
        if show_patch_outline:
            rect = Rectangle((self.y1, self.z1), self.y2 - self.y1, self.z2 - self.z1,
                     linewidth=2, edgecolor=color, facecolor='none', alpha=0.8)
            ax.add_patch(rect)

        # Draw filled rectangle
        ax.add_patch(Rectangle((self.y1, self.z1), self.y2 - self.y1, self.z2 - self.z1,
                       facecolor=color, edgecolor='none', alpha=0.3))

        # Draw grid lines if requested
        if show_fiber_grid:
            y_edges = np.linspace(self.y1, self.y2, self.num_subdiv_y + 1)
            z_edges = np.linspace(self.z1, self.z2, self.num_subdiv_z + 1)
            for y in y_edges:
                ax.plot([y, y], [self.z1, self.z2], color="white", linewidth=0.8, alpha=0.7)
            for z in z_edges:
                ax.plot([self.y1, self.y2], [z, z], color="white", linewidth=0.8, alpha=0.7)
    
    def validate(self) -> None:
        """Validate rectangular patch parameters"""
        if self.num_subdiv_y <= 0:
            raise ValueError("Number of subdivisions in y-direction must be positive")
        if self.num_subdiv_z <= 0:
            raise ValueError("Number of subdivisions in z-direction must be positive")
        if self.y1 >= self.y2:
            raise ValueError("y1 must be less than y2 for rectangular patch")
        if self.z1 >= self.z2:
            raise ValueError("z1 must be less than z2 for rectangular patch")
    
    def to_tcl(self) -> str:
        """Generate OpenSees TCL command for rectangular patch"""
        return f"    patch rect {self.material.tag} {self.num_subdiv_y} {self.num_subdiv_z} {self.y1} {self.z1} {self.y2} {self.z2}"
    
    def get_patch_type(self) -> str:
        return "Rectangular"
    
    def estimate_fiber_count(self) -> int:
        return self.num_subdiv_y * self.num_subdiv_z



class QuadrilateralPatch(PatchBase):
    """
    Quadrilateral patch for fiber sections
    """
    def __init__(self, material: Union[int, str, Material], num_subdiv_ij: int, num_subdiv_jk: int,
                 vertices: List[Tuple[float, float]]):
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
        color = material_colors.get(self.material.user_name, 'blue')
        if show_patch_outline:
            quad = Polygon(self.vertices, linewidth=2, edgecolor=color, facecolor='none', alpha=0.8, closed=True)
            ax.add_patch(quad)
        ax.add_patch(Polygon(self.vertices, facecolor=color, edgecolor='none', alpha=0.3, closed=True))
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
        if self.num_subdiv_ij <= 0:
            raise ValueError("Number of subdivisions along I-J edge must be positive")
        if self.num_subdiv_jk <= 0:
            raise ValueError("Number of subdivisions along J-K edge must be positive")
        if len(self.vertices) != 4:
            raise ValueError("Quadrilateral patch requires exactly 4 vertices")
        # Could add more geometric validation here

    def to_tcl(self) -> str:
        coords = []
        for y, z in self.vertices:
            coords.extend([str(y), str(z)])
        coords_str = " ".join(coords)
        return f"    patch quad {self.material.tag} {self.num_subdiv_ij} {self.num_subdiv_jk} {coords_str}"

    def get_patch_type(self) -> str:
        return "Quadrilateral"

    def estimate_fiber_count(self) -> int:
        return self.num_subdiv_ij * self.num_subdiv_jk


class CircularPatch(PatchBase):
    """
    Circular patch for fiber sections
    """
    def __init__(self, material: Union[int, str, Material], num_subdiv_circ: int, num_subdiv_rad: int,
                 y_center: float, z_center: float, int_rad: float, ext_rad: float,
                 start_ang: Optional[float] = 0.0, end_ang: Optional[float] = 360.0):
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
        color = material_colors.get(self.material.user_name, 'blue')
        if show_patch_outline:
            wedge = Wedge((self.y_center, self.z_center), self.ext_rad, self.start_ang, self.end_ang,
                          width=self.ext_rad - self.int_rad, linewidth=2, edgecolor=color, facecolor='none', alpha=0.8)
            ax.add_patch(wedge)
        ax.add_patch(Wedge((self.y_center, self.z_center), self.ext_rad, self.start_ang, self.end_ang,
                           width=self.ext_rad - self.int_rad, facecolor=color, edgecolor='none', alpha=0.3))
        if show_fiber_grid:
            angles = np.linspace(np.radians(self.start_ang), np.radians(self.end_ang), self.num_subdiv_circ + 1)
            yinner = self.int_rad * np.cos(angles) + self.y_center
            zinner = self.int_rad * np.sin(angles) + self.z_center
            youter = self.ext_rad * np.cos(angles) + self.y_center
            zouter = self.ext_rad * np.sin(angles) + self.z_center
            if self.is_solid():
                for i in range(len(angles) - 1):
                    ax.plot([self.y_center, youter[i]], [self.z_center, zouter[i]], color="white", linewidth=0.5, alpha=0.5)
                    ax.plot([self.y_center, youter[i+1]], [self.z_center, zouter[i+1]], color="white", linewidth=0.5, alpha=0.5)
            else:
                for i in range(len(yinner) - 1):
                    ax.plot([yinner[i], youter[i]], [zinner[i], zouter[i]], color="white", linewidth=0.5, alpha=0.5)
                    ax.plot([yinner[i+1], youter[i+1]], [zinner[i+1], zouter[i+1]], color="white", linewidth=0.5, alpha=0.5)
            for r in np.linspace(self.int_rad, self.ext_rad, self.num_subdiv_rad):
                if r < 1e-12:
                    continue
                ax.add_patch(Wedge((self.y_center, self.z_center), r, self.start_ang, self.end_ang,
                                   width=0.00, linewidth=0.5, edgecolor="white", facecolor='none', alpha=1.0))

    def validate(self) -> None:
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
        cmd = f"    patch circ {self.material.tag} {self.num_subdiv_circ} {self.num_subdiv_rad} "
        cmd += f"{self.y_center} {self.z_center} {self.int_rad} {self.ext_rad}"
        if self.start_ang != 0.0 or self.end_ang != 360.0:
            cmd += f" {self.start_ang} {self.end_ang}"
        return cmd

    def get_patch_type(self) -> str:
        return "Circular"

    def estimate_fiber_count(self) -> int:
        return self.num_subdiv_circ * self.num_subdiv_rad

    def is_solid(self) -> bool:
        return abs(self.int_rad) < 1e-12

