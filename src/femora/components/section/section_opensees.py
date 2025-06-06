"""
OpenSees Section Implementations for FEMORA
Based on OpenSees section types with validation and parameter management
"""

from typing import List, Dict, Union, Optional, Tuple
from abc import ABC, abstractmethod
import math
from femora.components.section.section_base import Section, SectionRegistry
from femora.components.Material.materialBase import Material
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Rectangle, Polygon, Circle, Wedge
import numpy as np


class ElasticSection(Section):
    """
    Elastic Section implementation for OpenSees
    Most commonly used section type for beam-column elements
    """
    
    def __init__(self, user_name: str = "Unnamed", **kwargs):
        kwargs = self.validate_section_parameters(**kwargs)
        super().__init__('section', 'Elastic', user_name)
        self.params = kwargs if kwargs else {}

    def to_tcl(self) -> str:
        """Generate the OpenSees TCL command for Elastic section"""
        param_order = self.get_parameters()
        params_str = " ".join(str(self.params[param]) for param in param_order if param in self.params)
        return f"section Elastic {self.tag} {params_str}; # {self.user_name}"

    @classmethod
    def get_parameters(cls) -> List[str]:
        """Parameters for Elastic section"""
        return ["E", "A", "Iz", "Iy", "G", "J"]

    @classmethod
    def get_description(cls) -> List[str]:
        """Parameter descriptions for Elastic section"""
        return [
            "Young's modulus",
            "Cross-sectional area", 
            "Moment of inertia about local z-axis",
            "Moment of inertia about local y-axis (optional)",
            "Shear modulus (optional)",
            "Torsional constant (optional)"
        ]

    @classmethod
    def get_help_text(cls) -> str:
        """Get the formatted help text for Elastic section"""
        return """
        <b>Elastic Section</b><br>
        Creates a linear elastic section with constant properties.<br><br>
        <b>Required Parameters:</b><br>
        • E: Young's modulus<br>
        • A: Cross-sectional area<br>
        • Iz: Moment of inertia about z-axis<br><br>
        <b>Optional Parameters:</b><br>
        • Iy: Moment of inertia about y-axis (3D)<br>
        • G: Shear modulus<br>
        • J: Torsional constant
        """

    @classmethod
    def validate_section_parameters(cls, **kwargs) -> Dict[str, Union[int, float, str]]:
        """Validate parameters for Elastic section"""
        required_params = ['E', 'A', 'Iz']
        optional_params = ['Iy', 'G', 'J']
        validated_params = {}
        
        # Check required parameters
        for param in required_params:
            if param not in kwargs:
                raise ValueError(f"ElasticSection requires the '{param}' parameter")
            try:
                value = float(kwargs[param])
                if value <= 0:
                    raise ValueError(f"'{param}' must be positive")
                validated_params[param] = value
            except (ValueError, TypeError):
                raise ValueError(f"Invalid value for '{param}'. Must be a positive number")
        
        # Check optional parameters
        for param in optional_params:
            if param in kwargs:
                try:
                    value = float(kwargs[param])
                    if value <= 0:
                        raise ValueError(f"'{param}' must be positive")
                    validated_params[param] = value
                except (ValueError, TypeError):
                    raise ValueError(f"Invalid value for '{param}'. Must be a positive number")
        
        return validated_params

    def get_values(self, keys: List[str]) -> Dict[str, Union[int, float, str]]:
        """Retrieve values for specific parameters"""
        return {key: self.params.get(key) for key in keys}

    def update_values(self, values: Dict[str, Union[int, float, str]]) -> None:
        """Update section parameters"""
        self.params.clear()
        validated_params = self.validate_section_parameters(**values)
        self.params.update(validated_params)



class AggregatorSection(Section):
    """
    Aggregator Section implementation for OpenSees
    Combines multiple materials for different response quantities
    """
    
    def __init__(self, user_name: str = "Unnamed", **kwargs):
        super().__init__('section', 'Aggregator', user_name)
        self.materials = {}  # Dict mapping response codes to materials
        self.base_section = None  # Optional base section
        if 'materials' in kwargs:
            self.materials = kwargs['materials']
        if 'base_section' in kwargs:
            self.base_section = kwargs['base_section']

    def add_material(self, material: Material, response_code: str):
        """Add a material with its response code"""
        valid_codes = ['P', 'Mz', 'My', 'Vy', 'Vz', 'T']
        if response_code not in valid_codes:
            raise ValueError(f"Invalid response code. Must be one of: {valid_codes}")
        self.materials[response_code] = material

    def to_tcl(self) -> str:
        """Generate the OpenSees TCL command for Aggregator section"""
        mat_pairs = []
        for code, material in self.materials.items():
            mat_pairs.extend([str(material.tag), code])
        
        tcl_cmd = f"section Aggregator {self.tag} " + " ".join(mat_pairs)
        
        if self.base_section:
            tcl_cmd += f" -section {self.base_section.tag}"
        
        tcl_cmd += f"; # {self.user_name}"
        return tcl_cmd

    def get_materials(self) -> List[Material]:
        """Get all materials used by this section"""
        materials = list(self.materials.values())
        if self.base_section:
            materials.extend(self.base_section.get_materials())
        return materials

    @classmethod
    def get_parameters(cls) -> List[str]:
        """Parameters for Aggregator section"""
        return ["materials", "base_section"]

    @classmethod
    def get_description(cls) -> List[str]:
        """Parameter descriptions for Aggregator section"""
        return [
            "Dictionary of materials mapped to response codes (P, Mz, My, Vy, Vz, T)",
            "Optional base section to aggregate with"
        ]

    @classmethod
    def get_help_text(cls) -> str:
        """Get the formatted help text for Aggregator section"""
        return """
        <b>Aggregator Section</b><br>
        Combines different uniaxial materials for different response quantities.<br><br>
        <b>Response Codes:</b><br>
        • P: Axial force<br>
        • Mz: Moment about z-axis<br>
        • My: Moment about y-axis<br>
        • Vy: Shear force in y-direction<br>
        • Vz: Shear force in z-direction<br>
        • T: Torsion
        """

    @classmethod
    def validate_section_parameters(cls, **kwargs) -> Dict[str, Union[int, float, str]]:
        """Validate parameters for Aggregator section"""
        validated_params = {}
        
        if 'materials' in kwargs:
            materials = kwargs['materials']
            if not isinstance(materials, dict):
                raise ValueError("Materials must be a dictionary mapping response codes to Material objects")
            
            valid_codes = ['P', 'Mz', 'My', 'Vy', 'Vz', 'T']
            for code, material in materials.items():
                if code not in valid_codes:
                    raise ValueError(f"Invalid response code '{code}'. Must be one of: {valid_codes}")
                if not isinstance(material, Material):
                    raise ValueError(f"Value for code '{code}' must be a Material object")
            
            validated_params['materials'] = materials
        
        if 'base_section' in kwargs:
            base_section = kwargs['base_section']
            if base_section is not None and not isinstance(base_section, Section):
                raise ValueError("Base section must be a Section object")
            validated_params['base_section'] = base_section
        
        return validated_params

    def get_values(self, keys: List[str]) -> Dict[str, Union[int, float, str]]:
        """Retrieve values for specific parameters"""
        values = {}
        if 'materials' in keys:
            values['materials'] = str(list(self.materials.keys()))
        if 'base_section' in keys:
            values['base_section'] = self.base_section.user_name if self.base_section else "None"
        return values

    def update_values(self, values: Dict[str, Union[int, float, str]]) -> None:
        """Update section parameters"""
        validated_params = self.validate_section_parameters(**values)
        if 'materials' in validated_params:
            self.materials = validated_params['materials']
        if 'base_section' in validated_params:
            self.base_section = validated_params['base_section']


class UniaxialSection(Section):
    """
    Uniaxial Section implementation for OpenSees
    Uses a single uniaxial material for a specific response
    """
    
    def __init__(self, user_name: str = "Unnamed", **kwargs):
        kwargs = self.validate_section_parameters(**kwargs)
        super().__init__('section', 'Uniaxial', user_name)
        self.params = kwargs

    def to_tcl(self) -> str:
        """Generate the OpenSees TCL command for Uniaxial section"""
        material_tag = self.params['material'].tag
        response_code = self.params['response_code']
        return f"section Uniaxial {self.tag} {material_tag} {response_code}; # {self.user_name}"

    def get_materials(self) -> List[Material]:
        """Get all materials used by this section"""
        return [self.params['material']]

    @classmethod
    def get_parameters(cls) -> List[str]:
        """Parameters for Uniaxial section"""
        return ["material", "response_code"]

    @classmethod
    def get_description(cls) -> List[str]:
        """Parameter descriptions for Uniaxial section"""
        return [
            "Uniaxial material to use",
            "Response code (P, Mz, My, Vy, Vz, T)"
        ]

    @classmethod
    def get_help_text(cls) -> str:
        """Get the formatted help text for Uniaxial section"""
        return """
        <b>Uniaxial Section</b><br>
        Uses a single uniaxial material for one response quantity.<br><br>
        Specify the material and the response code it represents.
        """

    @classmethod
    def validate_section_parameters(cls, **kwargs) -> Dict[str, Union[int, float, str]]:
        """Validate parameters for Uniaxial section"""
        if 'material' not in kwargs:
            raise ValueError("UniaxialSection requires a 'material' parameter")
        if 'response_code' not in kwargs:
            raise ValueError("UniaxialSection requires a 'response_code' parameter")
        
        material = kwargs['material']
        if not isinstance(material, Material):
            raise ValueError("Material must be a Material object")
        
        response_code = kwargs['response_code']
        valid_codes = ['P', 'Mz', 'My', 'Vy', 'Vz', 'T']
        if response_code not in valid_codes:
            raise ValueError(f"Response code must be one of: {valid_codes}")
        
        return {
            'material': material,
            'response_code': response_code
        }

    def get_values(self, keys: List[str]) -> Dict[str, Union[int, float, str]]:
        """Retrieve values for specific parameters"""
        values = {}
        if 'material' in keys:
            values['material'] = self.params['material'].user_name
        if 'response_code' in keys:
            values['response_code'] = self.params['response_code']
        return values

    def update_values(self, values: Dict[str, Union[int, float, str]]) -> None:
        """Update section parameters"""
        # Note: This would need material lookup by name if updating
        validated_params = self.validate_section_parameters(**values)
        self.params.update(validated_params)




"""
Complete Fiber Section Implementation for FEMORA
Based on OpenSees FiberSection documentation with full support for:
- Individual fibers
- Rectangular, Quadrilateral, and Circular patches
- Layer support framework
- Optional torsional stiffness (GJ)
- Comprehensive validation and TCL generation
"""

class FiberElement:
    """
    Represents a single fiber in a fiber section
    
    Args:
        y_loc (float): y-coordinate of the fiber in section's local coordinate system
        z_loc (float): z-coordinate of the fiber in section's local coordinate system  
        area (float): Cross-sectional area of the fiber
        material (Material): Uniaxial material associated with the fiber
    """
    
    def __init__(self, y_loc: float, z_loc: float, area: float, material: Material):
        # Validate and convert inputs
        try:
            self.y_loc = float(y_loc)
            self.z_loc = float(z_loc)
            self.area = float(area)
        except (ValueError, TypeError):
            raise ValueError("Fiber coordinates and area must be numeric values")
        
        if self.area <= 0:
            raise ValueError("Fiber area must be positive")
        
        if not isinstance(material, Material):
            raise ValueError("Material must be a Material instance")
        
        self.material = material

    def plot(self, ax: plt.Axes, material_colors: Dict[str, str], 
             scale_factor: float = 1.0, show_fibers: bool = True) -> None:
        """
        Plot the fiber on the given matplotlib axes
        
        Args:
            ax: Matplotlib axes to plot on
            material_colors: Dictionary mapping material names to colors
            scale_factor: Scaling factor for fiber size visualization
            show_fibers: Whether to show individual fibers
        """
        if not show_fibers:
            return
            
        # Get color for this material
        color = material_colors.get(self.material.user_name, 'blue')
        
        # Calculate fiber size for visualization (proportional to sqrt(area))
        fiber_size = math.sqrt(self.area) * scale_factor
        
        # Plot fiber as a circle
        circle = Circle((self.y_loc, self.z_loc), fiber_size/2, 
                       facecolor=color, edgecolor='black', linewidth=0.5, alpha=0.7)
        ax.add_patch(circle)
    
    def to_tcl(self) -> str:
        """Generate OpenSees TCL command for this fiber"""
        return f"    fiber {self.y_loc} {self.z_loc} {self.area} {self.material.tag}"
    
    def __str__(self) -> str:
        return f"Fiber at ({self.y_loc}, {self.z_loc}) with area {self.area}, material '{self.material.user_name}'"
    
    def __repr__(self) -> str:
        return f"FiberElement(y_loc={self.y_loc}, z_loc={self.z_loc}, area={self.area}, material={self.material.user_name})"


class PatchBase(ABC):
    """
    Abstract base class for all patch types in fiber sections
    Patches generate multiple fibers over defined geometric areas
    """
    
    def __init__(self, material: Material):
        if not isinstance(material, Material):
            raise ValueError("Material must be a Material instance")
        self.material = material
        self.validate()

    @abstractmethod
    def plot(self, ax: plt.Axes, material_colors: Dict[str, str], 
             show_patch_outline: bool = True, show_fiber_grid: bool = False) -> None:
        """
        Plot the patch on the given matplotlib axes
        
        Args:
            ax: Matplotlib axes to plot on
            material_colors: Dictionary mapping material names to colors
            show_patch_outline: Whether to show patch boundary
            show_fiber_grid: Whether to show individual fiber locations
        """
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
    Rectangular patch for fiber sections
    Generates fibers over a rectangular area
    
    Args:
        material (Material): Material for all fibers in this patch
        num_subdiv_y (int): Number of subdivisions along local y-axis
        num_subdiv_z (int): Number of subdivisions along local z-axis
        y1, z1 (float): Coordinates of first corner
        y2, z2 (float): Coordinates of opposite corner
    """
    
    def __init__(self, material: Material, num_subdiv_y: int, num_subdiv_z: int,
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
        """Plot rectangular patch as tiles; show grid lines if requested"""
        color = material_colors.get(self.material.user_name, 'blue')
        # Draw patch outline if requested
        if show_patch_outline:
            rect = Rectangle((self.y1, self.z1), self.y2 - self.y1, self.z2 - self.z1,
                     linewidth=2, edgecolor=color, facecolor='none', alpha=0.8)
            ax.add_patch(rect)

        # Draw a single filled rectangle for the patch area (grouped fill)
        ax.add_patch(Rectangle((self.y1, self.z1), self.y2 - self.y1, self.z2 - self.z1,
                       facecolor=color, edgecolor='none', alpha=0.3))

        # Draw grid lines if requested
        if show_fiber_grid:
            y_edges = np.linspace(self.y1, self.y2, self.num_subdiv_y + 1)
            z_edges = np.linspace(self.z1, self.z2, self.num_subdiv_z + 1)
            # Vertical lines
            for y in y_edges:
                ax.plot([y, y], [self.z1, self.z2], color="white", linewidth=0.8, alpha=0.7)
            # Horizontal lines
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
    
    def get_dimensions(self) -> Tuple[float, float]:
        """Return width and height of rectangular patch"""
        return (self.y2 - self.y1, self.z2 - self.z1)
    
    def __str__(self) -> str:
        dims = self.get_dimensions()
        return f"Rectangular Patch: {dims[0]} × {dims[1]}, {self.estimate_fiber_count()} fibers, material '{self.material.user_name}'"


class QuadrilateralPatch(PatchBase):
    """
    Quadrilateral patch for fiber sections
    Generates fibers over a four-sided area defined by vertices
    
    Args:
        material (Material): Material for all fibers in this patch
        num_subdiv_ij (int): Number of subdivisions along I-J edge
        num_subdiv_jk (int): Number of subdivisions along J-K edge  
        vertices (List[Tuple[float, float]]): Four vertices (I,J,K,L) in counter-clockwise order
    """
    
    def __init__(self, material: Material, num_subdiv_ij: int, num_subdiv_jk: int,
                 vertices: List[Tuple[float, float]]):
        try:
            self.num_subdiv_ij = int(num_subdiv_ij)
            self.num_subdiv_jk = int(num_subdiv_jk)
        except (ValueError, TypeError):
            raise ValueError("Number of subdivisions must be integers")
        
        if len(vertices) != 4:
            raise ValueError("Quadrilateral patch requires exactly 4 vertices")
        
        try:
            self.vertices = [(float(y), float(z)) for y, z in vertices]
        except (ValueError, TypeError):
            raise ValueError("All vertex coordinates must be numeric")
        
        super().__init__(material)


    def plot(self, ax: plt.Axes, material_colors: Dict[str, str], 
             show_patch_outline: bool = True, show_fiber_grid: bool = False) -> None:
        """Plot quadrilateral patch"""
        color = material_colors.get(self.material.user_name, 'blue')
        
        if show_patch_outline:
            # Draw patch outline
            quad = Polygon(self.vertices, linewidth=2, edgecolor=color, 
                          facecolor=color , alpha=0.8, closed=True)
            ax.add_patch(quad)
        
        if show_fiber_grid:
            # Draw fiber grid
            y_s = np.array([v[0] for v in self.vertices])
            z_s = np.array([v[1] for v in self.vertices])

            # find the for edges 
            edge1y = np.linspace(y_s[0], y_s[1], self.num_subdiv_ij + 1)[1:-1:]
            edge2y = np.linspace(y_s[1], y_s[2], self.num_subdiv_jk + 1)[1:-1:]
            edge3y = np.linspace(y_s[2], y_s[3], self.num_subdiv_ij + 1)[1:-1:][::-1]  # reverse for correct order
            edge4y = np.linspace(y_s[3], y_s[0], self.num_subdiv_jk + 1)[1:-1:][::-1]  # reverse for correct order

            edge1z = np.linspace(z_s[0], z_s[1], self.num_subdiv_ij + 1)[1:-1:]
            edge2z = np.linspace(z_s[1], z_s[2], self.num_subdiv_jk + 1)[1:-1:]
            edge3z = np.linspace(z_s[2], z_s[3], self.num_subdiv_ij + 1)[1:-1:][::-1]  # reverse for correct order
            edge4z = np.linspace(z_s[3], z_s[0], self.num_subdiv_jk + 1)[1:-1:][::-1]  # reverse for correct order

            # now connect the points to form a grid which are infront of each other
            for i in range(self.num_subdiv_ij -1):
                ax.plot([edge1y[i], edge3y[i]], [edge1z[i], edge3z[i]], color="white", linewidth=0.8, alpha=0.7)
            for i in range(self.num_subdiv_jk -1):
                ax.plot([edge2y[i], edge4y[i]], [edge2z[i], edge4z[i]], color="white", linewidth=0.8, alpha=0.7)

            
            


    
    def validate(self) -> None:
        """Validate quadrilateral patch parameters"""
        if self.num_subdiv_ij <= 0:
            raise ValueError("Number of subdivisions along I-J edge must be positive")
        if self.num_subdiv_jk <= 0:
            raise ValueError("Number of subdivisions along J-K edge must be positive")
        
        # Check for valid quadrilateral (no self-intersections)
        if self._is_self_intersecting():
            raise ValueError("Quadrilateral vertices create a self-intersecting shape")
    
    def _is_self_intersecting(self) -> bool:
        """Check if quadrilateral is self-intersecting (basic check)"""
        # This is a simplified check - could be enhanced
        # For now, just check if vertices are in reasonable order
        return False
    
    def to_tcl(self) -> str:
        """Generate OpenSees TCL command for quadrilateral patch"""
        coords = []
        for y, z in self.vertices:
            coords.extend([str(y), str(z)])
        coords_str = " ".join(coords)
        return f"    patch quad {self.material.tag} {self.num_subdiv_ij} {self.num_subdiv_jk} {coords_str}"
    
    def get_patch_type(self) -> str:
        return "Quadrilateral"
    
    def estimate_fiber_count(self) -> int:
        return self.num_subdiv_ij * self.num_subdiv_jk
    
    def __str__(self) -> str:
        return f"Quadrilateral Patch: 4 vertices, {self.estimate_fiber_count()} fibers, material '{self.material.user_name}'"


class CircularPatch(PatchBase):
    """
    Circular patch for fiber sections
    Generates fibers over a circular or annular area
    
    Args:
        material (Material): Material for all fibers in this patch
        num_subdiv_circ (int): Number of subdivisions in circumferential direction
        num_subdiv_rad (int): Number of subdivisions in radial direction
        y_center, z_center (float): Coordinates of circle center
        int_rad (float): Inner radius (0 for solid circle)
        ext_rad (float): Outer radius
        start_ang, end_ang (float, optional): Start and end angles in degrees (default: 0, 360)
    """
    
    def __init__(self, material: Material, num_subdiv_circ: int, num_subdiv_rad: int,
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
            raise ValueError("Invalid numeric values for circular patch parameters")
        
        super().__init__(material)


    def plot(self, ax: plt.Axes, material_colors: Dict[str, str], 
             show_patch_outline: bool = True, show_fiber_grid: bool = False) -> None:
        """Plot circular patch"""
        color = material_colors.get(self.material.user_name, 'blue')
        
        if show_patch_outline:
            # Draw patch outline
            if self.is_full_circle():
                # Full circles
                outer_wedge = Wedge((self.y_center, self.z_center), self.ext_rad,
                                  self.start_ang, self.end_ang, width= self.ext_rad - self.int_rad,
                                  linewidth=2, edgecolor=color, facecolor=color, alpha=0.8)
                ax.add_patch(outer_wedge)
            else:
                # Arc segments
                outer_wedge = Wedge((self.y_center, self.z_center), self.ext_rad,
                                  self.start_ang, self.end_ang, width= self.ext_rad - self.int_rad,
                                  linewidth=2, edgecolor=color, facecolor=color, alpha=0.8)
                ax.add_patch(outer_wedge)
        
        if show_fiber_grid:
            # Show fiber locations in polar coordinates
            angles = np.linspace(np.radians(self.start_ang), np.radians(self.end_ang), 
                               self.num_subdiv_circ + 1)
            
            yinner = self.int_rad * np.cos(angles) + self.y_center
            zinner = self.int_rad * np.sin(angles) + self.z_center
            youter = self.ext_rad * np.cos(angles) + self.y_center
            zouter = self.ext_rad * np.sin(angles) + self.z_center


            # now conncet the inner and outer points
            if self.is_solid():
                # Solid circle, connect all points
                yinner = self.y_center
                zinner = self.z_center
                for i in range(len(angles) - 1):
                    ax.plot([yinner, youter[i]], [zinner, zouter[i]], 
                            color="white", linewidth=0.5, alpha=0.5)
                    ax.plot([yinner, youter[i+1]], [zinner, zouter[i+1]], 
                            color="white", linewidth=0.5, alpha=0.5)

            else:
                # Annular patch, connect inner and outer points
                for i in range(len(yinner) - 1):
                    ax.plot([yinner[i], youter[i]], [zinner[i], zouter[i]], 
                            color="white", linewidth=0.5, alpha=0.5)
                    ax.plot([yinner[i+1], youter[i+1]], [zinner[i+1], zouter[i+1]], 
                            color="white", linewidth=0.5, alpha=0.5) 


                # add white circles with diferent raduis
            for r in np.linspace(self.int_rad, self.ext_rad, self.num_subdiv_rad):
                if r < 1e-12:
                    continue  # Skip if radius is effectively zero
                wedge = Wedge((self.y_center, self.z_center), r,
                                    self.start_ang, self.end_ang, width=0.00,
                                    linewidth=0.5, edgecolor="white", facecolor='none', alpha=1.0)
                ax.add_patch(wedge)
        


    
    def validate(self) -> None:
        """Validate circular patch parameters"""
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
        """Generate OpenSees TCL command for circular patch"""
        cmd = f"    patch circ {self.material.tag} {self.num_subdiv_circ} {self.num_subdiv_rad} "
        cmd += f"{self.y_center} {self.z_center} {self.int_rad} {self.ext_rad}"
        
        # Add angles if not default (0, 360)
        if self.start_ang != 0.0 or self.end_ang != 360.0:
            cmd += f" {self.start_ang} {self.end_ang}"
        
        return cmd
    
    def get_patch_type(self) -> str:
        return "Circular"
    
    def estimate_fiber_count(self) -> int:
        return self.num_subdiv_circ * self.num_subdiv_rad
    
    def is_full_circle(self) -> bool:
        """Check if this represents a full circle (360 degrees)"""
        return abs(self.end_ang - self.start_ang - 360.0) < 1e-6
    
    def is_solid(self) -> bool:
        """Check if this is a solid circle (inner radius = 0)"""
        return abs(self.int_rad) < 1e-12
    
    def __str__(self) -> str:
        shape_desc = "Solid Circle" if self.is_solid() else "Annular"
        if not self.is_full_circle():
            shape_desc += f" Arc ({self.start_ang}° to {self.end_ang}°)"
        return f"Circular Patch: {shape_desc}, R={self.ext_rad}, {self.estimate_fiber_count()} fibers, material '{self.material.user_name}'"


class LayerBase(ABC):
    """
    Abstract base class for layer definitions in fiber sections
    Layers generate fibers along geometric arcs or lines
    """
    
    def __init__(self, material: Material):
        if not isinstance(material, Material):
            raise ValueError("Material must be a Material instance")
        self.material = material
        self.validate()

    @abstractmethod
    def plot(self, ax: plt.Axes, material_colors: Dict[str, str], 
             show_layer_line: bool = True, show_fibers: bool = True) -> None:
        """
        Plot the layer on the given matplotlib axes
        
        Args:
            ax: Matplotlib axes to plot on
            material_colors: Dictionary mapping material names to colors
            show_layer_line: Whether to show the layer line
            show_fibers: Whether to show individual fiber locations
        """
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
    Straight layer of fibers between two points
    
    Args:
        material (Material): Material for all fibers in this layer
        num_fibers (int): Number of fibers in the layer
        area_per_fiber (float): Area of each fiber
        y1, z1 (float): Coordinates of start point
        y2, z2 (float): Coordinates of end point
    """
    
    def __init__(self, material: Material, num_fibers: int, area_per_fiber: float,
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
            # Draw layer line
            ax.plot([self.y1, self.y2], [self.z1, self.z2], 
                   color=color, linewidth=2, alpha=0.8, linestyle='--')
        
        if show_fibers:
            # Show fiber locations
            if self.num_fibers == 1:
                # Single fiber at midpoint
                y_pos = (self.y1 + self.y2) / 2
                z_pos = (self.z1 + self.z2) / 2
                ax.plot(y_pos, z_pos, 's', color=color, markersize=6, alpha=0.8)
            else:
                # Multiple fibers along the line
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
    
    def get_length(self) -> float:
        """Calculate length of the layer"""
        return math.sqrt((self.y2 - self.y1)**2 + (self.z2 - self.z1)**2)
    
    def __str__(self) -> str:
        length = self.get_length()
        return f"Straight Layer: {self.num_fibers} fibers, length={length:.3f}, material '{self.material.user_name}'"


class CircularLayer(LayerBase):
    """
    Circular layer of fibers along a circular arc
    
    Args:
        material (Material): Material for all fibers in this layer
        num_fibers (int): Number of fibers along the arc
        area_per_fiber (float): Area of each fiber
        y_center, z_center (float): Coordinates of arc center
        radius (float): Radius of the circular arc
        start_ang, end_ang (float, optional): Start and end angles in degrees
    """
    
    def __init__(self, material: Material, num_fibers: int, area_per_fiber: float,
                 y_center: float, z_center: float, radius: float,
                 start_ang: Optional[float] = 0.0, end_ang: Optional[float] = None):
        try:
            self.num_fibers = int(num_fibers)
            self.area_per_fiber = float(area_per_fiber)
            self.y_center = float(y_center)
            self.z_center = float(z_center)
            self.radius = float(radius)
            
            # Handle default end angle according to OpenSees specification
            if end_ang is None:
                self.end_ang = 360.0 - 360.0/self.num_fibers
            else:
                self.end_ang = float(end_ang)

            if start_ang is None:
                start_ang = 0.0
            self.start_ang = float(start_ang)
            
        except (ValueError, TypeError):
            raise ValueError("Invalid numeric parameters for circular layer")
        
        super().__init__(material)

    def plot(self, ax: plt.Axes, material_colors: Dict[str, str], 
             show_layer_line: bool = True, show_fibers: bool = True) -> None:
        """Plot circular layer"""
        color = material_colors.get(self.material.user_name, 'blue')
        
        if show_layer_line:
            # Plot the arc path
            angles = np.linspace(np.radians(self.start_ang), np.radians(self.end_ang), 100)
            y_arc = self.y_center + self.radius * np.cos(angles)
            z_arc = self.z_center + self.radius * np.sin(angles)
            ax.plot(y_arc, z_arc, color=color, linestyle='--', alpha=0.7, linewidth=2)
        
        if show_fibers:
            # Plot individual fiber positions
            if self.num_fibers == 1:
                # Single fiber at start angle
                angle = np.radians(self.start_ang)
            else:
                # Multiple fibers distributed along arc
                angles = np.linspace(np.radians(self.start_ang), np.radians(self.end_ang), self.num_fibers)
            
            if self.num_fibers == 1:
                angles = [np.radians(self.start_ang)]
            
            for angle in angles:
                y_fiber = self.y_center + self.radius * np.cos(angle)
                z_fiber = self.z_center + self.radius * np.sin(angle)
                
                # Plot fiber as a circle scaled by area
                fiber_radius = np.sqrt(self.area_per_fiber / np.pi) * 2  # Scale for visibility
                circle = plt.Circle((y_fiber, z_fiber), fiber_radius, color=color, alpha=0.7)
                ax.add_patch(circle)
    
    def validate(self) -> None:
        """Validate circular layer parameters"""
        if self.num_fibers <= 0:
            raise ValueError("Number of fibers must be positive")
        if self.area_per_fiber <= 0:
            raise ValueError("Area per fiber must be positive")
        if self.radius <= 0:
            raise ValueError("Radius must be positive")
        
        # Normalize angles to 0-360 range
        self.start_ang = self.start_ang % 360.0
        self.end_ang = self.end_ang % 360.0
        
        # Check that arc is valid
        if abs(self.start_ang - self.end_ang) < 1e-12:
            raise ValueError("Start and end angles cannot be the same")
    
    def to_tcl(self) -> str:
        """Generate OpenSees TCL command for circular layer"""
        # Check if we need to include optional angles
        if abs(self.start_ang) < 1e-12 and abs(self.end_ang - (360.0 - 360.0/self.num_fibers)) < 1e-12:
            # Use default angles - don't include them in command
            return f"    layer circ {self.material.tag} {self.num_fibers} {self.area_per_fiber} {self.y_center} {self.z_center} {self.radius} "
        else:
            # Include explicit angles
            return f"    layer circ {self.material.tag} {self.num_fibers} {self.area_per_fiber} {self.y_center} {self.z_center} {self.radius} {self.start_ang} {self.end_ang} "
    
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


class FiberSection(Section):
    """
    Complete Fiber Section implementation with support for:
    - Individual fibers
    - Rectangular, quadrilateral, and circular patches  
    - Straight layers
    - Optional torsional stiffness (GJ)
    
    Args:
        user_name (str): User-defined name for the section
        GJ (float, optional): Linear-elastic torsional stiffness
    """
    
    def __init__(self, user_name: str = "Unnamed", GJ: Optional[float] = None, 
                 components: Optional[List[Union[FiberElement, PatchBase, LayerBase]]] = None, **kwargs):
        super().__init__('section', 'Fiber', user_name)
        
        # Initialize collections
        self.fibers: List[FiberElement] = []
        self.patches: List[PatchBase] = []
        self.layers: List[LayerBase] = []
        
        # Process components list and sort into appropriate collections
        if components is not None:
            for i, component in enumerate(components):
                if isinstance(component, FiberElement):
                    self.fibers.append(component)
                elif isinstance(component, PatchBase):
                    self.patches.append(component)
                elif isinstance(component, LayerBase):
                    self.layers.append(component)
                else:
                    raise ValueError(f"Item {i} in components list is not a valid fiber section component (FiberElement, PatchBase, or LayerBase)")
        
        # Handle optional torsional stiffness
        self.GJ = None
        if GJ is not None:
            try:
                self.GJ = float(GJ)
                if self.GJ <= 0:
                    raise ValueError("GJ (torsional stiffness) must be positive")
            except (ValueError, TypeError):
                raise ValueError("GJ must be a positive number")
        
        # Handle any additional parameters
        self.params = kwargs if kwargs else {}
    

    def plot(self, ax: Optional[plt.Axes] = None, figsize: Tuple[float, float] = (10, 8),
             show_fibers: bool = True, show_patches: bool = True, show_layers: bool = True,
             show_patch_outline: bool = True, show_fiber_grid: bool = True,
             show_layer_line: bool = True, title: Optional[str] = None,
             material_colors: Optional[Dict[str, str]] = None,
             save_path: Optional[str] = None, dpi: int = 300) -> plt.Figure:
        """
        Plot the complete fiber section
        
        Args:
            ax: Matplotlib axes to plot on (if None, creates new figure)
            figsize: Figure size if creating new figure
            show_fibers: Whether to show individual fibers
            show_patches: Whether to show patches
            show_layers: Whether to show layers
            show_patch_outline: Whether to show patch outlines
            show_fiber_grid: Whether to show fiber grid in patches
            show_layer_line: Whether to show layer lines
            title: Custom title for the plot
            material_colors: Custom color mapping for materials
            save_path: Path to save the figure (optional)
            dpi: DPI for saved figure
            
        Returns:
            matplotlib Figure object
        """
        # Set default title if none provided
        if title is None:
            title = f"Fiber Section: {self.user_name} (Tag: {self.tag})"
        
        # Call the static plotting method
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
            dpi=dpi
        )

    @staticmethod
    def plot_components(fibers: List[FiberElement], patches: List[PatchBase], layers: List[LayerBase],
                       ax: Optional[plt.Axes] = None, figsize: Tuple[float, float] = (10, 8),
                       show_fibers: bool = True, show_patches: bool = True, show_layers: bool = True,
                       show_patch_outline: bool = True, show_fiber_grid: bool = True,
                       show_layer_line: bool = True, title: Optional[str] = None,
                       material_colors: Optional[Dict[str, str]] = None,
                       save_path: Optional[str] = None, dpi: int = 300) -> plt.Figure:
        """
        Static method to plot fiber section components
        
        Args:
            fibers: List of FiberElement objects
            patches: List of PatchBase objects  
            layers: List of LayerBase objects
            ax: Matplotlib axes to plot on (if None, creates new figure)
            figsize: Figure size if creating new figure
            show_fibers: Whether to show individual fibers
            show_patches: Whether to show patches
            show_layers: Whether to show layers
            show_patch_outline: Whether to show patch outlines
            show_fiber_grid: Whether to show fiber grid in patches
            show_layer_line: Whether to show layer lines
            title: Custom title for the plot
            material_colors: Custom color mapping for materials
            save_path: Path to save the figure (optional)
            dpi: DPI for saved figure
            
        Returns:
            matplotlib Figure object
        """
        # Create figure and axes if not provided
        if ax is None:
            fig, ax = plt.subplots(figsize=figsize)
        else:
            fig = ax.get_figure()
        
        # Generate material color mapping if not provided
        if material_colors is None:
            material_colors = FiberSection.generate_material_colors(fibers, patches, layers)
        
        # Calculate scale factor for fiber visualization
        scale_factor = FiberSection.calculate_scale_factor(fibers)
        
        # Plot individual fibers
        if show_fibers:
            for fiber in fibers:
                fiber.plot(ax, material_colors, scale_factor, show_fibers=True)
        
        # Plot patches
        if show_patches:
            for patch in patches:
                patch.plot(ax, material_colors, show_patch_outline, show_fiber_grid)
        
        # Plot layers
        if show_layers:
            for layer in layers:
                layer.plot(ax, material_colors, show_layer_line, show_fibers)
        
        # Customize plot appearance
        ax.set_xlabel('Y Coordinate')
        ax.set_ylabel('Z Coordinate')
        ax.set_aspect('equal')
        ax.grid(True, alpha=0.3)
        
        # Set title
        if title is not None:
            ax.set_title(title)
        
        # Add legend
        FiberSection._add_legend_to_axes(ax, material_colors)
        
        # Add section info text
        FiberSection._add_section_info_to_axes(ax, fibers, patches, layers)
        
        # Tight layout
        fig.tight_layout()
        
        # Save figure if requested
        if save_path:
            fig.savefig(save_path, dpi=dpi, bbox_inches='tight')
        
        return fig


    def _generate_material_colors(self) -> Dict[str, str]:
        """Generate color mapping for materials"""
        return self.generate_material_colors(self.fibers, self.patches, self.layers)

    @staticmethod
    def generate_material_colors(fibers: List[FiberElement], patches: List[PatchBase], 
                                layers: List[LayerBase]) -> Dict[str, str]:
        """Static method to generate color mapping for materials"""
        materials = []
        
        # Collect materials from all components
        for fiber in fibers:
            if fiber.material not in materials:
                materials.append(fiber.material)
        
        for patch in patches:
            if patch.material not in materials:
                materials.append(patch.material)
        
        for layer in layers:
            if layer.material not in materials:
                materials.append(layer.material)
        
        # Use a color cycle
        colors = ['tab:blue', 'tab:orange', 'tab:green', 'tab:red', 'tab:purple',
                 'tab:brown', 'tab:pink', 'tab:gray', 'tab:olive', 'tab:cyan']
        
        material_colors = {}
        for i, material in enumerate(materials):
            material_colors[material.user_name] = colors[i % len(colors)]
        
        return material_colors

    def _calculate_scale_factor(self) -> float:
        """Calculate appropriate scale factor for fiber visualization"""
        return self.calculate_scale_factor(self.fibers)

    @staticmethod
    def calculate_scale_factor(fibers: List[FiberElement]) -> float:
        """Static method to calculate appropriate scale factor for fiber visualization"""
        if not fibers:
            return 1.0
        
        # Get the range of coordinates
        y_coords = [fiber.y_loc for fiber in fibers]
        z_coords = [fiber.z_loc for fiber in fibers]
        
        if not y_coords or not z_coords:
            return 1.0
        
        y_range = max(y_coords) - min(y_coords)
        z_range = max(z_coords) - min(z_coords)
        coord_range = max(y_range, z_range)
        
        if coord_range == 0:
            return 1.0
        
        # Scale factor to make fibers visible but not overwhelming
        return coord_range / 50.0
    
    def _add_legend(self, ax: plt.Axes, material_colors: Dict[str, str]) -> None:
        """Add legend showing materials"""
        self._add_legend_to_axes(ax, material_colors)
    
    @staticmethod
    def _add_legend_to_axes(ax: plt.Axes, material_colors: Dict[str, str]) -> None:
        """Static helper method to add legend showing materials"""
        if not material_colors:
            return
        
        legend_elements = []
        for material_name, color in material_colors.items():
            legend_elements.append(mpatches.Patch(color=color, label=material_name))
        
        if legend_elements:
            ax.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(1.02, 1), borderaxespad=0.)

    def _add_section_info(self, ax: plt.Axes) -> None:
        """Add section information text"""
        self._add_section_info_to_axes(ax, self.fibers, self.patches, self.layers)
    
    @staticmethod
    def _add_section_info_to_axes(ax: plt.Axes, fibers: List[FiberElement], patches: List[PatchBase], 
                                 layers: List[LayerBase]) -> None:
        """Static helper method to add section information text"""
        # Calculate estimated total fibers
        total_fibers = len(fibers)
        for patch in patches:
            total_fibers += patch.estimate_fiber_count()
        for layer in layers:
            if hasattr(layer, 'num_fibers'):
                total_fibers += layer.num_fibers
        
        info_text = (f"Fibers: {len(fibers)}\n"
                    f"Patches: {len(patches)}\n"
                    f"Layers: {len(layers)}\n"
                    f"Est. Total Fibers: {total_fibers}")
        
        # Add text box
        ax.text(1.03, 0.02, info_text, transform=ax.transAxes, 
                horizontalalignment='left',
               verticalalignment='bottom', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    def add_fiber(self, y_loc: float, z_loc: float, area: float, material: Material) -> None:
        """
        Add an individual fiber to the section
        
        Args:
            y_loc, z_loc (float): Fiber coordinates in section local system
            area (float): Cross-sectional area of the fiber
            material (Material): Uniaxial material for the fiber
        """
        fiber = FiberElement(y_loc, z_loc, area, material)
        self.fibers.append(fiber)
    
    def add_rectangular_patch(self, material: Material, num_subdiv_y: int, num_subdiv_z: int,
                            y1: float, z1: float, y2: float, z2: float) -> None:
        """
        Add a rectangular patch to the section
        
        Args:
            material (Material): Material for all fibers in the patch
            num_subdiv_y, num_subdiv_z (int): Number of subdivisions in each direction
            y1, z1, y2, z2 (float): Coordinates defining the rectangle
        """
        patch = RectangularPatch(material, num_subdiv_y, num_subdiv_z, y1, z1, y2, z2)
        self.patches.append(patch)
    
    def add_quadrilateral_patch(self, material: Material, num_subdiv_ij: int, num_subdiv_jk: int,
                              vertices: List[Tuple[float, float]]) -> None:
        """
        Add a quadrilateral patch to the section
        
        Args:
            material (Material): Material for all fibers in the patch
            num_subdiv_ij, num_subdiv_jk (int): Number of subdivisions along edges
            vertices (List[Tuple[float, float]]): Four vertices (I,J,K,L) in counter-clockwise order
        """
        patch = QuadrilateralPatch(material, num_subdiv_ij, num_subdiv_jk, vertices)
        self.patches.append(patch)
    
    def add_circular_patch(self, material: Material, num_subdiv_circ: int, num_subdiv_rad: int,
                         y_center: float, z_center: float, int_rad: float, ext_rad: float,
                         start_ang: Optional[float] = None, end_ang: Optional[float] = None) -> None:
        """
        Add a circular patch to the section
        
        Args:
            material (Material): Material for all fibers in the patch
            num_subdiv_circ, num_subdiv_rad (int): Number of subdivisions in each direction
            y_center, z_center (float): Center coordinates
            int_rad, ext_rad (float): Inner and outer radii
            start_ang, end_ang (float, optional): Start and end angles in degrees
        """
        patch = CircularPatch(material, num_subdiv_circ, num_subdiv_rad,
                            y_center, z_center, int_rad, ext_rad, start_ang, end_ang)
        self.patches.append(patch)
    
    def add_straight_layer(self, material: Material, num_fibers: int, area_per_fiber: float,
                         y1: float, z1: float, y2: float, z2: float) -> None:
        """
        Add a straight layer of fibers to the section
        
        Args:
            material (Material): Material for all fibers in the layer
            num_fibers (int): Number of fibers in the layer
            area_per_fiber (float): Area of each fiber
            y1, z1, y2, z2 (float): Start and end coordinates
        """
        layer = StraightLayer(material, num_fibers, area_per_fiber, y1, z1, y2, z2)
        self.layers.append(layer)
    
    def add_circular_layer(self, material: Material, num_fibers: int, area_per_fiber: float,
                         y_center: float, z_center: float, radius: float,
                         start_ang: Optional[float] = None, end_ang: Optional[float] = None) -> None:
        """
        Add a circular layer of fibers to the section
        
        Args:
            material (Material): Material for all fibers in the layer
            num_fibers (int): Number of fibers along the arc
            area_per_fiber (float): Area of each fiber
            y_center, z_center (float): Coordinates of arc center
            radius (float): Radius of the circular arc
            start_ang, end_ang (float, optional): Start and end angles in degrees
        """
        layer = CircularLayer(material, num_fibers, area_per_fiber, y_center, z_center, radius, start_ang, end_ang)
        self.layers.append(layer)
    
    def clear_fibers(self) -> None:
        """Remove all individual fibers"""
        self.fibers.clear()
    
    def clear_patches(self) -> None:
        """Remove all patches"""
        self.patches.clear()
    
    def clear_layers(self) -> None:
        """Remove all layers"""
        self.layers.clear()
    
    def clear_all(self) -> None:
        """Remove all fibers, patches, and layers"""
        self.clear_fibers()
        self.clear_patches()
        self.clear_layers()
    
    def to_tcl(self) -> str:
        """Generate complete OpenSees TCL command for fiber section"""
        # Start section definition
        cmd = f"section Fiber {self.tag}"
        
        # Add optional GJ parameter
        if self.GJ is not None:
            cmd += f" -GJ {self.GJ}"
        
        cmd += " {\n"
        
        # Add individual fibers
        for fiber in self.fibers:
            cmd += fiber.to_tcl() + "\n"
        
        # Add patches
        for patch in self.patches:
            cmd += patch.to_tcl() + "\n"
        
        # Add layers
        for layer in self.layers:
            cmd += layer.to_tcl() + "\n"
        
        cmd += f"}}; # {self.user_name}"
        
        return cmd
    
    def get_materials(self) -> List[Material]:
        """Get all materials used by this section (for dependency tracking)"""
        materials = []
        
        # Materials from individual fibers
        for fiber in self.fibers:
            if fiber.material not in materials:
                materials.append(fiber.material)
        
        # Materials from patches
        for patch in self.patches:
            if patch.material not in materials:
                materials.append(patch.material)
        
        # Materials from layers
        for layer in self.layers:
            if layer.material not in materials:
                materials.append(layer.material)
        
        return materials
    
    def get_total_estimated_fibers(self) -> int:
        """Estimate total number of fibers in the section"""
        total = len(self.fibers)  # Individual fibers
        
        # Add estimated fibers from patches
        for patch in self.patches:
            total += patch.estimate_fiber_count()
        
        # Add fibers from layers
        for layer in self.layers:
            if hasattr(layer, 'num_fibers'):
                total += layer.num_fibers
        
        return total
    
    def get_section_summary(self) -> Dict[str, Union[int, str, List[str]]]:
        """Get a summary of the section contents"""
        return {
            'individual_fibers': len(self.fibers),
            'patches': len(self.patches),
            'layers': len(self.layers),
            'estimated_total_fibers': self.get_total_estimated_fibers(),
            'materials_used': [mat.user_name for mat in self.get_materials()],
            'has_torsional_stiffness': self.GJ is not None,
            'patch_types': [patch.get_patch_type() for patch in self.patches],
            'layer_types': [layer.get_layer_type() for layer in self.layers]
        }
    
    @classmethod
    def get_parameters(cls) -> List[str]:
        """Parameters for Fiber section"""
        return ["GJ", "fibers", "patches", "layers"]
    
    @classmethod
    def get_description(cls) -> List[str]:
        """Parameter descriptions for Fiber section"""
        return [
            "Linear-elastic torsional stiffness (optional)",
            "Individual fiber definitions",
            "Patch definitions (rectangular, quadrilateral, circular)",
            "Layer definitions (straight lines, arcs)"
        ]
    
    @classmethod
    def get_help_text(cls) -> str:
        """Get the formatted help text for Fiber section"""
        return """
        <b>Fiber Section</b><br>
        Creates a section using fiber discretization for nonlinear analysis.<br><br>
        Fibers are added programmatically using the add_fiber() method.<br>
        Each fiber has coordinates, area, and a material.
        """

    @classmethod
    def validate_section_parameters(cls, **kwargs) -> Dict[str, Union[int, float, str]]:
        """Validate parameters for Fiber section"""
        validated_params = {}
        
        # Validate GJ if provided
        if 'GJ' in kwargs and kwargs['GJ'] is not None:
            try:
                gj = float(kwargs['GJ'])
                if gj <= 0:
                    raise ValueError("GJ must be positive")
                validated_params['GJ'] = gj
            except (ValueError, TypeError):
                raise ValueError("GJ must be a positive number")
        
        return validated_params
    
    def get_values(self, keys: List[str]) -> Dict[str, Union[int, float, str]]:
        """Retrieve values for specific parameters"""
        values = {}
        if 'GJ' in keys:
            values['GJ'] = self.GJ if self.GJ is not None else "None"
        if 'fibers' in keys:
            values['fibers'] = len(self.fibers)
        if 'patches' in keys:
            values['patches'] = len(self.patches)
        if 'layers' in keys:
            values['layers'] = len(self.layers)
        if 'total_estimated_fibers' in keys:
            values['total_estimated_fibers'] = self.get_total_estimated_fibers()
        return values
    
    def update_values(self, values: Dict[str, Union[int, float, str]]) -> None:
        """Update section parameters"""
        # Only GJ can be updated directly - fibers/patches/layers are managed via methods
        if 'GJ' in values:
            if values['GJ'] == "None" or values['GJ'] is None:
                self.GJ = None
            else:
                try:
                    gj = float(values['GJ'])
                    if gj <= 0:
                        raise ValueError("GJ must be positive")
                    self.GJ = gj
                except (ValueError, TypeError):
                    raise ValueError("GJ must be a positive number")
    
    def __str__(self) -> str:
        summary = self.get_section_summary()
        return (f"Fiber Section '{self.user_name}' (Tag: {self.tag})\n"
                f"  Fibers: {summary['individual_fibers']}, "
                f"Patches: {summary['patches']}, "
                f"Layers: {summary['layers']}\n"
                f"  Estimated total fibers: {summary['estimated_total_fibers']}\n"
                f"  Materials: {', '.join(summary['materials_used'])}\n"
                f"  Torsional stiffness: {'Yes' if summary['has_torsional_stiffness'] else 'No'}")






"""
Wide Flange Section implementation for OpenSees
Creates a fiber section representation of a wide flange shape
Based on WFSection2d OpenSees command
"""

class WideFlangeFiberSection(Section):
    """
    Wide Flange Section implementation for OpenSees
    Creates a fiber section representation of a wide flange shape
    Based on WFSection2d OpenSees command
    """
    
    def __init__(self, user_name: str = "Unnamed", **kwargs):
        kwargs = self.validate_section_parameters(**kwargs)
        super().__init__('section', 'WFSection2d', user_name)
        self.params = kwargs if kwargs else {}

    def to_tcl(self) -> str:
        """Generate the OpenSees TCL command for WFSection2d"""
        param_order = self.get_parameters()
        params_str = " ".join(str(self.params[param]) for param in param_order if param in self.params)
        return f"section WFSection2d {self.tag} {params_str}; # {self.user_name}"

    @classmethod
    def get_parameters(cls) -> List[str]:
        """Parameters for WFSection2d section"""
        return ["matTag", "d", "tw", "bf", "tf", "Nflweb", "Nflflange"]

    @classmethod
    def get_description(cls) -> List[str]:
        """Parameter descriptions for WFSection2d section"""
        return [
            "Material tag",
            "Section depth",
            "Web thickness",
            "Flange width",
            "Flange thickness",
            "Number of fibers in the web",
            "Number of fibers in the flange"
        ]

    @classmethod
    def get_help_text(cls) -> str:
        """Get the formatted help text for WFSection2d section"""
        return """
        <b>Wide Flange Section (WFSection2d)</b><br>
        Creates a fiber section representation of a wide flange shape.<br><br>
        
        <b>Parameters:</b><br>
        • <b>Material Tag:</b> Material identifier for the section<br>
        • <b>Section Depth (d):</b> Overall depth of the section<br>
        • <b>Web Thickness (tw):</b> Thickness of the web<br>
        • <b>Flange Width (bf):</b> Width of the flanges<br>
        • <b>Flange Thickness (tf):</b> Thickness of the flanges<br>
        • <b>Web Fibers (Nflweb):</b> Number of fibers through web thickness<br>
        • <b>Flange Fibers (Nflflange):</b> Number of fibers through flange thickness<br><br>
        
        This section automatically creates a fiber discretization of a wide flange shape
        using the specified material and fiber counts.
        """

    @classmethod
    def validate_section_parameters(cls, **kwargs) -> Dict[str, Union[int, float, str]]:
        """Validate parameters for WFSection2d section"""
        validated_params = {}
        
        # Material tag (required)
        if 'matTag' not in kwargs:
            raise ValueError("matTag is required for WFSection2d")
        try:
            validated_params['matTag'] = int(kwargs['matTag'])
            if validated_params['matTag'] <= 0:
                raise ValueError("matTag must be positive")
        except (ValueError, TypeError):
            raise ValueError("matTag must be a positive integer")
        
        # Section depth (required)
        if 'd' not in kwargs:
            raise ValueError("d (section depth) is required for WFSection2d")
        try:
            validated_params['d'] = float(kwargs['d'])
            if validated_params['d'] <= 0:
                raise ValueError("Section depth must be positive")
        except (ValueError, TypeError):
            raise ValueError("Section depth must be a positive number")
        
        # Web thickness (required)
        if 'tw' not in kwargs:
            raise ValueError("tw (web thickness) is required for WFSection2d")
        try:
            validated_params['tw'] = float(kwargs['tw'])
            if validated_params['tw'] <= 0:
                raise ValueError("Web thickness must be positive")
        except (ValueError, TypeError):
            raise ValueError("Web thickness must be a positive number")
        
        # Flange width (required)
        if 'bf' not in kwargs:
            raise ValueError("bf (flange width) is required for WFSection2d")
        try:
            validated_params['bf'] = float(kwargs['bf'])
            if validated_params['bf'] <= 0:
                raise ValueError("Flange width must be positive")
        except (ValueError, TypeError):
            raise ValueError("Flange width must be a positive number")
        
        # Flange thickness (required)
        if 'tf' not in kwargs:
            raise ValueError("tf (flange thickness) is required for WFSection2d")
        try:
            validated_params['tf'] = float(kwargs['tf'])
            if validated_params['tf'] <= 0:
                raise ValueError("Flange thickness must be positive")
        except (ValueError, TypeError):
            raise ValueError("Flange thickness must be a positive number")
        
        # Number of fibers in web (required)
        if 'Nflweb' not in kwargs:
            raise ValueError("Nflweb (number of fibers in web) is required for WFSection2d")
        try:
            validated_params['Nflweb'] = int(kwargs['Nflweb'])
            if validated_params['Nflweb'] <= 0:
                raise ValueError("Number of fibers in web must be positive")
        except (ValueError, TypeError):
            raise ValueError("Number of fibers in web must be a positive integer")
        
        # Number of fibers in flange (required)
        if 'Nflflange' not in kwargs:
            raise ValueError("Nflflange (number of fibers in flange) is required for WFSection2d")
        try:
            validated_params['Nflflange'] = int(kwargs['Nflflange'])
            if validated_params['Nflflange'] <= 0:
                raise ValueError("Number of fibers in flange must be positive")
        except (ValueError, TypeError):
            raise ValueError("Number of fibers in flange must be a positive integer")
        
        # Additional validation - geometric constraints
        if validated_params['tf'] >= validated_params['d'] / 2:
            raise ValueError("Flange thickness must be less than half the section depth")
        
        if validated_params['tw'] >= validated_params['bf']:
            raise ValueError("Web thickness should be less than flange width")
        
        return validated_params

    def get_values(self, keys: List[str]) -> Dict[str, Union[int, float, str]]:
        """Retrieve values for specific parameters"""
        return {key: self.params.get(key) for key in keys}

    def update_values(self, values: Dict[str, Union[int, float, str]]) -> None:
        """Update section parameters"""
        self.params.clear()
        validated_params = self.validate_section_parameters(**values)
        self.params.update(validated_params)

    def get_materials(self) -> List[Material]:
        """Get all materials used by this section (for dependency tracking)"""
        # This section references a material by tag, but we don't have the actual Material object
        # Return empty list since we only have the tag reference
        return []
    

    
# Register all section types
SectionRegistry.register_section_type('Elastic', ElasticSection)
SectionRegistry.register_section_type('Fiber', FiberSection) 
SectionRegistry.register_section_type('Aggregator', AggregatorSection)
SectionRegistry.register_section_type('Uniaxial', UniaxialSection)
SectionRegistry.register_section_type('WFSection2d', WideFlangeFiberSection)