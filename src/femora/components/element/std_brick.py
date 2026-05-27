from typing import List

from femora.core.element_base import Element
from femora.core.material_base import Material


class stdBrickElement(Element):
    """Standard 8-node hexahedral continuum element for 3D solids.

    This element models 3D continuum response with 3 translational DOFs per
    node. It requires an assigned 3D ``nDMaterial`` and connects eight nodes in
    the order expected by OpenSees ``stdBrick``.

    Tcl form:
        ``element stdBrick <tag> <n1> ... <n8> <matTag> [<b1> <b2> <b3>] [-lumped]``

    Note:
        - Body forces ``b1``, ``b2``, and ``b3`` are constant in the global
          coordinate directions and are omitted from the Tcl command when zero.
        - When ``lumped`` is ``True``, the exported command includes the
          ``-lumped`` flag for lumped mass matrix formation.

    Attributes:
        b1: Constant body force in the global x-direction.
        b2: Constant body force in the global y-direction.
        b3: Constant body force in the global z-direction.
        lumped: Whether to request a lumped mass matrix in OpenSees.

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        mat = model.material.nd.elastic_isotropic(
            user_name="Soil",
            E=5.0e6,
            nu=0.3,
            rho=2000.0,
        )
        ele = model.element.brick.std(
            ndof=3,
            material=mat,
            b3=-9.81,
            lumped=True,
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
        lumped: bool = False,
        **kwargs,
    ):
        """Create a stdBrickElement with validated material and body-force inputs.

        Args:
            ndof: Number of DOFs per node. Must be 3 for this element.
            material: Managed 3D ``nDMaterial`` assigned to the brick.
            b1: Constant body force in the global x-direction.
            b2: Constant body force in the global y-direction.
            b3: Constant body force in the global z-direction.
            lumped: When ``True``, export the ``-lumped`` mass-matrix flag.
            **kwargs: Additional element parameters stored on the base element.

        Raises:
            ValueError: If the material is incompatible, if ``ndof`` is not 3,
                or if any provided parameter is invalid.
        """
        if not self._is_material_compatible(material):
            raise ValueError(
                f"Material {material.user_name} with type {material.material_type} "
                "is not compatible with stdBrickElement"
            )

        if ndof != 3:
            raise ValueError(f"stdBrickElement requires 3 DOFs, but got {ndof}")

        self.b1 = float(b1)
        self.b2 = float(b2)
        self.b3 = float(b3)
        self.lumped = bool(lumped)

        super().__init__("stdBrick", ndof, material, **kwargs)

    def to_tcl(self, tag: int, nodes: List[int]) -> str:
        """Render the element as an OpenSees Tcl command.

        Args:
            tag: Assigned element tag.
            nodes: Eight node tags in OpenSees ``stdBrick`` order.

        Returns:
            str: Tcl ``element stdBrick`` command for this element.

        Raises:
            ValueError: If ``nodes`` does not contain exactly eight node tags.
        """
        if len(nodes) != 8:
            raise ValueError("stdBrick element requires 8 nodes")

        nodes_str = " ".join(str(node) for node in nodes)
        elestr = f"element stdBrick {tag} {nodes_str} {self._material.tag}"

        if self.b3 != 0.0:
            elestr += f" {self.b1} {self.b2} {self.b3}"
        elif self.b2 != 0.0:
            elestr += f" {self.b1} {self.b2}"
        elif self.b1 != 0.0:
            elestr += f" {self.b1}"

        if self.lumped:
            elestr += " -lumped"

        return elestr

    @classmethod
    def _is_material_compatible(cls, material: Material) -> bool:
        """Check whether the material is compatible with ``stdBrick``.

        Args:
            material: Material instance to validate.

        Returns:
            bool: ``True`` when ``material.material_type == 'nDMaterial'``.
        """
        return material.material_type == "nDMaterial"
