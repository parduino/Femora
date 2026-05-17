from femora.core.material_base import Material
from femora.core.section_base import Section


class Isolator2SpringSection(Section):
    """Built-in two-spring isolator section."""

    def __init__(
        self,
        user_name: str = "Unnamed",
        *,
        tol: float,
        k1: float,
        Fy: float,
        k2: float,
        kv: float,
        hb: float,
        Pe: float,
        Po: float,
    ):
        try:
            tol = float(tol)
            k1 = float(k1)
            Fy = float(Fy)
            k2 = float(k2)
            kv = float(kv)
            hb = float(hb)
            Pe = float(Pe)
            Po = float(Po)
        except (TypeError, ValueError) as exc:
            raise ValueError("Isolator2SpringSection parameters must be numeric") from exc
        if tol <= 0:
            raise ValueError("tol must be positive")
        if min(k1, k2, kv, Fy, hb) <= 0:
            raise ValueError("k1, Fy, k2, kv, and hb must be positive")
        if Pe < 0 or Po < 0:
            raise ValueError("Pe and Po must be non-negative")

        super().__init__("section", "Isolator2spring", user_name)
        self.tol = tol
        self.k1 = k1
        self.Fy = Fy
        self.k2 = k2
        self.kv = kv
        self.hb = hb
        self.Pe = Pe
        self.Po = Po
        self.material = None

    def to_tcl(self) -> str:
        return (
            f"section Isolator2spring {self._require_tag()} {self.tol} {self.k1} {self.Fy} {self.k2} "
            f"{self.kv} {self.hb} {self.Pe} {self.Po}; # {self.user_name}"
        )

    def get_materials(self) -> list[Material]:
        return []
