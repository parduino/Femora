from abc import ABC, abstractmethod
from typing import List, Dict, Type, Optional, Union, Any
from femora.components.Material.materialBase import Material, MaterialManager
from femora.components.section.section_base import Section, SectionManager
from femora.components.transformation.transformation import GeometricTransformation, GeometricTransformationManager


class Element(ABC):
    """
    Base abstract class for all OpenSees elements
    Material, section, and transformation validation is handled by child classes
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
        """
        Initialize a new element with flexible dependency support.
        Child classes handle validation of materials, sections, and transformations.

        Args:
            element_type (str): The type of element (e.g., 'quad', 'truss')
            ndof (int): Number of degrees of freedom for the element
            material (Union[Material, List[Material], None]): Material(s) for the element
            section (Section, optional): Section for section-based elements
            transformation (GeometricTransformation, optional): Transformation for beam elements
            **element_params: Element-specific parameters (thickness, body forces, etc.)
        """
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
        """
        Retag all elements sequentially from 1 to n based on their current order.
        Updates both mapping dictionaries.
        """
        # Get all current elements sorted by their tags
        sorted_elements = sorted(cls._elements.items(), key=lambda x: x[0])
        
        # Clear existing mappings
        cls._elements.clear()
        cls._element_to_tag.clear()
        
        # Reassign tags sequentially
        for new_tag, (old_tag, element) in enumerate(sorted_elements, start=1):
            element.tag = new_tag
            cls._elements[new_tag] = element
            cls._element_to_tag[element] = new_tag
        
        # Update next available tag
        cls._next_tag = len(sorted_elements) + 1

    @classmethod
    def delete_element(cls, tag: int) -> None:
        """
        Delete an element by its tag and retag remaining elements.
        
        Args:
            tag (int): The tag of the element to delete
        """
        if tag in cls._elements:
            element = cls._elements[tag]
            # Remove from both dictionaries
            del cls._elements[tag]
            del cls._element_to_tag[element]
            # Retag remaining elements
            cls._retag_elements()

    @classmethod
    def get_element_by_tag(cls, tag: int) -> Optional['Element']:
        """
        Get an element by its tag.
        
        Args:
            tag (int): The tag to look up
            
        Returns:
            Optional[Element]: The element with the given tag, or None if not found
        """
        return cls._elements.get(tag)

    @classmethod
    def get_tag_by_element(cls, element: 'Element') -> Optional[int]:
        """
        Get an element's tag.
        
        Args:
            element (Element): The element to look up
            
        Returns:
            Optional[int]: The tag for the given element, or None if not found
        """
        return cls._element_to_tag.get(element)

    @classmethod
    def set_tag_start(cls, start_number: int):
        """
        Set the starting number for element tags and retag all existing elements.
        
        Args:
            start_number (int): The first tag number to use
        """
        if not cls._elements:
            cls._next_tag = start_number
        else:
            offset = start_number - 1
            # Create new mappings with offset tags
            new_elements = {(tag + offset): element for tag, element in cls._elements.items()}
            new_element_to_tag = {element: (tag + offset) for element, tag in cls._element_to_tag.items()}
            
            # Update all element tags
            for element in cls._elements.values():
                element.tag += offset
            
            # Replace the mappings
            cls._elements = new_elements
            cls._element_to_tag = new_element_to_tag
            cls._next_tag = max(cls._elements.keys()) + 1

    @classmethod
    def get_all_elements(cls) -> Dict[int, 'Element']:
        """
        Retrieve all created elements.
        
        Returns:
            Dict[int, Element]: A dictionary of all elements, keyed by their unique tags
        """
        return cls._elements

    @classmethod
    def clear_all_elements(cls):
        """Clear all elements and reset tag counter."""
        cls._elements.clear()
        cls._element_to_tag.clear()
        cls._next_tag = 1

    def assign_material(self, material: Union[Material, List[Material]]):
        """
        Assign a material to the element.
        Note: Child classes may override this to add validation.
        
        Args:
            material (Union[Material, List[Material]]): The material(s) to assign
        """
        if isinstance(material, list):
            self._materials = material
            self._material = material[0] if material else None
        else:
            self._material = material
            self._materials = [material] if material else []

    def assign_section(self, section: Section):
        """
        Assign a section to the element.
        Note: Child classes may override this to add validation.
        
        Args:
            section (Section): The section to assign
        """
        self._section = section

    def assign_transformation(self, transformation: GeometricTransformation):
        """
        Assign a geometric transformation to the element.
        Note: Child classes may override this to add validation.
        
        Args:
            transformation (GeometricTransformation): The transformation to assign
        """
        self._transformation = transformation

    def assign_ndof(self, ndof: int):
        """
        Assign the number of DOFs for the element
        
        Args:
            ndof (int): Number of DOFs for the element
        """
        self._ndof = ndof

    def get_material(self) -> Optional[Material]:
        """
        Retrieve the primary assigned material
        
        Returns:
            Optional[Material]: The primary material assigned to this element, or None
        """
        return self._material

    def get_materials(self) -> List[Material]:
        """
        Retrieve all assigned materials
        
        Returns:
            List[Material]: List of all materials assigned to this element
        """
        return self._materials.copy()

    def get_section(self) -> Optional[Section]:
        """
        Retrieve the assigned section
        
        Returns:
            Optional[Section]: The section assigned to this element, or None
        """
        return self._section

    def get_transformation(self) -> Optional[GeometricTransformation]:
        """
        Retrieve the assigned geometric transformation
        
        Returns:
            Optional[GeometricTransformation]: The transformation assigned to this element, or None
        """
        return self._transformation

    def get_element_params(self) -> Dict[str, Any]:
        """
        Retrieve element-specific parameters
        
        Returns:
            Dict[str, Any]: Dictionary of element-specific parameters
        """
        return self.element_params.copy()

    def update_element_params(self, **new_params):
        """
        Update element-specific parameters
        
        Args:
            **new_params: New parameter values to update
        """
        self.element_params.update(new_params)

    def get_ndof(self) -> int:
        """
        Get the number of degrees of freedom for this element
        
        Returns:
            int: Number of DOFs
        """
        return self._ndof

    # Abstract methods for element implementation
    @classmethod  
    @abstractmethod
    def get_parameters(cls) -> List[str]:
        """
        Get the list of parameters for this element type.
        
        Returns:
            List[str]: List of parameter names
        """
        pass

    @classmethod
    @abstractmethod
    def get_possible_dofs(cls) -> List[str]:
        """
        Get the list of possible DOFs for this element type.
        
        Returns:
            List[str]: List of possible DOFs
        """
        pass

    @classmethod
    @abstractmethod
    def get_description(cls) -> List[str]:
        """
        Get the list of parameter descriptions for this element type.
        
        Returns:
            List[str]: List of parameter descriptions
        """
        pass

    @classmethod
    @abstractmethod
    def validate_element_parameters(cls, **kwargs) -> Dict[str, Union[int, float, str]]:
        """
        Check if the element input parameters are valid.
        
        Args:
            **kwargs: Element parameters to validate
        
        Returns:
            Dict[str, Union[int, float, str]]: Dictionary of parameters with valid values
        """
        pass

    @abstractmethod
    def get_values(self, keys: List[str]) -> Dict[str, Union[int, float, str]]:
        """
        Retrieve values for specific parameters.
        
        Args:
            keys (List[str]): List of parameter names to retrieve
        
        Returns:
            Dict[str, Union[int, float, str]]: Dictionary of parameter values
        """
        pass

    @abstractmethod
    def update_values(self, values: Dict[str, Union[int, float, str]]) -> None:
        """
        Update element parameters.
        
        Args:
            values (Dict[str, Union[int, float, str]]): Dictionary of parameter names and values to update
        """
        pass

    @abstractmethod
    def to_tcl(self, tag: int, nodes: List[int]) -> str:
        """
        Convert the element to a TCL command string.
        
        Args:
            tag (int): The tag of the element
            nodes (List[int]): List of node tags for the element
        
        Returns:
            str: TCL command string representation of the element
        """
        pass

    def __str__(self) -> str:
        """String representation of the element"""
        return f"{self.element_type} Element (Tag: {self.tag}, DOF: {self._ndof})"

    def __repr__(self) -> str:
        """Detailed string representation of the element"""
        return f"Element(type='{self.element_type}', tag={self.tag}, ndof={self._ndof}, " \
               f"material={'Yes' if self._material else 'No'}, " \
               f"section={'Yes' if self._section else 'No'}, " \
               f"transformation={'Yes' if self._transformation else 'No'})"



class ElementRegistry:
    """
    A singleton registry to manage element types and their creation with full dependency resolution.
    """
    _instance = None
    _element_types = {}

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(ElementRegistry, cls).__new__(cls)
        return cls._instance

    @classmethod
    def register_element_type(cls, name: str, element_class: Type[Element]):
        """
        Register a new element type for easy creation.
        
        Args:
            name (str): The name of the element type
            element_class (Type[Element]): The class of the element
        """
        cls._element_types[name] = element_class

    @classmethod
    def unregister_element_type(cls, name: str):
        """
        Unregister an element type.
        
        Args:
            name (str): The name of the element type to remove
        """
        if name in cls._element_types:
            del cls._element_types[name]

    @classmethod
    def get_element_types(cls) -> List[str]:
        """
        Get available element types.
        
        Returns:
            List[str]: Available element types
        """
        return list(cls._element_types.keys())

    @classmethod
    def is_element_type_registered(cls, name: str) -> bool:
        """
        Check if an element type is registered.
        
        Args:
            name (str): The element type name to check
            
        Returns:
            bool: True if registered, False otherwise
        """
        return name in cls._element_types

    @classmethod
    def create_element(cls, 
                       element_type: str, 
                       **kwargs) -> Element:
        """
        Create a new element of a specific type with full dependency resolution.

        Args:
            element_type (str): Type of element to create
            **kwargs: All element parameters including ndof, material, section, transformation

        Returns:
            Element: A new element instance

        Raises:
            KeyError: If the element type is not registered
            ValueError: If dependencies cannot be resolved
        """
        if element_type not in cls._element_types:
            raise KeyError(f"Element type '{element_type}' not registered. "
                          f"Available types: {list(cls._element_types.keys())}")

        # Resolve dependencies
        resolved_kwargs = kwargs.copy()
        
        if 'material' in resolved_kwargs:
            resolved_kwargs['material'] = cls._resolve_materials(resolved_kwargs['material'])
        
        if 'section' in resolved_kwargs:
            resolved_kwargs['section'] = cls._resolve_section(resolved_kwargs['section'])
            
        if 'transformation' in resolved_kwargs:
            resolved_kwargs['transformation'] = cls._resolve_transformation(resolved_kwargs['transformation'])
        
        return cls._element_types[element_type](**resolved_kwargs)
    
    @classmethod
    def _resolve_materials(cls, material):
        """
        Resolve material references to actual Material objects
        
        Args:
            material: Material reference (str, int, Material, or list of these)
            
        Returns:
            Resolved material object(s) or None
        """
        if material is None:
            return None
        
        if isinstance(material, list):
            # List of materials
            resolved_materials = []
            for i, mat in enumerate(material):
                if isinstance(mat, (str, int)):
                    resolved_mat = MaterialManager.get_material(mat)
                    if resolved_mat is None:
                        raise ValueError(f"Material {mat} at index {i} not found")
                    resolved_materials.append(resolved_mat)
                elif isinstance(mat, Material):
                    resolved_materials.append(mat)
                else:
                    raise ValueError(f"Invalid material type at index {i}: {type(mat)}")
            return resolved_materials
        
        elif isinstance(material, (str, int)):
            # Single material by reference
            resolved_material = MaterialManager.get_material(material)
            if resolved_material is None:
                raise ValueError(f"Material '{material}' not found")
            return resolved_material
        
        elif isinstance(material, Material):
            # Already a Material object
            return material
        
        else:
            raise ValueError(f"Invalid material type: {type(material)}")
    
    @classmethod
    def _resolve_section(cls, section):
        """
        Resolve section references to actual Section objects
        
        Args:
            section: Section reference (str, int, Section, or None)
            
        Returns:
            Resolved section object or None
        """
        if section is None:
            return None
        
        if isinstance(section, (str, int)):
            resolved_section = SectionManager.get_section(section)
            if resolved_section is None:
                raise ValueError(f"Section '{section}' not found")
            return resolved_section
        elif isinstance(section, Section):
            return section
        else:
            raise ValueError(f"Invalid section type: {type(section)}")
    
    @classmethod
    def _resolve_transformation(cls, transformation):
        """
        Resolve transformation references to actual GeometricTransformation objects
        
        Args:
            transformation: Transformation reference (str, int, GeometricTransformation, or None)
            
        Returns:
            Resolved transformation object or None
        """
        if transformation is None:
            return None
        
        if isinstance(transformation, (str, int)):
            resolved_transformation = GeometricTransformationManager.get_transformation(transformation)
            if resolved_transformation is None:
                raise ValueError(f"Transformation '{transformation}' not found")
            return resolved_transformation
        elif isinstance(transformation, GeometricTransformation):
            return transformation
        else:
            raise ValueError(f"Invalid transformation type: {type(transformation)}")
    
    @classmethod
    def get_element(cls, tag: int) -> Optional[Element]:
        """
        Get an element by its tag.
        
        Args:
            tag (int): The tag of the element to retrieve
            
        Returns:
            Optional[Element]: The element with the given tag, or None if not found
        """
        return Element.get_element_by_tag(tag)
    
    @classmethod
    def get_element_count(cls) -> int:
        """
        Get the total number of registered elements.
        
        Returns:
            int: Number of elements
        """
        return len(Element.get_all_elements())
    
    @classmethod
    def clear_all_elements(cls):
        """Clear all elements."""
        Element.clear_all_elements()


# Import existing element implementations
from femora.components.Element.elementsOpenSees import *
from femora.components.Element.elements_opensees_beam import *