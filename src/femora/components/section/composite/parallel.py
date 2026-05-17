from typing import List, Optional, Union

from femora.core.material_base import Material
from femora.core.section_base import Section


class ParallelSection(Section):
    """Combine multiple sections in parallel."""

    def __init__(self, user_name: str = "Unnamed", *, sections: Optional[List[Union[int, str, "Section"]]] = None):
        resolved_sections: list[Section] = []
        if sections:
            for section_input in sections:
                if isinstance(section_input, Section):
                    resolved_sections.append(section_input)
                else:
                    from femora.components.MeshMaker import MeshMaker
                    resolved_sections.append(MeshMaker.get_instance().section.get(section_input))
        
        super().__init__("section", "Parallel", user_name)
        self.sections = resolved_sections
        all_materials = self.get_materials()
        self.material = all_materials[0] if all_materials else None

    def add_section(self, section_input: Union[int, str, "Section"]) -> None:
        resolved_section = self.resolve_section(section_input)
        self.sections.append(resolved_section)
        if self.material is None:
            section_materials = resolved_section.get_materials()
            if section_materials:
                self.material = section_materials[0]

    def to_tcl(self) -> str:
        section_tags = " ".join(str(sec.tag) for sec in self.sections)
        return f"section Parallel {self._require_tag()} {section_tags}; # {self.user_name}"

    def get_materials(self) -> list[Material]:
        materials: list[Material] = []
        for section in self.sections:
            for material in section.get_materials():
                if material not in materials:
                    materials.append(material)
        return materials
