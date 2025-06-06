"""
Enhanced OpenSees Section Implementations for FEMORA with Material Resolution
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
    No external material required - uses built-in elastic properties
    """
    
    def __init__(self, user_name: str = "Unnamed", **kwargs):
        kwargs = self.validate_section_parameters(**kwargs)
        super().__init__('section', 'Elastic', user_name)
        self.params = kwargs if kwargs else {}
        # Elastic sections don't require external materials
        self.material = None

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
        • J: Torsional constant<br><br>
        <b>Note:</b> This section type does not require external materials.
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

    def get_materials(self) -> List[Material]:
        """Elastic sections don't use external materials"""
        return []


class AggregatorSection(Section):
    """
    Aggregator Section implementation for OpenSees
    Combines multiple materials for different response quantities
    """
    
    def __init__(self, user_name: str = "Unnamed", 
                 materials: Optional[Dict[str, Union[int, str, Material]]] = None,
                 base_section: Optional[Union[int, str, 'Section']] = None, **kwargs):
        super().__init__('section', 'Aggregator', user_name)
        
        # Resolve materials dictionary
        self.materials = {}
        if materials:
            self.materials = self.resolve_materials_dict(materials)
        
        # Resolve base section if provided
        self.base_section = None
        if base_section is not None:
            self.base_section = self.resolve_section(base_section)
        
        # Set primary material (first material if any)
        if self.materials:
            self.material = next(iter(self.materials.values()))
        else:
            self.material = None

    @staticmethod
    def resolve_section(section_input: Union[int, str, 'Section']) -> 'Section':
        """
        Resolve section from different input types
        
        Args:
            section_input: Section tag, name, or object
            
        Returns:
            Section object
        """
        if isinstance(section_input, Section):
            return section_input
        
        if isinstance(section_input, (int, str)):
            from femora.components.section.section_base import SectionManager
            return SectionManager.get_section(section_input)
        
        raise ValueError(f"Invalid section input type: {type(section_input)}")

    def add_material(self, material_input: Union[int, str, Material], response_code: str):
        """Add a material with its response code"""
        valid_codes = ['P', 'Mz', 'My', 'Vy', 'Vz', 'T']
        if response_code not in valid_codes:
            raise ValueError(f"Invalid response code. Must be one of: {valid_codes}")
        
        material = self.resolve_material(material_input)
        self.materials[response_code] = material
        
        # Set as primary material if none exists
        if self.material is None:
            self.material = material

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
        • T: Torsion<br><br>
        <b>Materials:</b> Accepts UniaxialMaterial objects, tags, or names
        """

    @classmethod
    def validate_section_parameters(cls, **kwargs) -> Dict[str, Union[int, float, str]]:
        """Validate parameters for Aggregator section"""
        validated_params = {}
        
        if 'materials' in kwargs:
            materials = kwargs['materials']
            if not isinstance(materials, dict):
                raise ValueError("Materials must be a dictionary mapping response codes to materials")
            
            valid_codes = ['P', 'Mz', 'My', 'Vy', 'Vz', 'T']
            for code in materials.keys():
                if code not in valid_codes:
                    raise ValueError(f"Invalid response code '{code}'. Must be one of: {valid_codes}")
            
            validated_params['materials'] = materials
        
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
        if 'materials' in values:
            # This would need custom parsing logic for materials
            pass
        if 'base_section' in values and values['base_section'] != "None":
            self.base_section = self.resolve_section(values['base_section'])


class UniaxialSection(Section):
    """
    Uniaxial Section implementation for OpenSees
    Uses a single uniaxial material for a specific response
    """
    
    def __init__(self, user_name: str = "Unnamed", 
                 material: Union[int, str, Material] = None,
                 response_code: str = "P", **kwargs):
        super().__init__('section', 'Uniaxial', user_name)
        
        # Resolve and store material
        if material is None:
            raise ValueError("UniaxialSection requires a material")
        self.material = self.resolve_material(material)
        
        # Validate and store response code
        valid_codes = ['P', 'Mz', 'My', 'Vy', 'Vz', 'T']
        if response_code not in valid_codes:
            raise ValueError(f"Response code must be one of: {valid_codes}")
        self.response_code = response_code
        
        # Store in params for consistency
        self.params = {
            'material': self.material,
            'response_code': response_code
        }

    def to_tcl(self) -> str:
        """Generate the OpenSees TCL command for Uniaxial section"""
        return f"section Uniaxial {self.tag} {self.material.tag} {self.response_code}; # {self.user_name}"

    def get_materials(self) -> List[Material]:
        """Get all materials used by this section"""
        return [self.material]

    @classmethod
    def get_parameters(cls) -> List[str]:
        """Parameters for Uniaxial section"""
        return ["material", "response_code"]

    @classmethod
    def get_description(cls) -> List[str]:
        """Parameter descriptions for Uniaxial section"""
        return [
            "Uniaxial material to use (tag, name, or object)",
            "Response code (P, Mz, My, Vy, Vz, T)"
        ]

    @classmethod
    def get_help_text(cls) -> str:
        """Get the formatted help text for Uniaxial section"""
        return """
        <b>Uniaxial Section</b><br>
        Uses a single uniaxial material for one response quantity.<br><br>
        Specify the material and the response code it represents.<br><br>
        <b>Materials:</b> Accepts UniaxialMaterial objects, tags, or names
        """

    @classmethod
    def validate_section_parameters(cls, **kwargs) -> Dict[str, Union[int, float, str]]:
        """Validate parameters for Uniaxial section"""
        validated_params = {}
        
        if 'response_code' in kwargs:
            response_code = kwargs['response_code']
            valid_codes = ['P', 'Mz', 'My', 'Vy', 'Vz', 'T']
            if response_code not in valid_codes:
                raise ValueError(f"Response code must be one of: {valid_codes}")
            validated_params['response_code'] = response_code
        
        return validated_params

    def get_values(self, keys: List[str]) -> Dict[str, Union[int, float, str]]:
        """Retrieve values for specific parameters"""
        values = {}
        if 'material' in keys:
            values['material'] = self.material.user_name if self.material else "None"
        if 'response_code' in keys:
            values['response_code'] = self.response_code
        return values

    def update_values(self, values: Dict[str, Union[int, float, str]]) -> None:
        """Update section parameters"""
        if 'material' in values:
            self.material = self.resolve_material(values['material'])
            self.params['material'] = self.material
        if 'response_code' in values:
            self.response_code = values['response_code']
            self.params['response_code'] = self.response_code


class FiberElement:
    """
    Represents a single fiber in a fiber section with enhanced material handling
    """
    
    def __init__(self, y_loc: float, z_loc: float, area: float, 
                 material: Union[int, str, Material]):
        # Validate and convert inputs
        try:
            self.y_loc = float(y_loc)
            self.z_loc = float(z_loc)
            self.area = float(area)
        except (ValueError, TypeError):
            raise ValueError("Fiber coordinates and area must be numeric values")
        
        if self.area <= 0:
            raise ValueError("Fiber area must be positive")
        
        # Resolve material
        self.material = Section.resolve_material(material)
        if self.material is None:
            raise ValueError("Fiber requires a valid material")

    def plot(self, ax: plt.Axes, material_colors: Dict[str, str], 
             scale_factor: float = 1.0, show_fibers: bool = True) -> None:
        """Plot the fiber on the given matplotlib axes"""
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


class FiberSection(Section):
    """
    Complete Fiber Section implementation with enhanced material handling
    """
    
    def __init__(self, user_name: str = "Unnamed", GJ: Optional[float] = None, 
                 components: Optional[List[Union[FiberElement, PatchBase, LayerBase]]] = None, **kwargs):
        super().__init__('section', 'Fiber', user_name)
        
        # Initialize collections
        self.fibers: List[FiberElement] = []
        self.patches: List[PatchBase] = []
        self.layers: List[LayerBase] = []
        
        # Process components list
        if components is not None:
            for i, component in enumerate(components):
                if isinstance(component, FiberElement):
                    self.fibers.append(component)
                elif isinstance(component, PatchBase):
                    self.patches.append(component)
                elif isinstance(component, LayerBase):
                    self.layers.append(component)
                else:
                    raise ValueError(f"Item {i} in components list is not a valid fiber section component")
        
        # Handle optional torsional stiffness
        self.GJ = None
        if GJ is not None:
            try:
                self.GJ = float(GJ)
                if self.GJ <= 0:
                    raise ValueError("GJ (torsional stiffness) must be positive")
            except (ValueError, TypeError):
                raise ValueError("GJ must be a positive number")
        
        # Set primary material to first found material
        all_materials = self.get_materials()
        self.material = all_materials[0] if all_materials else None
        
        self.params = kwargs if kwargs else {}

    def add_fiber(self, y_loc: float, z_loc: float, area: float, 
                  material: Union[int, str, Material]) -> None:
        """Add an individual fiber to the section"""
        fiber = FiberElement(y_loc, z_loc, area, material)
        self.fibers.append(fiber)
        
        # Update primary material if none exists
        if self.material is None:
            self.material = fiber.material

    def add_rectangular_patch(self, material: Union[int, str, Material], 
                            num_subdiv_y: int, num_subdiv_z: int,
                            y1: float, z1: float, y2: float, z2: float) -> None:
        """Add a rectangular patch to the section"""
        patch = RectangularPatch(material, num_subdiv_y, num_subdiv_z, y1, z1, y2, z2)
        self.patches.append(patch)
        
        # Update primary material if none exists
        if self.material is None:
            self.material = patch.material

    def add_straight_layer(self, material: Union[int, str, Material], 
                         num_fibers: int, area_per_fiber: float,
                         y1: float, z1: float, y2: float, z2: float) -> None:
        """Add a straight layer of fibers to the section"""
        layer = StraightLayer(material, num_fibers, area_per_fiber, y1, z1, y2, z2)
        self.layers.append(layer)
        
        # Update primary material if none exists
        if self.material is None:
            self.material = layer.material

    def to_tcl(self) -> str:
        """Generate complete OpenSees TCL command for fiber section"""
        cmd = f"section Fiber {self.tag}"
        
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
        """Get all materials used by this section"""
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
        Each fiber has coordinates, area, and a material.<br><br>
        <b>Materials:</b> Accepts UniaxialMaterial objects, tags, or names
        """

    @classmethod
    def validate_section_parameters(cls, **kwargs) -> Dict[str, Union[int, float, str]]:
        """Validate parameters for Fiber section"""
        validated_params = {}
        
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
        return values

    def update_values(self, values: Dict[str, Union[int, float, str]]) -> None:
        """Update section parameters"""
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


# Register section types
SectionRegistry.register_section_type('Elastic', ElasticSection)
SectionRegistry.register_section_type('Fiber', FiberSection) 
SectionRegistry.register_section_type('Aggregator', AggregatorSection)
SectionRegistry.register_section_type('Uniaxial', UniaxialSection)


if __name__ == "__main__":
    # Example usage demonstrating enhanced material handling
    """
    Create example sections demonstrating enhanced material handling
    """
    from femora.components.Material.materialsOpenSees import ElasticUniaxialMaterial
    
    # Create materials
    steel = ElasticUniaxialMaterial(user_name="Steel", E=200000, eta=0.0)
    concrete = ElasticUniaxialMaterial(user_name="Concrete", E=30000, eta=0.0)
    
    print("Created materials:")
    print(f"  Steel: tag={steel.tag}, name='{steel.user_name}'")
    print(f"  Concrete: tag={concrete.tag}, name='{concrete.user_name}'")
    
    # Example 1: Elastic section (no materials required)
    elastic_sec = ElasticSection("Beam_Section", E=200000, A=0.01, Iz=8.33e-5)
    print(f"\nElastic Section: {elastic_sec}")
    print(f"  Has material: {elastic_sec.has_material()}")
    
    # Example 2: Uniaxial section with material object
    uniaxial_sec1 = UniaxialSection("Steel_Axial", material=steel, response_code="P")
    print(f"\nUniaxial Section (material object): {uniaxial_sec1}")
    print(f"  Material: {uniaxial_sec1.material.user_name}")
    
    # Example 3: Uniaxial section with material tag
    uniaxial_sec2 = UniaxialSection("Concrete_Moment", material=concrete.tag, response_code="Mz")
    print(f"\nUniaxial Section (material tag): {uniaxial_sec2}")
    print(f"  Material: {uniaxial_sec2.material.user_name}")
    
    # Example 4: Uniaxial section with material name
    uniaxial_sec3 = UniaxialSection("Steel_Moment", material="Steel", response_code="Mz")
    print(f"\nUniaxial Section (material name): {uniaxial_sec3}")
    print(f"  Material: {uniaxial_sec3.material.user_name}")
    
    # Example 5: Fiber section with mixed material inputs
    fiber_sec = FiberSection("RC_Section", GJ=1000000)
    
    # Add fiber with material object
    fiber_sec.add_fiber(0.0, 0.0, 0.0001, steel)
    
    # Add patch with material name
    fiber_sec.add_rectangular_patch("Concrete", 10, 10, -0.1, -0.1, 0.1, 0.1)
    
    # Add layer with material tag
    fiber_sec.add_straight_layer(steel.tag, 4, 0.0005, -0.08, -0.08, 0.08, -0.08)
    
    print(f"\nFiber Section: {fiber_sec}")
    print(f"  Materials used: {[mat.user_name for mat in fiber_sec.get_materials()]}")
    print(f"  Primary material: {fiber_sec.material.user_name if fiber_sec.material else 'None'}")
    
    sections =  [elastic_sec, uniaxial_sec1, uniaxial_sec2, uniaxial_sec3, fiber_sec]
    
    print("\n" + "="*50)
    print("TCL OUTPUT:")
    print("="*50)
    
    for section in sections:
        print(f"\n# {section.user_name}")
        print(section.to_tcl())