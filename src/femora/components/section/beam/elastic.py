from typing import Optional

from femora.core.material_base import Material
from femora.core.section_base import Section


class ElasticSection(Section):
    """Elastic OpenSees section with explicit geometric properties."""

    def __init__(
        self,
        user_name: str = "Unnamed",
        *,
        E: float,
        A: float,
        Iz: float,
        Iy: Optional[float] = None,
        G: Optional[float] = None,
        J: Optional[float] = None,
    ):
        try:
            E = float(E)
            A = float(A)
            Iz = float(Iz)
            Iy = None if Iy is None else float(Iy)
            G = None if G is None else float(G)
            J = None if J is None else float(J)
        except (TypeError, ValueError) as exc:
            raise ValueError("ElasticSection parameters must be numeric") from exc

        if E <= 0 or A <= 0 or Iz <= 0:
            raise ValueError("E, A, and Iz must be positive")
        if Iy is not None and Iy <= 0:
            raise ValueError("Iy must be positive when provided")
        if G is not None and G <= 0:
            raise ValueError("G must be positive when provided")
        if J is not None and J <= 0:
            raise ValueError("J must be positive when provided")

        super().__init__("section", "Elastic", user_name)
        self.E = E
        self.A = A
        self.Iz = Iz
        self.Iy = Iy
        self.G = G
        self.J = J
        self.material = None

    def to_tcl(self) -> str:
        values = [self.E, self.A, self.Iz]
        if self.Iy is not None:
            values.append(self.Iy)
        if self.G is not None:
            values.append(self.G)
        if self.J is not None:
            values.append(self.J)
        params_str = " ".join(str(value) for value in values)
        return f"section Elastic {self._require_tag()} {params_str}; # {self.user_name}"

    def get_materials(self) -> list[Material]:
        return []

    def get_area(self) -> float:
        return self.A

    def get_Iz(self) -> float:
        return self.Iz

    def get_Iy(self) -> float:
        return 0.0 if self.Iy is None else self.Iy

    def get_J(self) -> float:
        return 0.0 if self.J is None else self.J
