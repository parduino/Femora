from typing import Union

from femora.core.material_base import Material
from femora.core.section_base import Section


class PlateFiberSection(Section):
    """Plate fiber section backed by one plane-stress nD material."""

    def __init__(self, user_name: str = "Unnamed", *, material: Union[int, str, Material]):
        resolved_material = Section.resolve_material_reference(material)
        if resolved_material is None:
            raise ValueError(f"Material not found: {material}")
            
        if hasattr(resolved_material, "material_type") and resolved_material.material_type != "nDMaterial":
            raise ValueError("PlateFiberSection requires an nDMaterial for plane stress behavior")

        super().__init__("section", "PlateFiber", user_name)
        self.material = resolved_material

    def to_tcl(self) -> str:
        return f"section PlateFiber {self._require_tag()} {self.material.tag}; # {self.user_name}"

    def get_materials(self) -> list[Material]:
        return [self.material]
