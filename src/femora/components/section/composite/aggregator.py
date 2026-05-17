from typing import Dict, Optional, Union

from femora.core.material_base import Material
from femora.core.section_base import Section


class AggregatorSection(Section):
    """Aggregate multiple uniaxial materials under section response codes."""

    def __init__(
        self,
        user_name: str = "Unnamed",
        *,
        materials: Optional[Dict[str, Union[int, str, Material]]] = None,
        base_section: Optional[Union[int, str, "Section"]] = None,
    ):
        valid_codes = {"P", "Mz", "My", "Vy", "Vz", "T"}
        resolved_materials: Dict[str, Material] = {}
        if materials:
            invalid = [code for code in materials if code not in valid_codes]
            if invalid:
                raise ValueError(f"Invalid response code(s): {invalid}. Must be one of: {sorted(valid_codes)}")
            
            for key, val in materials.items():
                resolved_materials[key] = Section.resolve_material_reference(val)

        resolved_base_section = None
        if base_section is not None:
            if isinstance(base_section, Section):
                resolved_base_section = base_section
            else:
                from femora.components.MeshMaker import MeshMaker
                resolved_base_section = MeshMaker.get_instance().section.get(base_section)

        super().__init__("section", "Aggregator", user_name)
        self.materials = resolved_materials
        self.base_section = resolved_base_section
        self.material = next(iter(self.materials.values())) if self.materials else None

    def add_material(self, material_input: Union[int, str, Material], response_code: str) -> None:
        valid_codes = {"P", "Mz", "My", "Vy", "Vz", "T"}
        if response_code not in valid_codes:
            raise ValueError(f"Invalid response code. Must be one of: {sorted(valid_codes)}")
        material = self.resolve_material(material_input)
        self.materials[response_code] = material
        if self.material is None:
            self.material = material

    def to_tcl(self) -> str:
        mat_pairs: list[str] = []
        for code, material in self.materials.items():
            mat_pairs.extend([str(material.tag), code])
        tcl_cmd = f"section Aggregator {self._require_tag()} " + " ".join(mat_pairs)
        if self.base_section:
            tcl_cmd += f" -section {self.base_section.tag}"
        return f"{tcl_cmd}; # {self.user_name}"

    def get_materials(self) -> list[Material]:
        materials = list(self.materials.values())
        if self.base_section:
            materials.extend(self.base_section.get_materials())
        return materials
