# =============================================================================
# Femora: Fast Efficient Meta-modeling for OpenSees-based Resilience Analysis
# Copyright 2026 Amin Pakzad and Pedro Arduino
# Developed at the UW Geotechnical Lab
# SPDX-License-Identifier: Apache-2.0
# =============================================================================

from typing import List, Dict, Union, Optional, Tuple
import math

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from matplotlib.patches import Circle

from femora.core.material_base import Material
from femora.core.section_base import Section

class FiberElement:
    """Represents a single fiber in a fiber section.

    A fiber is the smallest unit of discretization in a fiber section, defined by
     its position (y, z) and its area. Each fiber is associated with a material
     response.

    Tcl form:
        ``fiber <yLoc> <zLoc> <area> <matTag>``

    Attributes:
        y_loc: Local y-coordinate of the fiber center.
        z_loc: Local z-coordinate of the fiber center.
        area: Cross-sectional area of the fiber.
        material: Resolved Material object for the fiber.

    Example:
        ```python
        from femora.core.model import Model
        import femora.components.section.fiber  # noqa: F401

        model = Model()
        mat = model.material.uniaxial.steel01(
            user_name="S",
            Fy=50.0,
            E0=29000.0,
            b=0.01,
        )
        section = model.section.fiber.section(user_name="BeamFiber")
        section.add_fiber(y_loc=0.5, z_loc=0.5, area=0.1, material=mat)
        print(section.fibers[0].to_tcl())
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

    def __init__(self, y_loc: float, z_loc: float, area: float,
                 material: Union[int, str, Material]):
        """Create a FiberElement with validated coordinates and area.

        Args:
            y_loc: Local y-coordinate.
            z_loc: Local z-coordinate.
            area: Fiber area.
            material: Uniaxial material reference (object, tag, or name).

        Raises:
            ValueError: If coordinates or area are not numeric, if area is
                non-positive, or if the material cannot be resolved.
        """
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
        """Plot the fiber on the given matplotlib axes.

        Args:
            ax: Matplotlib axes to plot on.
            material_colors: Dictionary mapping material names to colors.
            scale_factor: Scaling factor for visualization.
            show_fibers: Whether to actually draw the fiber.
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
        """Render the fiber as an OpenSees Tcl command.

        Returns:
            str: Indented Tcl ``fiber`` command for this element.
        """
        return f"    fiber {self.y_loc} {self.z_loc} {self.area} {self.material.tag}"

    def __str__(self) -> str:
        """Return a string representation of the fiber."""
        return f"Fiber at ({self.y_loc}, {self.z_loc}) with area {self.area}, material '{self.material.user_name}'"
