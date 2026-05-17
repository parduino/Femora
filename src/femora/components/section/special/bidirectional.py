from femora.core.material_base import Material
from femora.core.section_base import Section


class BidirectionalSection(Section):
    """Built-in bidirectional plasticity section."""

    def __init__(self, user_name: str = "Unnamed", *, E: float, Fy: float, Hiso: float, Hkin: float):
        try:
            E = float(E)
            Fy = float(Fy)
            Hiso = float(Hiso)
            Hkin = float(Hkin)
        except (TypeError, ValueError) as exc:
            raise ValueError("BidirectionalSection parameters must be numeric") from exc
        if E <= 0 or Fy <= 0:
            raise ValueError("E and Fy must be positive")
        if Hiso < 0 or Hkin < 0:
            raise ValueError("Hiso and Hkin must be non-negative")

        super().__init__("section", "Bidirectional", user_name)
        self.E = E
        self.Fy = Fy
        self.Hiso = Hiso
        self.Hkin = Hkin
        self.material = None

    def to_tcl(self) -> str:
        return f"section Bidirectional {self._require_tag()} {self.E} {self.Fy} {self.Hiso} {self.Hkin}; # {self.user_name}"

    def get_materials(self) -> list[Material]:
        return []
