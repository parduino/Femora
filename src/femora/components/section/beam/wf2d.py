from typing import Union

from femora.core.material_base import Material
from femora.core.section_base import Section


class WFSection2d(Section):
    """Wide-flange section for internal 2D fiber discretization.

    This section type represents a standard wide-flange (I-shape) beam or column.
    It automates the discretization of the cross-section into a collection of
    internal fibers, making it much easier to define than a manual
    [FiberSection][femora.components.section.fiber.section.FiberSection].

    Tcl form:
        ``section WFSection2d <tag> <matTag> <d> <tw> <bf> <tf> <Nflweb> <Nflflange>``

    Note:
        - This section is strictly 2D. It only supports strong-axis bending and
          axial response.
        - The discretization creates longitudinal fibers. The number of fibers
          in the web (`Nflweb`) and flanges (`Nflflange`) determines the
          integration accuracy across the depth.

    Tip:
        - Use this section for steel frame modeling where nonlinear material
          behavior is required, but a full fiber-by-fiber definition is too
          verbose.
        - Convergence Tip: Usually 8-12 web fibers and 2-4 flange fibers are
          sufficient for standard structural steel convergence.

    Example:
        ```python
        import femora as fm

        model = fm.Model()
        # Create a nonlinear steel material
        mat = model.material.uniaxial.steel01(user_name="Steel", Fy=50.0, E=29000.0, b=0.01)

        # Create a W14X90-like 2D section
        sec = model.section.beam.wf2d(
            user_name="W14X90_Nonlinear",
            material=mat,
            d=14.0,
            tw=0.44,
            bf=14.5,
            tf=0.71,
            Nflweb=8,
            Nflflange=4
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
        material: Union[int, str, Material],
        d: float,
        tw: float,
        bf: float,
        tf: float,
        Nflweb: int,
        Nflflange: int,
    ):
        """Create a WFSection2d with validated dimensions and discretization.

        Args:
            user_name: Unique identifier for the section.
            material: Uniaxial material reference for the entire section.
            d: Total section depth.
            tw: Web thickness.
            bf: Flange width.
            tf: Flange thickness.
            Nflweb: Number of fibers along the web depth.
            Nflflange: Number of fibers along each flange width.

        Raises:
            ValueError: If the material cannot be resolved, or if any dimension
                is non-positive, or if fiber counts are not positive integers.
        """
        resolved_material = self.resolve_material(material)
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
        """Render the section as an OpenSees Tcl command.

        Returns:
            The Tcl command string.
        """
        return (
            f"section WFSection2d {self._require_tag()} "
            f"{self.d} {self.tw} {self.bf} {self.tf} {self.Nflweb} {self.Nflflange} {self.material.tag}; # {self.user_name}"
        )

    def get_materials(self) -> list[Material]:
        """Return the material used by this section.

        Returns:
            A list containing the single Material object.
        """
        return [self.material]
