from typing import Union

from femora.core.material_base import Material
from femora.core.section_base import Section


class PlateFiberSection(Section):
    """Nonlinear shell section backed by a plane-stress nD material.

    This section type represents a shell section whose response is integrated
    from a single nD material. It is used to model nonlinear behavior in plate
    and shell structures where the material response is defined in terms of
    plane-stress invariants.

    Tcl form:
        ``section PlateFiber <tag> <matTag>``

    Note:
        - The material must be an `nDMaterial` compatible with plane-stress
          behavior.
        - This section is typically used when the nonlinear material behavior is
          the primary focus of the shell model.

    Tip:
        - For concrete shell modeling, use this with a nonlinear concrete
          material (like `Concrete01` wrapped as an nD material if supported, or
          a dedicated nD concrete model).

    Example:
        ```python
        import femora as fm

        model = fm.MeshMaker()
        # Create an nD material for the section
        mat = model.material.nd.elastic_isotropic(user_name="ConcreteND", E=3600.0, nu=0.2)

        # Create the plate fiber section
        sec = model.section.shell.plate_fiber(
            user_name="ShellNonlinear",
            material=mat
        )
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": False,
        "members": ["__init__", "to_tcl", "get_materials"],
    }

    def __init__(self, user_name: str = "Unnamed", *, material: Union[int, str, Material]):
        """Create a PlateFiberSection with a validated nD material.

        Args:
            user_name: Unique identifier for the section.
            material: nD material reference (object, tag, or name).

        Raises:
            ValueError: If the material cannot be resolved, or if it is not
                recognized as an nDMaterial.
        """
        resolved_material = self.resolve_material(material)
        if resolved_material is None:
            raise ValueError(f"Material not found: {material}")
            
        if hasattr(resolved_material, "material_type") and resolved_material.material_type != "nDMaterial":
            raise ValueError("PlateFiberSection requires an nDMaterial for plane stress behavior")

        super().__init__("section", "PlateFiber", user_name)
        self.material = resolved_material

    def to_tcl(self) -> str:
        """Render the section as an OpenSees Tcl command.

        Returns:
            The Tcl command string.
        """
        return f"section PlateFiber {self._require_tag()} {self.material.tag}; # {self.user_name}"

    def get_materials(self) -> list[Material]:
        """Return the material used by this section.

        Returns:
            A list containing the single nD Material object.
        """
        return [self.material]
