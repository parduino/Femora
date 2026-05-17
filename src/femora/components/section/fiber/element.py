from typing import List, Dict, Union, Optional, Tuple
import math

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from matplotlib.patches import Circle

from femora.core.material_base import Material
from femora.core.section_base import Section

class FiberElement:
    """
    Represents a single fiber in a fiber section with enhanced material handling.

    Parameters
    ----------
    y_loc : float
        Y-coordinate of the fiber.
    z_loc : float
        Z-coordinate of the fiber.
    area : float
        Area of the fiber.
    material : int, str, or Material
        Material for the fiber (tag, name, or object).
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
        self.material = Section.resolve_material_reference(material)
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

