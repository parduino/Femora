from __future__ import annotations

from typing import TYPE_CHECKING, Dict, Iterator, Optional, Type, List, Union

from femora.core.element_base import Element
from femora.core.tagging import CompactRetagPolicy
from femora.core.material_base import Material
from femora.core.section_base import Section
from femora.core.transformation_base import GeometricTransformation

if TYPE_CHECKING:
    from femora.components.MeshMaker import MeshMaker


class ElementManager:
    """Local manager for ``Element`` lifecycle and tag assignment."""

    _element_types: Dict[str, Type[Element]] = {}

    def __init__(self, mesh_maker: MeshMaker):
        from femora.components.MeshMaker import MeshMaker as MeshMakerClass

        if not isinstance(mesh_maker, MeshMakerClass):
            raise TypeError("mesh_maker must be a MeshMaker instance")
        self._mesh_maker = mesh_maker
        self._elements: Dict[int, Element] = {}
        self._start_tag = 1
        self._tagging = CompactRetagPolicy[Element]()

        # Initialize namespaces
        self.beam = BeamElementManager(self)
        self.brick = BrickElementManager(self)
        self.quad = QuadElementManager(self)
        self.special = SpecialElementManager(self)

    @classmethod
    def register_element_type(cls, name: str, element_class: Type[Element]):
        """Registers a new element type (class-level)."""
        cls._element_types[name] = element_class

    @classmethod
    def get_element_types(cls) -> List[str]:
        """Gets available element types (class-level)."""
        return list(cls._element_types.keys())

    # ------------------------------------------------------------------
    # Core lifecycle
    # ------------------------------------------------------------------

    def add(self, element: Element) -> Element:
        if not isinstance(element, Element):
            raise TypeError("element must be an Element instance")
        if element._owner is None:
            element._owner = self
        elif element._owner is not self:
            raise ValueError("element already belongs to another manager")

        try:
            element.tag = self._tagging.assign_tag(
                self._elements, element, self._start_tag
            )
        except ValueError as exc:
            raise ValueError(f"Element tag {element.tag} already exists") from exc

        self._elements[element.tag] = element
        return element

    def get(self, tag: int) -> Optional[Element]:
        return self._elements.get(int(tag))

    def get_all(self) -> Dict[int, Element]:
        return dict(self._elements)

    def remove(self, tag: int) -> None:
        element = self._elements.pop(int(tag), None)
        if element is not None:
            element.tag = None
            element._owner = None
            self._reassign_tags()

    def clear(self) -> None:
        for element in list(self._elements.values()):
            element.tag = None
            element._owner = None
        self._elements.clear()

    def set_tag_start(self, start_tag: int) -> None:
        self._start_tag = self._tagging.validate_start_tag(start_tag)
        self._reassign_tags()

    get_element = get
    get_all_elements = get_all
    clear_all_elements = clear

    def get_element_count(self) -> int:
        return len(self._elements)

    def __len__(self) -> int:
        return len(self._elements)

    def __iter__(self) -> Iterator[Element]:
        return iter(self._elements.values())

    def _reassign_tags(self) -> None:
        self._tagging.reassign_tags(self._elements, self._start_tag)

    def create_element(self, element_type: str, **kwargs) -> Element:
        """Creates a new element with model-aware dependency resolution and adds it to the manager."""
        if element_type not in self._element_types:
            raise KeyError(f"Element type '{element_type}' not registered.")

        resolved_kwargs = kwargs.copy()

        if 'material' in resolved_kwargs:
            resolved_kwargs['material'] = self._resolve_materials(resolved_kwargs['material'])

        if 'section' in resolved_kwargs:
            resolved_kwargs['section'] = self._resolve_section(resolved_kwargs['section'])

        if 'transformation' in resolved_kwargs:
            resolved_kwargs['transformation'] = self._resolve_transformation(resolved_kwargs['transformation'])

        elem = self._element_types[element_type](**resolved_kwargs)
        return self.add(elem)

    def _resolve_materials(self, material):
        if material is None:
            return None

        if isinstance(material, list):
            resolved_materials = []
            for i, mat in enumerate(material):
                if isinstance(mat, (str, int)):
                    resolved_mat = self._mesh_maker.material.get(mat)
                    if resolved_mat is None:
                        raise ValueError(f"Material {mat} at index {i} not found")
                    resolved_materials.append(resolved_mat)
                elif isinstance(mat, Material):
                    resolved_materials.append(mat)
                else:
                    raise ValueError(f"Invalid material type at index {i}: {type(mat)}")
            return resolved_materials

        elif isinstance(material, (str, int)):
            resolved_material = self._mesh_maker.material.get(material)
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
            resolved_section = self._mesh_maker.section.get(section)
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
            resolved_transformation = self._mesh_maker.transformation.get(transformation)
            if resolved_transformation is None:
                raise ValueError(f"Transformation '{transformation}' not found")
            return resolved_transformation
        elif isinstance(transformation, GeometricTransformation):
            if transformation.tag is None:
                raise ValueError("Transformation must be managed")
            return transformation
        raise ValueError(f"Invalid transformation type: {type(transformation)}")

# Import existing element implementations
from femora.components.element import SSPQuadElement, stdBrickElement, PML3DElement, SSPbrickElement
from femora.components.element import DispBeamColumnElement, ForceBeamColumnElement, ElasticBeamColumnElement
from femora.components.element import GhostNodeElement
from femora.components.element import TrussElement
from femora.components.element import ASDEmbeddedNodeElement3D, ZeroLengthContactASDimplex

# Register elements for create_element compatibility
ElementManager.register_element_type('ElasticBeamColumn', ElasticBeamColumnElement)
ElementManager.register_element_type('DispBeamColumn', DispBeamColumnElement)
ElementManager.register_element_type('NonlinearBeamColumn', ForceBeamColumnElement)
ElementManager.register_element_type('ForceBasedBeamColumn', ForceBeamColumnElement)
ElementManager.register_element_type('Truss', TrussElement)
ElementManager.register_element_type('truss', TrussElement)
ElementManager.register_element_type('trussSection', TrussElement)
ElementManager.register_element_type('stdBrick', stdBrickElement)
ElementManager.register_element_type('PML3D', PML3DElement)
ElementManager.register_element_type('SSPbrick', SSPbrickElement)
ElementManager.register_element_type('SSPQuad', SSPQuadElement)
ElementManager.register_element_type('GhostNode', GhostNodeElement)
ElementManager.register_element_type('ASDEmbeddedNodeElement3D', ASDEmbeddedNodeElement3D)
ElementManager.register_element_type('ZeroLengthContactASDimplex', ZeroLengthContactASDimplex)

# Namespace Factories

class BeamElementManager:
    def __init__(self, manager: ElementManager):
        self._manager = manager

    def elastic(self, ndof: int, section, transformation, **kwargs):
        from femora.components.element.elastic_beam_column import ElasticBeamColumnElement
        sec = self._manager._resolve_section(section)
        transf = self._manager._resolve_transformation(transformation)
        return self._manager.add(ElasticBeamColumnElement(ndof, sec, transf, **kwargs))

    def disp(self, ndof: int, section, transformation, **kwargs):
        from femora.components.element.disp_beam_column import DispBeamColumnElement
        sec = self._manager._resolve_section(section)
        transf = self._manager._resolve_transformation(transformation)
        return self._manager.add(DispBeamColumnElement(ndof, sec, transf, **kwargs))

    def force(self, ndof: int, section, transformation, **kwargs):
        from femora.components.element.force_beam_column import ForceBeamColumnElement
        sec = self._manager._resolve_section(section)
        transf = self._manager._resolve_transformation(transformation)
        return self._manager.add(ForceBeamColumnElement(ndof, sec, transf, **kwargs))

    def truss(self, ndof: int, material=None, section=None, **kwargs):
        from femora.components.element.truss import TrussElement
        if material is not None and section is not None:
            raise ValueError("TrussElement manager path expects either material or section, not both")
        if material is not None:
            raise ValueError("TrussElement currently requires a managed section; material-based truss creation is not supported")
        sec = self._manager._resolve_section(section) if section else None
        return self._manager.add(TrussElement(ndof, section=sec, **kwargs))

class BrickElementManager:
    def __init__(self, manager: ElementManager):
        self._manager = manager

    def std(self, ndof: int, material, **kwargs):
        from femora.components.element.std_brick import stdBrickElement
        mat = self._manager._resolve_materials(material)
        return self._manager.add(stdBrickElement(ndof, mat, **kwargs))

    def pml3d(self, ndof: int, material, **kwargs):
        from femora.components.element.pml_3d import PML3DElement
        mat = self._manager._resolve_materials(material)
        return self._manager.add(PML3DElement(ndof, mat, **kwargs))

    def ssp(self, ndof: int, material, **kwargs):
        from femora.components.element.ssp_brick import SSPbrickElement
        mat = self._manager._resolve_materials(material)
        return self._manager.add(SSPbrickElement(ndof, mat, **kwargs))

class QuadElementManager:
    def __init__(self, manager: ElementManager):
        self._manager = manager

    def ssp(self, ndof: int, material, **kwargs):
        from femora.components.element.ssp_quad import SSPQuadElement
        mat = self._manager._resolve_materials(material)
        return self._manager.add(SSPQuadElement(ndof, mat, **kwargs))

class SpecialElementManager:
    def __init__(self, manager: ElementManager):
        self._manager = manager

    def ghost_node(self, ndof: int, **kwargs):
        from femora.components.element.ghost_node import GhostNodeElement
        return self._manager.add(GhostNodeElement(ndof, **kwargs))
