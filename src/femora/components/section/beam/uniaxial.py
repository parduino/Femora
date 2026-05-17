from typing import Union

from femora.core.material_base import Material
from femora.core.section_base import Section


class UniaxialSection(Section):
    """Section backed by one uniaxial material response."""

    def __init__(
        self,
        user_name: str = "Unnamed",
        *,
        material: Union[int, str, Material],
        response_code: str = "P",
    ):
        valid_codes = {"P", "Mz", "My", "Vy", "Vz", "T"}
        if response_code not in valid_codes:
            raise ValueError(f"Response code must be one of: {sorted(valid_codes)}")
        
        resolved_material = Section.resolve_material_reference(material)
        if resolved_material is None:
             raise ValueError(f"Material not found: {material}")

        super().__init__("section", "Uniaxial", user_name)
        self.material = resolved_material
        self.response_code = response_code

    def to_tcl(self) -> str:
        return f"section Uniaxial {self._require_tag()} {self.material.tag} {self.response_code}; # {self.user_name}"

    def get_materials(self) -> list[Material]:
        return [self.material]
