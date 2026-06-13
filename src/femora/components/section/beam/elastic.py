# =============================================================================
# Femora: Fast Efficient Meta-modeling for OpenSees-based Resilience Analysis
# Copyright 2026 Amin Pakzad and Pedro Arduino
# Developed at the UW Geotechnical Lab
# SPDX-License-Identifier: Apache-2.0
# =============================================================================

from typing import Optional

from femora.core.material_base import Material
from femora.core.section_base import Section


class ElasticSection(Section):
    """Linear-elastic section defined by explicit geometric and material constants.

    This section represents a linear beam-column cross-section. Unlike most
    other Femora sections, it does not reference a `Material` object; instead,
    it takes material moduli (E, G) and geometric properties (A, I, J) directly
    as constructor arguments.

    Tcl form:
        - 2D: ``section Elastic <tag> <E> <A> <Iz>``
        - 3D: ``section Elastic <tag> <E> <A> <Iz> <Iy> <G> <J>``

    Note:
        - This section is strictly linear. For nonlinear behavior, use
          [FiberSection][femora.components.section.fiber.section.FiberSection] or
          [UniaxialSection][femora.components.section.beam.uniaxial.UniaxialSection].
        - When using this section in a 3D model, you must provide all six
          parameters (E, A, Iz, Iy, G, J). OpenSees usually expects either 3 or 6
          values for the Elastic section command.

    Tip:
        - Use this section for preliminary modeling or when physical section
          dimensions are unknown but aggregate properties (like equivalent
          stiffness) are available.

    Example:
        ```python
        from femora.core.model import Model
        import femora.components.section.beam  # noqa: F401

        model = Model()
        sec_2d = model.section.beam.elastic(
            user_name="Beam2D",
            E=29000.0,
            A=10.0,
            Iz=150.0,
        )
        sec_3d = model.section.beam.elastic(
            user_name="Column3D",
            E=29000.0,
            A=26.5,
            Iz=999.0,
            Iy=150.0,
            G=11200.0,
            J=2.5,
        )
        print(sec_3d.tag)
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__", "get_area", "get_Iy", "get_Iz", "get_J"],
    }

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
        """Create an ElasticSection with validated geometric properties.

        Args:
            user_name: User-specified name for the section.
            E: Young's modulus.
            A: Cross-sectional area.
            Iz: Second moment of area about the local z-axis.
            Iy: Optional second moment of area about the local y-axis (for 3D).
            G: Optional shear modulus (for 3D).
            J: Optional torsional constant (for 3D).

        Raises:
            ValueError: If parameters are not numeric or if essential values
                (E, A, Iz) are non-positive.
        """
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
        """Render the section as an OpenSees Tcl command.

        Returns:
            str: Tcl command string for this section.

        Raises:
            ValueError: If this section has not been added to a manager.
        """
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
        """Return materials used by this section.

        Returns:
            An empty list as ElasticSection does not use Material objects.
        """
        return []

    def get_area(self) -> float:
        """Return the cross-sectional area.

        Returns:
            Area value.
        """
        return self.A

    def get_Iz(self) -> float:
        """Return the second moment of area about the local z-axis.

        Returns:
            Iz value.
        """
        return self.Iz

    def get_Iy(self) -> float:
        """Return the second moment of area about the local y-axis.

        Returns:
            Iy value, or 0.0 if not defined.
        """
        return 0.0 if self.Iy is None else self.Iy

    def get_J(self) -> float:
        """Return the torsional constant.

        Returns:
            J value, or 0.0 if not defined.
        """
        return 0.0 if self.J is None else self.J
