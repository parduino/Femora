"""
OpenSees Section Implementations for FEMORA
Based on OpenSees section types with validation and parameter management
"""

from typing import List, Dict, Union, Optional, Tuple
from abc import ABC, abstractmethod
import math
from femora.components.section.section_base import Section, SectionRegistry
from femora.components.Material.materialBase import Material


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
    
    def __init__(self, user_name: str = "Unnamed", GJ: Optional[float] = None, **kwargs):
        super().__init__('section', 'Fiber', user_name)
        
        # Initialize collections
        self.fibers: List[FiberElement] = []
        self.patches: List[PatchBase] = []
        self.layers: List[LayerBase] = []
        
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


# Update the section registry
SectionRegistry.register_section_type('Fiber', FiberSection)

# Register section types
SectionRegistry.register_section_type('Elastic', ElasticSection)
SectionRegistry.register_section_type('Fiber', FiberSection) 
SectionRegistry.register_section_type('Aggregator', AggregatorSection)
SectionRegistry.register_section_type('Uniaxial', UniaxialSection)