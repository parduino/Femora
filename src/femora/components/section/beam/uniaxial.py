from typing import Union

from femora.core.material_base import Material
from femora.core.section_base import Section


class UniaxialSection(Section):
    """Section defined by a single uniaxial material response.

    This section type wraps a single uniaxial material and maps it to a specific
    section degree of freedom (e.g., axial force, bending moment). It is most
    commonly used as a component within an
    [AggregatorSection][femora.components.section.composite.aggregator.AggregatorSection]
    to build complex multi-DOF section models.

    Tcl form:
        ``section Uniaxial <tag> <matTag> <responseCode>``

    Note:
        - The `response_code` determines which internal force result the material
          provides (e.g., 'P' for axial, 'Mz' for strong-axis bending).
        - This section is essentially a pass-through to the underlying material
          tangent and stress.

    Tip:
        - If you need a section that only resists one type of force (like a
          purely axial brace), this is the most efficient section choice.
        - Combine multiple `UniaxialSection` instances using an `Aggregator` to
          create custom sections with uncoupled behaviors (e.g., nonlinear
          flexure with linear shear).

    Example:
        ```python
        import femora as fm

        model = fm.Model()
        # Create a material for the section
        mat = model.material.uniaxial.elastic(user_name="SteelMat", E=29000.0)

        # Create a uniaxial section for axial response ('P')
        sec = model.section.beam.uniaxial(
            user_name="AxialBrace",
            material=mat,
            response_code="P"
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
        response_code: str = "P",
    ):
        """Create a UniaxialSection with validated material and response code.

        Args:
            user_name: User-specified name for the section.
            material: Uniaxial material reference (object, tag, or name).
            response_code: Section response code. Must be one of:
                'P', 'Mz', 'My', 'Vy', 'Vz', 'T'.

        Raises:
            ValueError: If the response code is invalid or the material
                cannot be resolved.
        """
        valid_codes = {"P", "Mz", "My", "Vy", "Vz", "T"}
        if response_code not in valid_codes:
            raise ValueError(f"Response code must be one of: {sorted(valid_codes)}")
        
        resolved_material = self.resolve_material(material)
        if resolved_material is None:
             raise ValueError(f"Material not found: {material}")

        super().__init__("section", "Uniaxial", user_name)
        self.material = resolved_material
        self.response_code = response_code

    def to_tcl(self) -> str:
        """Render the section as an OpenSees Tcl command.

        Returns:
            Tcl command string.
        """
        return f"section Uniaxial {self._require_tag()} {self.material.tag} {self.response_code}; # {self.user_name}"

    def get_materials(self) -> list[Material]:
        """Return the material used by this section.

        Returns:
            List containing the single uniaxial material.
        """
        return [self.material]
