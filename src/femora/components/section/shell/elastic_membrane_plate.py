from femora.core.material_base import Material
from femora.core.section_base import Section


class ElasticMembranePlateSection(Section):
    """Linear elastic section for shell and plate elements.

    This section type represents a homogeneous elastic material that resists
    both membrane (in-plane) and plate (out-of-plane bending) actions. It is
    parameterized by material moduli and the section thickness.

    Tcl form:
        ``section ElasticMembranePlateSection <tag> <E> <nu> <h> <rho>``

    Note:
        - This section is ideal for modeling elastic slabs, diaphragms, and
          shear walls where nonlinear behavior is not expected.
        - `rho` is the mass density per unit volume.

    Tip:
        - Use this section with `ShellMITC4` or `ShellDKGQ` elements for
          structural analysis of 2D surfaces.

    Example:
        ```python
        from femora.core.model import Model
        import femora.components.section.shell  # noqa: F401

        model = Model()
        sec = model.section.shell.elastic_membrane_plate(
            user_name="SlabSection",
            E=3600.0,
            nu=0.2,
            h=8.0,
            rho=0.00015,
        )
        print(sec.tag)
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

    def __init__(self, user_name: str = "Unnamed", *, E: float, nu: float, h: float, rho: float):
        """Create an ElasticMembranePlateSection with validated constants.

        Args:
            user_name: Unique identifier for the section.
            E: Young's modulus of the shell material.
            nu: Poisson's ratio.
            h: Thickness of the shell.
            rho: Mass density (mass per unit volume).

        Raises:
            ValueError: If any parameter is not numeric, if E or h are
                non-positive, if nu is not in [0, 0.5), or if rho is negative.
        """
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
        """Render the section as an OpenSees Tcl command.

        Returns:
            str: Tcl command string for this section.

        Raises:
            ValueError: If this section has not been added to a manager.
        """
        return f"section ElasticMembranePlateSection {self._require_tag()} {self.E} {self.nu} {self.h} {self.rho}; # {self.user_name}"

    def get_materials(self) -> list[Material]:
        """Return materials used by this section.

        Returns:
            An empty list as this section defines its own elastic properties.
        """
        return []
