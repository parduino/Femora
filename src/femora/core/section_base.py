from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

if TYPE_CHECKING:
    from femora.core.material_base import Material


class Section(ABC):
    """Abstract base class for all sections with manager-owned tagging.

    Section objects do not self-register and do not assign their own tags.
    A :class:`~femora.core.section_manager.SectionManager` owns lifecycle
    operations, tag assignment, removal, and retagging for a local model context.

    Args:
        section_type: The type of section (e.g., 'section').
        section_name: The specific section name for OpenSees (e.g., 'Elastic').
        user_name: User-specified name for the section.

    Attributes:
        tag: Manager-assigned OpenSees tag. It remains ``None`` until the
            instance is added to a :class:`~femora.core.section_manager.SectionManager`.
        _owner: Reference to the owning manager, or ``None`` when unmanaged.
    """

    def __init__(self, section_type: str, section_name: str, user_name: str):
        self.tag: Optional[int] = None
        self._owner: Optional[Any] = None  # Should be SectionManager
        self.section_type = section_type
        self.section_name = section_name
        self.user_name = user_name
        
        # Base class material placeholder
        self.material: Optional[Material] = None

    def _require_tag(self) -> int:
        """Return the assigned tag or fail if the instance is unmanaged.

        Returns:
            The manager-assigned integer tag.

        Raises:
            ValueError: If this section has not been added to a manager.
        """
        if self.tag is None:
            raise ValueError(f"Section '{self.user_name}' must be managed before rendering TCL")
        return self.tag

    @abstractmethod
    def to_tcl(self) -> str:
        """Convert the section to a TCL string representation for OpenSees.

        Returns:
            TCL command string for this section.
        """
        raise NotImplementedError

    def resolve_material(self, material_input: Union[int, str, "Material", None]) -> Optional["Material"]:
        """Resolve material using the owner manager when possible."""
        if self._owner and hasattr(self._owner, "resolve_material"):
            return self._owner.resolve_material(material_input)
        return self.resolve_material_reference(material_input)

    def resolve_materials_dict(
        self, materials_input: Dict[str, Union[int, str, "Material"]]
    ) -> Dict[str, "Material"]:
        """Resolve a dictionary of material references."""
        return {key: self.resolve_material(value) for key, value in materials_input.items()}

    def resolve_section(self, section_input: Union[int, str, "Section", None]) -> Optional["Section"]:
        """Resolve another section using the owner manager when possible."""
        if section_input is None:
            return None
        if isinstance(section_input, Section):
            return section_input
        if self._owner and hasattr(self._owner, "get"):
            return self._owner.get(section_input)

        from femora.components.MeshMaker import MeshMaker

        return MeshMaker.get_instance().section.get(section_input)

    @staticmethod
    def resolve_material_reference(
        material_input: Union[int, str, "Material", None]
    ) -> Optional["Material"]:
        """Resolve material from object, tag, or name using global fallback."""
        if material_input is None:
            return None

        from femora.core.material_base import Material as MaterialClass

        if isinstance(material_input, MaterialClass):
            return material_input

        if isinstance(material_input, (int, str)):
            try:
                from femora.components.MeshMaker import MeshMaker

                material = MeshMaker.get_instance().material.get(material_input)
                if material is None:
                    raise KeyError(material_input)
                return material
            except (KeyError, TypeError, AttributeError) as exc:
                raise ValueError(f"Material not found: {material_input}. Error: {exc}") from exc

        raise ValueError(
            f"Invalid material input type: {type(material_input)}. "
            "Expected Material object, int (tag), str (name), or None"
        )

    def get_materials(self) -> List["Material"]:
        """Return materials used by this section for dependency tracking."""
        if self.material is not None:
            return [self.material]
        return []

    def has_material(self) -> bool:
        """Return True when this section depends on a material."""
        return self.material is not None

    def get_area(self) -> float:
        """Return cross-sectional area when the section provides it."""
        return 0.0

    def get_Iy(self) -> float:
        """Return second moment of area about local y when available."""
        return 0.0

    def get_Iz(self) -> float:
        """Return second moment of area about local z when available."""
        return 0.0

    def get_J(self) -> float:
        """Return torsional constant when the section provides it."""
        return 0.0

    def __str__(self) -> str:
        tag = self.tag if self.tag is not None else "unmanaged"
        material_info = f", Material: {self.material.user_name}" if self.material else ", No Material"
        return (f"Section '{self.user_name}' (Tag: {tag}, Type: {self.section_name}"
                f"{material_info})")
