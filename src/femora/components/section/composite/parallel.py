from typing import List, Optional, Union

from femora.core.material_base import Material
from femora.core.section_base import Section


class ParallelSection(Section):
    """Section composed of multiple sections acting in parallel.

    The Parallel section sums the forces and stiffnesses of its constituent
    sections at each integration point. It is ideal for modeling composite
    structural members or adding supplemental energy dissipation.

    Tcl form:
        ``section Parallel <tag> <secTag1> <secTag2> ...``

    Note:
        - The constituent sections are assumed to share the same kinematic state
          (strains).
        - Use the `add_section` method to add components to a parallel section
          after creation.

    Tip:
        - This is often used to model "base + augmentation" behavior where you
          want to keep the original member properties but add an additional
          layer of stiffness or damping.

    Example:
        ```python
        import femora as fm

        model = fm.Model()
        # Create two different sections
        sec1 = model.section.beam.elastic(user_name="Primary", E=29000.0, A=10.0, Iz=100.0)
        sec2 = model.section.beam.elastic(user_name="Secondary", E=29000.0, A=2.0, Iz=20.0)

        # Combine them in parallel
        combined = model.section.composite.parallel(
            user_name="CompositeMember",
            sections=[sec1, sec2]
        )
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": False,
        "members": ["__init__", "add_section", "to_tcl", "get_materials"],
    }

    def __init__(self, user_name: str = "Unnamed", *, sections: Optional[List[Union[int, str, "Section"]]] = None):
        """Create a ParallelSection with validated constituent sections.

        Args:
            user_name: User-specified name for the section.
            sections: Optional list of constituent sections (objects, tags, or names).

        Raises:
            ValueError: If constituent sections cannot be resolved.
        """
        resolved_sections: list[Section] = []
        if sections:
            for section_input in sections:
                resolved_sections.append(self.resolve_section(section_input))
        
        super().__init__("section", "Parallel", user_name)
        self.sections = resolved_sections
        all_materials = self.get_materials()
        self.material = all_materials[0] if all_materials else None

    def add_section(self, section_input: Union[int, str, "Section"]) -> None:
        """Add a constituent section to the parallel combination.

        Args:
            section_input: Section reference (object, tag, or name).

        Raises:
            ValueError: If the section cannot be resolved.
        """
        resolved_section = self.resolve_section(section_input)
        self.sections.append(resolved_section)
        if self.material is None:
            section_materials = resolved_section.get_materials()
            if section_materials:
                self.material = section_materials[0]

    def to_tcl(self) -> str:
        """Render the section as an OpenSees Tcl command.

        Returns:
            Tcl command string.
        """
        section_tags = " ".join(str(sec.tag) for sec in self.sections)
        return f"section Parallel {self._require_tag()} {section_tags}; # {self.user_name}"

    def get_materials(self) -> list[Material]:
        """Return all unique materials used by all constituent sections.

        Returns:
            List of unique Material objects.
        """
        materials: list[Material] = []
        for section in self.sections:
            for material in section.get_materials():
                if material not in materials:
                    materials.append(material)
        return materials
