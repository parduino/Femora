"""Reinforced-concrete fiber section."""

from __future__ import annotations

from typing import List, Union

from femora.core.material_base import Material
from femora.core.section_base import Section


class RCSection(Section):
    """Reinforced concrete section with separate core, cover, and steel materials."""

    def __init__(
        self,
        user_name: str = "Unnamed",
        *,
        core_material: Union[int, str, Material],
        cover_material: Union[int, str, Material],
        steel_material: Union[int, str, Material],
        d: float,
        b: float,
        cover_to_center_of_bar: float,
    ) -> None:
        resolved_core_material = Section.resolve_material_reference(core_material)
        if resolved_core_material is None:
            raise ValueError("RCSection requires a valid core_material")

        resolved_cover_material = Section.resolve_material_reference(cover_material)
        if resolved_cover_material is None:
            raise ValueError("RCSection requires a valid cover_material")

        resolved_steel_material = Section.resolve_material_reference(steel_material)
        if resolved_steel_material is None:
            raise ValueError("RCSection requires a valid steel_material")

        try:
            d = float(d)
            b = float(b)
            cover_to_center_of_bar = float(cover_to_center_of_bar)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "RCSection dimensions must be numeric values",
            ) from exc

        if d <= 0:
            raise ValueError("RCSection requires d > 0")
        if b <= 0:
            raise ValueError("RCSection requires b > 0")
        if cover_to_center_of_bar <= 0:
            raise ValueError("RCSection requires cover_to_center_of_bar > 0")

        super().__init__("section", "RC", user_name)
        self.core_material = resolved_core_material
        self.cover_material = resolved_cover_material
        self.steel_material = resolved_steel_material
        self.d = d
        self.b = b
        self.cover_to_center_of_bar = cover_to_center_of_bar
        self.material = self.core_material

    def to_tcl(self) -> str:
        """Generate the OpenSees Tcl command for the section."""
        return (
            f"section RC {self._require_tag()} {self.core_material.tag} "
            f"{self.cover_material.tag} {self.steel_material.tag} {self.d} {self.b} "
            f"{self.cover_to_center_of_bar}; # {self.user_name}"
        )

    def get_materials(self) -> List[Material]:
        """Return all unique materials used by the section."""
        materials: List[Material] = []
        for material in (
            self.core_material,
            self.cover_material,
            self.steel_material,
        ):
            if material is not None and material not in materials:
                materials.append(material)
        return materials
