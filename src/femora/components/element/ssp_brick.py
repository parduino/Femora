from typing import List

from femora.core.element_base import Element
from femora.core.material_base import Material


class SSPbrickElement(Element):
    """Stabilized single-point 8-node brick element for 3D continua.

    This element uses physically stabilized single-point integration with an
    enhanced assumed strain field to reduce volumetric and shear locking. It is
    often more efficient than full-integration bricks on coarse meshes while
    improving bending-dominated response.

    Tcl form:
        ``element SSPbrick <tag> <n1> ... <n8> <matTag> [<b1> <b2> <b3>]``

    Note:
        - Requires a 3D ``nDMaterial`` and exactly 3 DOFs per node.
        - Body forces are constant in global coordinates and omitted from the
          Tcl command when zero.
        - Recorder quantities such as stress and strain follow the assigned
          material and are evaluated at the element center integration point.

    Attributes:
        b1: Constant body force in the global x-direction.
        b2: Constant body force in the global y-direction.
        b3: Constant body force in the global z-direction.

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        mat = model.material.nd.elastic_isotropic(
            user_name="Rock",
            E=1.0e7,
            nu=0.25,
            rho=2500.0,
        )
        ele = model.element.brick.ssp(
            ndof=3,
            material=mat,
            b3=-9.81,
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
        b1: float = 0.0,
        b2: float = 0.0,
        b3: float = 0.0,
        **kwargs,
    ):
        """Create an SSPbrickElement with validated material and body-force inputs.

        Args:
            ndof: Number of DOFs per node. Must be 3 for this element.
            material: Managed 3D ``nDMaterial`` assigned to the brick.
            b1: Constant body force in the global x-direction.
            b2: Constant body force in the global y-direction.
            b3: Constant body force in the global z-direction.
            **kwargs: Additional element parameters stored on the base element.

        Raises:
            ValueError: If the material is incompatible, if ``ndof`` is not 3,
                or if any provided parameter is invalid.
        """
        if not self._is_material_compatible(material):
            raise ValueError(
                f"Material {material.user_name} with type {material.material_type} "
                "is not compatible with SSPbrickElement"
            )
        if ndof != 3:
            raise ValueError(f"SSPbrickElement requires 3 DOFs, but got {ndof}")

        self.b1 = float(b1)
        self.b2 = float(b2)
        self.b3 = float(b3)

        super().__init__("SSPbrick", ndof, material, **kwargs)

    def to_tcl(self, tag: int, nodes: List[int]) -> str:
        """Render the element as an OpenSees Tcl command.

        Args:
            tag: Assigned element tag.
            nodes: Eight node tags in OpenSees ``SSPbrick`` order.

        Returns:
            str: Tcl ``element SSPbrick`` command for this element.

        Raises:
            ValueError: If ``nodes`` does not contain exactly eight node tags.
        """
        if len(nodes) != 8:
            raise ValueError("SSPbrick element requires 8 nodes")

        nodes_str = " ".join(str(node) for node in nodes)
        cmd = f"element SSPbrick {tag} {nodes_str} {self._material.tag}"

        if self.b3 != 0.0:
            cmd += f" {self.b1} {self.b2} {self.b3}"
        elif self.b2 != 0.0:
            cmd += f" {self.b1} {self.b2}"
        elif self.b1 != 0.0:
            cmd += f" {self.b1}"

        return cmd

    @classmethod
    def _is_material_compatible(cls, material: Material) -> bool:
        """Check whether the material is compatible with ``SSPbrick``.

        Args:
            material: Material instance to validate.

        Returns:
            bool: ``True`` when ``material.material_type == 'nDMaterial'``.
        """
        return material.material_type == "nDMaterial"
