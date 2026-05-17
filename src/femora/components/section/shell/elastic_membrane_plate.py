from femora.core.material_base import Material
from femora.core.section_base import Section


class ElasticMembranePlateSection(Section):
    """Elastic membrane-plate section for shell elements."""

    def __init__(self, user_name: str = "Unnamed", *, E: float, nu: float, h: float, rho: float):
        try:
            E = float(E)
            nu = float(nu)
            h = float(h)
            rho = float(rho)
        except (TypeError, ValueError) as exc:
            raise ValueError("ElasticMembranePlateSection parameters must be numeric") from exc
        if E <= 0:
            raise ValueError("E must be positive")
        if not (0 <= nu < 0.5):
            raise ValueError("nu must be in range [0, 0.5)")
        if h <= 0:
            raise ValueError("h must be positive")
        if rho < 0:
            raise ValueError("rho must be non-negative")

        super().__init__("section", "ElasticMembranePlateSection", user_name)
        self.E = E
        self.nu = nu
        self.h = h
        self.rho = rho
        self.material = None

    def to_tcl(self) -> str:
        return f"section ElasticMembranePlateSection {self._require_tag()} {self.E} {self.nu} {self.h} {self.rho}; # {self.user_name}"

    def get_materials(self) -> list[Material]:
        return []
