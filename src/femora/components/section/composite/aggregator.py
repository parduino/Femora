from typing import Dict, Optional, Union

from femora.core.material_base import Material
from femora.core.section_base import Section


class AggregatorSection(Section):
    """Section composed of multiple materials and optionally a base section.

    The Aggregator is a powerful section type that allows you to combine
    independent uniaxial responses into a single section, or to add missing
    response degrees of freedom to an existing section.

    Tcl form:
        ``section Aggregator <tag> <matTag1> <code1> ... [-section <secTag>]``

    Note:
        - Each material provided is mapped to a specific section degree of
          freedom (e.g., 'Mz', 'T').
        - If `base_section` is provided, the materials in the aggregator are
          added to the response of that section. This is frequently used to add
          linear torsional stiffness ('T') to a fiber section that only handles
          flexure and axial force.
        - The aggregator assumes the responses are uncoupled.

    Tip:
        - Use the `add_material` method to build an aggregator incrementally if
          the materials are not all known at initialization.

    Example:
        ```python
        import femora as fm

        model = fm.MeshMaker()
        # Create a fiber section for flexure
        fiber_sec = model.section.fiber.section(user_name="BendingOnly")
        # (add patches/fibers to fiber_sec here)

        # Create a linear torsional material
        torsion_mat = model.material.uniaxial.elastic(user_name="TorMat", E=11200.0)

        # Use Aggregator to add torsion to the fiber section
        full_sec = model.section.composite.aggregator(
            user_name="FullSection",
            materials={"T": torsion_mat},
            base_section=fiber_sec
        )
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": False,
        "members": ["__init__", "add_material", "to_tcl", "get_materials"],
    }

    def __init__(
        self,
        user_name: str = "Unnamed",
        *,
        materials: Optional[Dict[str, Union[int, str, Material]]] = None,
        base_section: Optional[Union[int, str, "Section"]] = None,
    ):
        """Create an AggregatorSection with validated materials and response codes.

        Args:
            user_name: User-specified name for the section.
            materials: Optional dictionary mapping section response codes (e.g., 'P', 'Mz')
                to uniaxial materials (object, tag, or name).
            base_section: Optional base section to be augmented (object, tag, or name).

        Raises:
            ValueError: If response codes are invalid or materials/sections
                cannot be resolved.
        """
        valid_codes = {"P", "Mz", "My", "Vy", "Vz", "T"}
        resolved_materials: Dict[str, Material] = {}
        if materials:
            invalid = [code for code in materials if code not in valid_codes]
            if invalid:
                raise ValueError(f"Invalid response code(s): {invalid}. Must be one of: {sorted(valid_codes)}")
            
            for key, val in materials.items():
                resolved_materials[key] = Section.resolve_material_reference(val)

        resolved_base_section = None
        if base_section is not None:
            if isinstance(base_section, Section):
                resolved_base_section = base_section
            else:
                from femora.components.MeshMaker import MeshMaker
                resolved_base_section = MeshMaker.get_instance().section.get(base_section)

        super().__init__("section", "Aggregator", user_name)
        self.materials = resolved_materials
        self.base_section = resolved_base_section
        self.material = next(iter(self.materials.values())) if self.materials else None

    def add_material(self, material_input: Union[int, str, Material], response_code: str) -> None:
        """Add a uniaxial material response to the aggregator.

        Args:
            material_input: Uniaxial material reference (object, tag, or name).
            response_code: Section response code. Must be one of:
                'P', 'Mz', 'My', 'Vy', 'Vz', 'T'.

        Raises:
            ValueError: If the response code is invalid or the material cannot be resolved.
        """
        valid_codes = {"P", "Mz", "My", "Vy", "Vz", "T"}
        if response_code not in valid_codes:
            raise ValueError(f"Invalid response code. Must be one of: {sorted(valid_codes)}")
        material = self.resolve_material(material_input)
        self.materials[response_code] = material
        if self.material is None:
            self.material = material

    def to_tcl(self) -> str:
        """Render the section as an OpenSees Tcl command.

        Returns:
            Tcl command string.
        """
        mat_pairs: list[str] = []
        for code, material in self.materials.items():
            mat_pairs.extend([str(material.tag), code])
        tcl_cmd = f"section Aggregator {self._require_tag()} " + " ".join(mat_pairs)
        if self.base_section:
            tcl_cmd += f" -section {self.base_section.tag}"
        return f"{tcl_cmd}; # {self.user_name}"

    def get_materials(self) -> list[Material]:
        """Return all materials used by this section and its base section.

        Returns:
            List of unique Material objects.
        """
        materials = list(self.materials.values())
        if self.base_section:
            materials.extend(self.base_section.get_materials())
        return materials
