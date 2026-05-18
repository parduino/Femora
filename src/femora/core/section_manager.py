from __future__ import annotations

from typing import TYPE_CHECKING, Dict, Optional, Union, Type

from femora.core.tagging import CompactRetagPolicy
from femora.core.section_base import Section

if TYPE_CHECKING:
    from femora.components.MeshMaker import MeshMaker
    from femora.core.material_base import Material


class _BeamSectionNamespace:
    """Beam-section factory namespace bound to a SectionManager."""

    def __init__(self, manager: "SectionManager"):
        self._manager = manager

    def elastic(self, user_name: str = "Unnamed", **kwargs) -> Section:
        return self._manager.create_section("Elastic", user_name=user_name, **kwargs)

    def uniaxial(self, user_name: str = "Unnamed", **kwargs) -> Section:
        return self._manager.create_section("Uniaxial", user_name=user_name, **kwargs)

    def wf2d(self, user_name: str = "Unnamed", **kwargs) -> Section:
        return self._manager.create_section("WFSection2d", user_name=user_name, **kwargs)


class _CompositeSectionNamespace:
    """Composite-section factory namespace bound to a SectionManager."""

    def __init__(self, manager: "SectionManager"):
        self._manager = manager

    def aggregator(self, user_name: str = "Unnamed", **kwargs) -> Section:
        return self._manager.create_section("Aggregator", user_name=user_name, **kwargs)

    def parallel(self, user_name: str = "Unnamed", **kwargs) -> Section:
        return self._manager.create_section("Parallel", user_name=user_name, **kwargs)


class _FiberSectionNamespace:
    """Fiber-section factory namespace bound to a SectionManager."""

    def __init__(self, manager: "SectionManager"):
        self._manager = manager

    def section(self, user_name: str = "Unnamed", **kwargs) -> Section:
        return self._manager.create_section("Fiber", user_name=user_name, **kwargs)

    def rc(self, user_name: str = "Unnamed", **kwargs) -> Section:
        return self._manager.create_section("RC", user_name=user_name, **kwargs)


class _ShellSectionNamespace:
    """Shell-section factory namespace bound to a SectionManager."""

    def __init__(self, manager: "SectionManager"):
        self._manager = manager

    def elastic_membrane_plate(self, user_name: str = "Unnamed", **kwargs) -> Section:
        return self._manager.create_section(
            "ElasticMembranePlateSection",
            user_name=user_name,
            **kwargs,
        )

    def plate_fiber(self, user_name: str = "Unnamed", **kwargs) -> Section:
        return self._manager.create_section("PlateFiber", user_name=user_name, **kwargs)


class _SpecialSectionNamespace:
    """Special-section factory namespace bound to a SectionManager."""

    def __init__(self, manager: "SectionManager"):
        self._manager = manager

    def bidirectional(self, user_name: str = "Unnamed", **kwargs) -> Section:
        return self._manager.create_section("Bidirectional", user_name=user_name, **kwargs)

    def isolator2spring(self, user_name: str = "Unnamed", **kwargs) -> Section:
        return self._manager.create_section("Isolator2spring", user_name=user_name, **kwargs)


class SectionManager:
    """Local manager for ``Section`` lifecycle and tag assignment.

    The manager is intentionally not a singleton. Each instance owns an
    independent tag space so future model or ``MeshMaker`` instances can keep
    their own section collections.
    """
    _section_types: Dict[str, Type[Section]] = {}

    def __init__(self, mesh_maker: MeshMaker):
        """Create an empty manager with tags starting at ``1``.

        Args:
            mesh_maker: The owning MeshMaker instance.

        Raises:
            TypeError: If mesh_maker is not a MeshMaker instance.
            RuntimeError: If the MeshMaker already owns a SectionManager.
        """
        from femora.components.MeshMaker import MeshMaker as MeshMakerClass

        if not isinstance(mesh_maker, MeshMakerClass):
            raise TypeError("mesh_maker must be a MeshMaker instance")
        
        if hasattr(mesh_maker, "section") and mesh_maker.section is not None:
             if mesh_maker.section is not self:
                raise RuntimeError("MeshMaker already owns a SectionManager")

        self._mesh_maker = mesh_maker
        self._sections: Dict[int, Section] = {}
        self._names: Dict[str, Section] = {}
        self._start_tag = 1
        self._tagging = CompactRetagPolicy[Section]()
        self.beam = _BeamSectionNamespace(self)
        self.composite = _CompositeSectionNamespace(self)
        self.fiber = _FiberSectionNamespace(self)
        self.shell = _ShellSectionNamespace(self)
        self.special = _SpecialSectionNamespace(self)

    def add(self, section: Section) -> Section:
        """Add an existing section and assign a tag if needed.

        Args:
            section: Unmanaged or already-managed ``Section`` instance.

        Returns:
            The same ``section`` instance after it is stored by this manager.

        Raises:
            TypeError: If ``section`` is not a ``Section`` instance.
            ValueError: If its preassigned tag conflicts or name is duplicate.
        """
        if not isinstance(section, Section):
            raise TypeError("section must be a Section instance")
        
        if section.user_name in self._names and self._names[section.user_name] is not section:
            raise ValueError(f"Section name '{section.user_name}' already exists in this manager")

        if section._owner is None:
            section._owner = self
        elif section._owner is not self:
            raise ValueError("section already belongs to another manager")
        
        try:
            section.tag = self._tagging.assign_tag(
                self._sections,
                section,
                self._start_tag,
            )
        except ValueError as exc:
            raise ValueError(f"Section tag {section.tag} already exists") from exc
            
        self._sections[section.tag] = section
        self._names[section.user_name] = section
        return section

    def get(self, identifier: Union[int, str]) -> Optional[Section]:
        """Return the section with ``tag`` or ``user_name`` if it exists.

        Args:
            identifier: Section tag (int) or name (str) to look up.

        Returns:
            The matching ``Section`` instance, or ``None``.
        """
        if isinstance(identifier, int):
            return self._sections.get(identifier)
        return self._names.get(identifier)

    def get_all(self) -> Dict[int, Section]:
        """Return a shallow copy of all managed sections keyed by tag."""
        return dict(self._sections)

    def remove(self, identifier: Union[int, str]) -> None:
        """Remove a managed section and compact the remaining tags.

        Args:
            identifier: Tag or name of the section to remove. Missing sections are ignored.
        """
        section = self.get(identifier)
        if section is not None:
            self._sections.pop(section.tag, None)
            self._names.pop(section.user_name, None)
            section.tag = None
            section._owner = None
            self._reassign_tags()

    def clear(self) -> None:
        """Remove all sections and clear their assigned tags."""
        for section in self._sections.values():
            section.tag = None
            section._owner = None
        self._sections.clear()
        self._names.clear()

    def set_tag_start(self, start_tag: int) -> None:
        """Set the first tag used by this manager and retag existing objects.

        Args:
            start_tag: Positive integer for the first assigned tag.

        Raises:
            ValueError: If ``start_tag`` is less than ``1``.
        """
        self._start_tag = self._tagging.validate_start_tag(start_tag)
        self._reassign_tags()

    def create_section(self, section_type: str, user_name: str, **section_params) -> Section:
        """Create and manage a section by type name using the manager factory map.

        This is the authoritative creation path for the active runtime. It ensures
        that the section is context-aware during its initialization so it can
        resolve materials and other dependencies without global state.

        Args:
            section_type: Registered section type name.
            user_name: Unique name for the section.
            **section_params: Constructor arguments for the selected concrete class.

        Returns:
            Managed ``Section`` instance.

        Raises:
            KeyError: If ``section_type`` is not registered.
        """
        section_class = self._section_types.get(section_type)
        if section_class is None:
            raise KeyError(f"Section type '{section_type}' not registered")
        
        # Instantiate without calling __init__ yet to inject manager context
        section = section_class.__new__(section_class)
        section._owner = self
        section.__init__(user_name=user_name, **section_params)
        
        return self.add(section)

    def resolve_material(self, material_input: Union[int, str, Material, None]) -> Optional[Material]:
        """Resolve a material using the manager's MeshMaker context."""
        from femora.core.material_base import Material as MaterialClass
        if material_input is None:
            return None
        if isinstance(material_input, MaterialClass):
            return material_input
        return self._mesh_maker.material.get(material_input)

    def _reassign_tags(self) -> None:
        """Retag all managed sections from ``_start_tag`` in tag order."""
        self._tagging.reassign_tags(self._sections, self._start_tag)

    def __len__(self) -> int:
        return len(self._sections)

    def __iter__(self):
        return iter(self._sections.values())

    @classmethod
    def register_section_type(cls, name: str, section_class: Type[Section]) -> None:
        """Register a concrete section type for manager-owned creation."""
        cls._section_types[name] = section_class

    @classmethod
    def get_section_types(cls) -> list[str]:
        """Return section types registered on the active manager factory map."""
        return list(cls._section_types.keys())
