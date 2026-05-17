from abc import ABC, abstractmethod
from typing import List, Dict, Type, Optional, Union, Any, TYPE_CHECKING
from femora.core.material_base import Material
from femora.core.section_base import Section
from femora.core.transformation_base import GeometricTransformation

if TYPE_CHECKING:
    from femora.components.MeshMaker import MeshMaker


class Element(ABC):
    """Base abstract class for all OpenSees finite elements.

    This class provides a foundation for creating and managing finite element
    objects in structural analysis. It handles automatic tag assignment, element
    registration, and dependency management for materials, sections, and
    geometric transformations.

    Attributes:
        tag: The unique sequential identifier for this element.
        element_type: The type of element (e.g., 'quad', 'truss', 'beam').
        _ndof: Number of degrees of freedom for the element.
        element_params: Dictionary of element-specific parameters.
        _material: Primary material assigned to this element.
        _materials: List of all materials assigned to this element.
        _section: Section assigned to this element (for section-based elements).
        _transformation: Geometric transformation assigned to this element (for beam elements).
    """
    _elements = {}  # Dictionary mapping tags to elements
    _element_to_tag = {}  # Dictionary mapping elements to their tags
    _next_tag = 1  # Track the next available tag

    def __init__(self, element_type: str,
                 ndof: int,
                 material: Union[Material, List[Material], None] = None,
                 section: Section = None,
                 transformation: GeometricTransformation = None,
                 **element_params
                 ):
        """Initializes the Element with flexible dependency support."""
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

        # Assign the next available tag
        self.tag = self._next_tag
        Element._next_tag += 1

        # Register this element in both mapping dictionaries
        Element._elements[self.tag] = self
        Element._element_to_tag[self] = self.tag

    @classmethod
    def _retag_elements(cls):
        """Retags all elements sequentially from 1 to n based on their current order."""
        sorted_elements = sorted(cls._elements.items(), key=lambda x: x[0])
        cls._elements.clear()
        cls._element_to_tag.clear()

        for new_tag, (old_tag, element) in enumerate(sorted_elements, start=1):
            element.tag = new_tag
            cls._elements[new_tag] = element
            cls._element_to_tag[element] = new_tag

        cls._next_tag = len(sorted_elements) + 1

    @classmethod
    def delete_element(cls, tag: int) -> None:
        """Deletes an element by its tag and retags remaining elements."""
        if tag in cls._elements:
            element = cls._elements[tag]
            del cls._elements[tag]
            del cls._element_to_tag[element]
            cls._retag_elements()

    @classmethod
    def get_element_by_tag(cls, tag: int) -> Optional['Element']:
        """Gets an element by its tag."""
        return cls._elements.get(tag)

    @classmethod
    def get_tag_by_element(cls, element: 'Element') -> Optional[int]:
        """Gets an element's tag."""
        return cls._element_to_tag.get(element)

    @classmethod
    def set_tag_start(cls, start_number: int):
        """Sets the starting number for element tags."""
        if not cls._elements:
            cls._next_tag = start_number
        else:
            offset = start_number - 1
            new_elements = {(tag + offset): element for tag, element in cls._elements.items()}
            new_element_to_tag = {element: (tag + offset) for element, tag in cls._element_to_tag.items()}
            for element in cls._elements.values():
                element.tag += offset
            cls._elements = new_elements
            cls._element_to_tag = new_element_to_tag
            cls._next_tag = max(cls._elements.keys()) + 1

    @classmethod
    def get_all_elements(cls) -> Dict[int, 'Element']:
        """Retrieves all created elements."""
        return cls._elements

    @classmethod
    def clear_all_elements(cls):
        """Clears all elements and resets tag counter."""
        cls._elements.clear()
        cls._element_to_tag.clear()
        cls._next_tag = 1

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

    @classmethod
    @abstractmethod
    def get_parameters(cls) -> List[str]:
        """Gets the list of parameters for this element type."""
        pass

    @classmethod
    @abstractmethod
    def get_possible_dofs(cls) -> List[str]:
        """Gets the list of possible DOFs for this element type."""
        pass

    @classmethod
    @abstractmethod
    def get_description(cls) -> List[str]:
        """Gets the list of parameter descriptions for this element type."""
        pass

    @classmethod
    @abstractmethod
    def validate_element_parameters(cls, **kwargs) -> Dict[str, Union[int, float, str]]:
        """Checks if the element input parameters are valid."""
        pass

    @abstractmethod
    def get_values(self, keys: List[str]) -> Dict[str, Union[int, float, str]]:
        """Retrieves values for specific parameters."""
        pass

    @abstractmethod
    def update_values(self, values: Dict[str, Union[int, float, str]]) -> None:
        """Updates element parameters."""
        pass

    @abstractmethod
    def to_tcl(self, tag: int, nodes: List[int]) -> str:
        """Converts the element to a TCL command string for OpenSees."""
        pass

    def __str__(self) -> str:
        return f"{self.element_type} Element (Tag: {self.tag}, DOF: {self._ndof})"

    def __repr__(self) -> str:
        return f"Element(type='{self.element_type}', tag={self.tag}, ndof={self._ndof}, " \
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


class ElementRegistry:
    """Manager to manage element types and their creation with model-aware resolution."""
    _element_types: Dict[str, Type[Element]] = {}

    def __init__(self, mesh_maker: Optional["MeshMaker"] = None):
        self._mesh_maker = mesh_maker

    @property
    def beam(self):
        from femora.core.element_manager import _BeamElements
        return _BeamElements

    @property
    def brick(self):
        from femora.core.element_manager import _BrickElements
        return _BrickElements

    @property
    def quad(self):
        from femora.core.element_manager import _QuadElements
        return _QuadElements

    @property
    def special(self):
        from femora.core.element_manager import _SpecialElements
        return _SpecialElements

    @classmethod
    def register_element_type(cls, name: str, element_class: Type[Element]):
        """Registers a new element type (class-level)."""
        cls._element_types[name] = element_class

    @classmethod
    def get_element_types(cls) -> List[str]:
        """Gets available element types (class-level)."""
        return list(cls._element_types.keys())

    def create_element(self, element_type: str, **kwargs) -> Element:
        """Creates a new element with model-aware dependency resolution."""
        if element_type not in self._element_types:
            raise KeyError(f"Element type '{element_type}' not registered.")

        resolved_kwargs = kwargs.copy()

        if 'material' in resolved_kwargs:
            resolved_kwargs['material'] = self._resolve_materials(resolved_kwargs['material'])

        if 'section' in resolved_kwargs:
            resolved_kwargs['section'] = self._resolve_section(resolved_kwargs['section'])

        if 'transformation' in resolved_kwargs:
            resolved_kwargs['transformation'] = self._resolve_transformation(resolved_kwargs['transformation'])

        return self._element_types[element_type](**resolved_kwargs)

    def _resolve_materials(self, material):
        if material is None:
            return None

        if isinstance(material, list):
            resolved_materials = []
            for i, mat in enumerate(material):
                if isinstance(mat, (str, int)):
                    resolved_mat = self._get_material(mat)
                    if resolved_mat is None:
                        raise ValueError(f"Material {mat} at index {i} not found")
                    resolved_materials.append(resolved_mat)
                elif isinstance(mat, Material):
                    resolved_materials.append(mat)
                else:
                    raise ValueError(f"Invalid material type at index {i}: {type(mat)}")
            return resolved_materials

        elif isinstance(material, (str, int)):
            resolved_material = self._get_material(material)
            if resolved_material is None:
                raise ValueError(f"Material '{material}' not found")
            return resolved_material

        elif isinstance(material, Material):
            return material
        raise ValueError(f"Invalid material type: {type(material)}")

    def _resolve_section(self, section):
        if section is None:
            return None
        if isinstance(section, (str, int)):
            resolved_section = self._get_section(section)
            if resolved_section is None:
                raise ValueError(f"Section '{section}' not found")
            return resolved_section
        elif isinstance(section, Section):
            return section
        raise ValueError(f"Invalid section type: {type(section)}")

    def _resolve_transformation(self, transformation):
        if transformation is None:
            return None
        if isinstance(transformation, str):
            raise ValueError("Transformation lookup by name not supported; pass managed object")
        if isinstance(transformation, int):
            resolved_transformation = self._get_transformation(transformation)
            if resolved_transformation is None:
                raise ValueError(f"Transformation '{transformation}' not found")
            return resolved_transformation
        elif isinstance(transformation, GeometricTransformation):
            if transformation.tag is None:
                raise ValueError("Transformation must be managed")
            return transformation
        raise ValueError(f"Invalid transformation type: {type(transformation)}")

    def _get_material(self, identifier):
        if self._mesh_maker:
            return self._mesh_maker.material.get(identifier)
        from femora.components.MeshMaker import MeshMaker
        return MeshMaker.get_instance().material.get(identifier)

    def _get_section(self, identifier):
        if self._mesh_maker:
            return self._mesh_maker.section.get(identifier)
        from femora.components.MeshMaker import MeshMaker
        return MeshMaker.get_instance().section.get(identifier)

    def _get_transformation(self, identifier):
        if self._mesh_maker:
            return self._mesh_maker.transformation.get(identifier)
        from femora.components.MeshMaker import MeshMaker
        return MeshMaker.get_instance().transformation.get(identifier)

    def get_element(self, tag: int) -> Optional[Element]:
        """Gets an element by its tag."""
        return Element.get_element_by_tag(tag)

    def get_element_count(self) -> int:
        """Gets the total number of registered elements."""
        return len(Element.get_all_elements())

    def clear_all_elements(self):
        """Clears all elements and resets the element tag counter."""
        Element.clear_all_elements()

    def clear(self):
        self.clear_all_elements()


# Import existing element implementations
from femora.components.element import ssp_brick
from femora.components.element import ssp_quad
from femora.components.element import std_brick
from femora.components.element import pml_3d
from femora.components.element import asd_embedded_node
from femora.components.element import zero_length_contact
from femora.components.element import disp_beam_column
from femora.components.element import force_beam_column
from femora.components.element import elastic_beam_column
from femora.components.element import ghost_node
