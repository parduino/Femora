from femora.core.material_base import Material
from femora.core.section_base import Section


class Isolator2SpringSection(Section):
    """Horizontal isolator section modeled by two springs in series.

    This section type represents a specialized model for seismic isolation
    bearings. It consists of two springs (one elastic, one elastic-plastic)
    acting in series, and it accounts for the coupling between horizontal and
    vertical loads, including the reduction in horizontal stiffness due to
    axial buckling.

    Tcl form:
        ``section Isolator2spring <tag> <tol> <k1> <Fy> <k2> <kv> <hb> <Pe> <Po>``

    Note:
        - `k1`, `Fy`, and `k2` define the bilinear horizontal response.
        - `kv` is the vertical stiffness of the bearing.
        - `hb` is the total height of the elastomeric or friction bearing.
        - `Pe` is the Euler buckling load, and `Po` is the static axial load
          used to compute the initial P-Delta effect.
        - The algorithm iterates to find the horizontal force that balances the
          spring series; `tol` is the convergence tolerance.

    Tip:
        - Use this section when modeling lead-rubber bearings (LRB) or high-
          damping rubber bearings where P-Delta effects and buckling are
          significant concerns.

    Example:
        ```python
        import femora as fm

        model = fm.Model()
        # Create a two-spring isolator section for a seismic isolation study
        sec = model.section.special.isolator2spring(
            user_name="Isolator_Unit1",
            tol=1e-6,
            k1=10.0,
            Fy=1.0,
            k2=1.5,
            kv=1000.0,
            hb=12.0,
            Pe=500.0,
            Po=50.0
        )
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": False,
        "members": ["__init__", "to_tcl", "get_materials"],
    }

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
        """Create an Isolator2SpringSection with validated parameters.

        Args:
            user_name: User-specified name for the section.
            tol: Tolerance.
            k1: Initial horizontal stiffness.
            Fy: Yield force.
            k2: Post-yield horizontal stiffness.
            kv: Vertical stiffness.
            hb: Bearing height.
            Pe: Buckling load.
            Po: Axial load.

        Raises:
            ValueError: If parameters are not numeric, if dimensions/stiffnesses
                are non-positive, or if loads are negative.
        """
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
        """Render the section as an OpenSees Tcl command.

        Returns:
            Tcl command string.
        """
        return (
            f"section Isolator2spring {self._require_tag()} {self.tol} {self.k1} {self.Fy} {self.k2} "
            f"{self.kv} {self.hb} {self.Pe} {self.Po}; # {self.user_name}"
        )

    def get_materials(self) -> list[Material]:
        """Return materials used by this section.

        Returns:
            An empty list as this section does not use Material objects.
        """
        return []
