"""Internal helper bases for fiber section components."""

from abc import ABC, abstractmethod
from typing import Dict, Union

import matplotlib.pyplot as plt

from femora.core.material_base import Material
from femora.core.section_base import Section


class PatchBase(ABC):
    """Abstract base class for patch definitions used by fiber sections."""

    def __init__(self, material: Union[int, str, Material]):
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
        """Plot the patch on matplotlib axes."""

    @abstractmethod
    def to_tcl(self) -> str:
        """Generate the OpenSees Tcl command for this patch."""

    @abstractmethod
    def validate(self) -> None:
        """Validate patch parameters."""

    @abstractmethod
    def get_patch_type(self) -> str:
        """Return the patch type name."""

    @abstractmethod
    def estimate_fiber_count(self) -> int:
        """Estimate the number of fibers this patch will generate."""


class LayerBase(ABC):
    """Abstract base class for layer definitions used by fiber sections."""

    def __init__(self, material: Union[int, str, Material]):
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
        """Plot the layer on matplotlib axes."""

    @abstractmethod
    def to_tcl(self) -> str:
        """Generate the OpenSees Tcl command for this layer."""

    @abstractmethod
    def validate(self) -> None:
        """Validate layer parameters."""

    @abstractmethod
    def get_layer_type(self) -> str:
        """Return the layer type name."""
