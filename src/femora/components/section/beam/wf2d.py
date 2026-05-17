from typing import Union

from femora.core.material_base import Material
from femora.core.section_base import Section


class WFSection2d(Section):
    """Wide-flange section for 2D fiber-style beam modeling."""

    def __init__(
        self,
        user_name: str = "Unnamed",
        *,
        material: Union[int, str, Material],
        d: float,
        tw: float,
        bf: float,
        tf: float,
        Nflweb: int,
        Nflflange: int,
    ):
        resolved_material = Section.resolve_material_reference(material)
        if resolved_material is None:
            raise ValueError(f"Material not found: {material}")

        try:
            d = float(d)
            tw = float(tw)
            bf = float(bf)
            tf = float(tf)
            Nflweb = int(Nflweb)
            Nflflange = int(Nflflange)
        except (TypeError, ValueError) as exc:
            raise ValueError("WFSection2d parameters must be numeric") from exc
        if min(d, tw, bf, tf) <= 0:
            raise ValueError("d, tw, bf, and tf must be positive")
        if Nflweb <= 0 or Nflflange <= 0:
            raise ValueError("Nflweb and Nflflange must be positive integers")

        super().__init__("section", "WFSection2d", user_name)
        self.material = resolved_material
        self.d = d
        self.tw = tw
        self.bf = bf
        self.tf = tf
        self.Nflweb = Nflweb
        self.Nflflange = Nflflange

    def to_tcl(self) -> str:
        return (
            f"section WFSection2d {self._require_tag()} "
            f"{self.d} {self.tw} {self.bf} {self.tf} {self.Nflweb} {self.Nflflange} {self.material.tag}; # {self.user_name}"
        )

    def get_materials(self) -> list[Material]:
        return [self.material]
