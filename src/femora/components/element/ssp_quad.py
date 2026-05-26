from typing import List

from femora.core.element_base import Element
from femora.core.material_base import Material


class SSPQuadElement(Element):
    """Stabilized single-point quadrilateral continuum element for 2D models.

    This four-node element represents plane-strain or plane-stress continua with
    2 translational DOFs per node. It requires a 2D ``nDMaterial`` and an
    explicit out-of-plane thickness.

    Tcl form:
        ``element SSPquad <tag> <n1> <n2> <n3> <n4> <matTag> <Type> <Thickness> [<b1> <b2>]``

    Note:
        - ``Type`` must be either ``PlaneStrain`` or ``PlaneStress``.
        - Nodes should be ordered counter-clockwise in the element plane.
        - Body forces are constant in global coordinates and omitted when zero.

    Attributes:
        Type: Plane-stress or plane-strain formulation flag.
        Thickness: Out-of-plane thickness used by the element formulation.
        b1: Constant body force in the global x-direction.
        b2: Constant body force in the global y-direction.

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        mat = model.material.nd.elastic_isotropic(
            user_name="Soil2D",
            E=3.0e7,
            nu=0.3,
            rho=1900.0,
        )
        ele = model.element.quad.ssp(
            ndof=2,
            material=mat,
            Type="PlaneStrain",
            Thickness=1.0,
        )
        print(ele.tag)
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

    def __init__(
        self,
        ndof: int,
        material: Material,
        Type: str,
        Thickness: float,
        b1: float = 0.0,
        b2: float = 0.0,
        **kwargs,
    ):
        """Create an SSPQuadElement with validated material and geometry inputs.

        Args:
            ndof: Number of DOFs per node. Must be 2 for this element.
            material: Managed 2D ``nDMaterial`` assigned to the quadrilateral.
            Type: ``PlaneStrain`` or ``PlaneStress`` formulation flag.
            Thickness: Element thickness in the out-of-plane direction.
            b1: Constant body force in the global x-direction.
            b2: Constant body force in the global y-direction.
            **kwargs: Additional element parameters stored on the base element.

        Raises:
            ValueError: If the material is incompatible, if ``ndof`` is not 2,
                or if any parameter is missing or invalid.
        """
        if not self._is_material_compatible(material):
            raise ValueError(
                f"Material {material.user_name} with type {material.material_type} "
                "is not compatible with SSPQuadElement"
            )

        if ndof != 2:
            raise ValueError(f"SSPQuadElement requires 2 DOFs, but got {ndof}")

        if Type not in ["PlaneStrain", "PlaneStress"]:
            raise ValueError("Element type must be either 'PlaneStrain' or 'PlaneStress'")
        self.Type = Type

        self.Thickness = float(Thickness)
        self.b1 = float(b1)
        self.b2 = float(b2)

        super().__init__("SSPQuad", ndof, material, **kwargs)

    def __str__(self):
        """Return a compact parameter summary for debugging.

        Returns:
            str: Material tag followed by element parameters.
        """
        params_str = f"{self.Type} {self.Thickness}"
        if self.b2 != 0.0:
            params_str += f" {self.b1} {self.b2}"
        elif self.b1 != 0.0:
            params_str += f" {self.b1}"

        return f"{self._material.tag} {params_str}"

    def to_tcl(self, tag: int, nodes: List[int]) -> str:
        """Render the element as an OpenSees Tcl command.

        Args:
            tag: Assigned element tag.
            nodes: Four node tags in counter-clockwise order.

        Returns:
            str: Tcl ``element SSPquad`` command for this element.

        Raises:
            ValueError: If ``nodes`` does not contain exactly four node tags.
        """
        if len(nodes) != 4:
            raise ValueError("SSPQuad element requires 4 nodes")

        nodes_str = " ".join(str(node) for node in nodes)
        tag = str(tag)

        cmd = f"element SSPquad {tag} {nodes_str} {self._material.tag} {self.Type} {self.Thickness}"

        if self.b2 != 0.0:
            cmd += f" {self.b1} {self.b2}"
        elif self.b1 != 0.0:
            cmd += f" {self.b1}"

        return cmd

    @classmethod
    def _is_material_compatible(cls, material: Material) -> bool:
        """Check whether the material is compatible with ``SSPquad``.

        Args:
            material: Material instance to validate.

        Returns:
            bool: ``True`` when ``material.material_type == 'nDMaterial'``.
        """
        return material.material_type == "nDMaterial"
