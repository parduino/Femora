"""Internal helper bases for fiber section components."""

from abc import ABC, abstractmethod
from typing import Dict, Union

import matplotlib.pyplot as plt

from femora.core.material_base import Material
from femora.core.section_base import Section


class PatchBase(ABC):
    """Abstract base class for patch definitions in fiber sections.

    A patch represents a geometric area (rectangular, quadrilateral, or circular)
    that is discretized into multiple fibers. All fibers in a patch share the
    same material.

    Note:
        - Subclasses must implement `plot`, `to_tcl`, `validate`, `get_patch_type`,
          and `estimate_fiber_count`.
        - The `material` is resolved during initialization.

    Attributes:
        material: Resolved Material object for the patch.
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

    def __init__(self, material: Union[int, str, Material]):
        """Initialize the patch and resolve its material.

        Args:
            material: Uniaxial material reference (object, tag, or name).

        Raises:
            ValueError: If the material cannot be resolved or if validation fails.
        """
        self.material = Section.resolve_material_reference(material)
        if self.material is None:
            raise ValueError("Patch requires a valid material")
        self.validate()

    @abstractmethod
    def plot(
        self,
        ax: plt.Axes,
        material_colors: Dict[str, str],
        show_patch_outline: bool = True,
        show_fiber_grid: bool = False,
    ) -> None:
        """Plot the patch on matplotlib axes.

        Args:
            ax: Matplotlib axes to plot on.
            material_colors: Dictionary mapping material names to colors.
            show_patch_outline: Whether to draw the patch boundary.
            show_fiber_grid: Whether to draw the discretized fiber grid.
        """

    @abstractmethod
    def to_tcl(self) -> str:
        """Generate the OpenSees Tcl command for this patch.

        Returns:
            Tcl command string.
        """

    @abstractmethod
    def validate(self) -> None:
        """Validate patch parameters.

        Raises:
            ValueError: If parameters are inconsistent or invalid.
        """

    @abstractmethod
    def get_patch_type(self) -> str:
        """Return the patch type name.

        Returns:
            Type name (e.g., 'Rectangular').
        """

    @abstractmethod
    def estimate_fiber_count(self) -> int:
        """Estimate the number of fibers this patch will generate.

        Returns:
            Total number of fibers.
        """


class LayerBase(ABC):
    """Abstract base class for layer definitions in fiber sections.

    A layer represents a line or arc of fibers. All fibers in a layer share the
    same material and area.

    Note:
        - Subclasses must implement `plot`, `to_tcl`, `validate`, and `get_layer_type`.
        - The `material` is resolved during initialization.

    Attributes:
        material: Resolved Material object for the layer.
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

    def __init__(self, material: Union[int, str, Material]):
        """Initialize the layer and resolve its material.

        Args:
            material: Uniaxial material reference (object, tag, or name).

        Raises:
            ValueError: If the material cannot be resolved or if validation fails.
        """
        self.material = Section.resolve_material_reference(material)
        if self.material is None:
            raise ValueError("Layer requires a valid material")
        self.validate()

    @abstractmethod
    def plot(
        self,
        ax: plt.Axes,
        material_colors: Dict[str, str],
        show_layer_line: bool = True,
        show_fibers: bool = True,
    ) -> None:
        """Plot the layer on matplotlib axes.

        Args:
            ax: Matplotlib axes to plot on.
            material_colors: Dictionary mapping material names to colors.
            show_layer_line: Whether to draw the line/arc representing the layer.
            show_fibers: Whether to draw individual fiber markers.
        """

    @abstractmethod
    def to_tcl(self) -> str:
        """Generate the OpenSees Tcl command for this layer.

        Returns:
            Tcl command string.
        """

    @abstractmethod
    def validate(self) -> None:
        """Validate layer parameters.

        Raises:
            ValueError: If parameters are inconsistent or invalid.
        """

    @abstractmethod
    def get_layer_type(self) -> str:
        """Return the layer type name.

        Returns:
            Type name (e.g., 'Straight').
        """
