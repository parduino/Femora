from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Union, Any, TYPE_CHECKING
from femora.core.material_base import Material
from femora.core.section_base import Section
from femora.core.transformation_base import GeometricTransformation

if TYPE_CHECKING:
    from femora.core.element_manager import ElementManager


class Element(ABC):
    """Base abstract class for manager-owned OpenSees finite elements.

    Element instances do not self-register and do not assign their own tags.
    An `ElementManager` owns lifecycle operations, tag assignment, removal,
    and retagging for a local model context.

    Attributes:
        tag: Manager-assigned OpenSees element tag. Remains None until
            this object is added to an ElementManager.
        _owner: Reference to the owning manager, or None when unmanaged.
        element_type: The type of element (e.g., 'quad', 'truss', 'beam').
        _ndof: Number of degrees of freedom for the element.
        element_params: Dictionary of element-specific parameters.
        _material: Primary material assigned to this element.
        _materials: List of all materials assigned to this element.
        _section: Section assigned to this element (for section-based elements).
        _transformation: Geometric transformation assigned to this element (for beam elements).
    """

    def __init__(self, element_type: str,
                 ndof: int,
                 material: Union[Material, List[Material], None] = None,
                 section: Section = None,
                 transformation: GeometricTransformation = None,
                 **element_params
                 ):
        """Initializes the Element with flexible dependency support."""
        self.tag: Optional[int] = None
        self._owner: object | None = None
        
        self.element_type = element_type
        self._ndof = ndof
        self.element_params = element_params

        # Store dependencies without validation (child classes handle validation)
        self._material = material
        self._section = section
        self._transformation = transformation

        # Handle multiple materials for list case
        if isinstance(material, list):
            self._materials = material
            self._material = material[0] if material else None  # Primary material
        else:
            self._materials = [material] if material else []

    def _require_tag(self) -> int:
        """Return the assigned tag, or raise if this element is unmanaged."""
        if self.tag is None:
            raise ValueError(
                f"Element of type '{self.element_type}' must be added to an ElementManager "
                "before rendering TCL."
            )
        return self.tag

    def assign_material(self, material: Union[Material, List[Material]]):
        """Assigns a material to the element."""
        if isinstance(material, list):
            self._materials = material
            self._material = material[0] if material else None
        else:
            self._material = material
            self._materials = [material] if material else []

    def assign_section(self, section: Section):
        """Assigns a section to the element."""
        self._section = section

    def assign_transformation(self, transformation: GeometricTransformation):
        """Assigns a geometric transformation to the element."""
        self._transformation = transformation

    def assign_ndof(self, ndof: int):
        """Assigns the number of DOFs for the element."""
        self._ndof = ndof

    def get_material(self) -> Optional[Material]:
        """Retrieves the primary assigned material."""
        return self._material

    def get_materials(self) -> List[Material]:
        """Retrieves all assigned materials."""
        return self._materials.copy()

    def get_section(self) -> Optional[Section]:
        """Retrieves the assigned section."""
        return self._section

    def get_transformation(self) -> Optional[GeometricTransformation]:
        """Retrieves the assigned geometric transformation."""
        return self._transformation

    def get_element_params(self) -> Dict[str, Any]:
        """Retrieves element-specific parameters."""
        return self.element_params.copy()

    def update_element_params(self, **new_params):
        """Updates element-specific parameters."""
        self.element_params.update(new_params)

    def get_ndof(self) -> int:
        """Gets the number of degrees of freedom for this element."""
        return self._ndof

    @abstractmethod
    def to_tcl(self, tag: int, nodes: List[int]) -> str:
        """Converts the element to a TCL command string for OpenSees."""
        pass

    def __str__(self) -> str:
        tag_str = self.tag if self.tag is not None else "unmanaged"
        return f"{self.element_type} Element (Tag: {tag_str}, DOF: {self._ndof})"

    def __repr__(self) -> str:
        tag_str = self.tag if self.tag is not None else "None"
        return f"Element(type='{self.element_type}', tag={tag_str}, ndof={self._ndof}, " \
               f"material={'Yes' if self._material else 'No'}, " \
               f"section={'Yes' if self._section else 'No'}, " \
               f"transformation={'Yes' if self._transformation else 'No'})"

    def get_section_tag(self) -> Optional[int]:
        """Gets the tag of the assigned section."""
        return self._section.tag if self._section else 0

    def get_material_tag(self) -> Optional[int]:
        """Gets the tag of the primary assigned material."""
        return self._material.tag if self._material else 0

    def get_mass_per_length(self) -> float:
        """Gets the mass per length of the element."""
        return 0.0
    
    def get_density(self) -> float:
        """Gets the density of the element."""
        return 0.0

    @classmethod
    def get_all_elements(cls) -> Dict[int, "Element"]:
        """Return all managed elements in the active model context."""
        from femora.components.MeshMaker import MeshMaker

        return MeshMaker.get_instance().element.get_all()

    @classmethod
    def get_element_by_tag(cls, tag: int) -> Optional["Element"]:
        """Return a managed element by tag in the active model context."""
        from femora.components.MeshMaker import MeshMaker

        return MeshMaker.get_instance().element.get(int(tag))

    @classmethod
    def delete_element(cls, tag_or_name: int) -> None:
        """Remove a managed element by tag from the active model context."""
        from femora.components.MeshMaker import MeshMaker

        MeshMaker.get_instance().element.remove(int(tag_or_name))

    @classmethod
    def clear_all_elements(cls):
        """Test compatibility: clears all elements in the active MeshMaker."""
        from femora.components.MeshMaker import MeshMaker

        MeshMaker.get_instance().element.clear()
