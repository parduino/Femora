from femora.core.material_base import Material
from femora.core.section_base import Section


class BidirectionalSection(Section):
    """Coupled bidirectional plasticity section for specialized components.

    This section type represents a material with a coupled bidirectional
    force-deformation relationship. It is typically used to model components
    with a circular yield surface, where plasticity in two orthogonal directions
    is dependent on the total resultant force (e.g., specialized isolation
    bearings or friction devices).

    Tcl form:
        ``section Bidirectional <tag> <E> <Fy> <Hiso> <Hkin>``

    Note:
        - The section uses an explicit integration algorithm in OpenSees for the
          plastic flow.
        - `Hiso` and `Hkin` define the isotropic and kinematic hardening
          moduli, respectively.
        - This section only resists forces in two local directions.

    Tip:
        - Use this section for modeling structural components where circular
          interaction between local axes is critical for capturing energy
          dissipation.

    Example:
        ```python
        import femora as fm

        model = fm.Model()
        # Create a bidirectional plasticity section for an isolator model
        sec = model.section.special.bidirectional(
            user_name="IsolatorShear",
            E=100.0,
            Fy=1.0,
            Hiso=0.0,
            Hkin=0.02
        )
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": False,
        "members": ["__init__", "to_tcl", "get_materials"],
    }

    def __init__(self, user_name: str = "Unnamed", *, E: float, Fy: float, Hiso: float, Hkin: float):
        """Create a BidirectionalSection with validated parameters.

        Args:
            user_name: User-specified name for the section.
            E: Elastic modulus.
            Fy: Yield force.
            Hiso: Isotropic hardening modulus.
            Hkin: Kinematic hardening modulus.

        Raises:
            ValueError: If parameters are not numeric, if E or Fy are non-positive,
                or if hardening moduli are negative.
        """
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
        """Render the section as an OpenSees Tcl command.

        Returns:
            Tcl command string.
        """
        return f"section Bidirectional {self._require_tag()} {self.E} {self.Fy} {self.Hiso} {self.Hkin}; # {self.user_name}"

    def get_materials(self) -> list[Material]:
        """Return materials used by this section.

        Returns:
            An empty list as this section does not use Material objects.
        """
        return []
