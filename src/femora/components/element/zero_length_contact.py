# =============================================================================
# Femora: Fast Efficient Meta-modeling for OpenSees-based Resilience Analysis
# Copyright 2026 Amin Pakzad and Pedro Arduino
# Developed at the UW Geotechnical Lab
# SPDX-License-Identifier: Apache-2.0
# =============================================================================

from typing import List, Optional

from femora.core.element_base import Element
from femora.core.material_base import Material


class ZeroLengthContactASDimplex(Element):
    """Two-node zero-length contact element with normal and tangential penalty stiffness.

    This element models frictional contact between two coincident or nearly
    coincident nodes using normal stiffness ``Kn``, tangential stiffness ``Kt``,
    and a Mohr-Coulomb friction coefficient ``mu``.

    Tcl form:
        ``element zeroLengthContactASDimplex <tag> <n1> <n2> <Kn> <Kt> <mu> [-orient nx ny nz] [-intType type]``

    Note:
        - Requires exactly two nodes at export.
        - ``intType`` selects the contact integration scheme (``0`` implicit,
          ``1`` IMPL-EX).

    Attributes:
        Kn: Normal contact penalty stiffness.
        Kt: Tangential contact penalty stiffness.
        mu: Friction coefficient.
        orient: Optional contact orientation vector ``[nx, ny, nz]``.
        intType: Contact integration type (``0`` implicit, ``1`` IMPL-EX).

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        ele = model.element.special.zero_length_contact(
            ndof=3,
            Kn=1.0e8,
            Kt=1.0e8,
            mu=0.5,
            orient=[0.0, 0.0, 1.0],
            intType=1,
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
        Kn: float,
        Kt: float,
        mu: float,
        material: Material = None,
        orient: List[float] = None,
        intType: int = 0,
        **kwargs,
    ):
        """Create a ZeroLengthContactASDimplex element with validated contact inputs.

        Args:
            ndof: Number of DOFs per node in the surrounding model (2, 3, 4,
                or 6).
            Kn: Normal contact penalty stiffness. Must be positive.
            Kt: Tangential contact penalty stiffness. Must be positive.
            mu: Mohr-Coulomb friction coefficient. Must be non-negative.
            material: Unused placeholder accepted for base-class compatibility.
            orient: Optional contact orientation vector ``[nx, ny, nz]``.
            intType: Contact integration type (``0`` implicit, ``1`` IMPL-EX).
            **kwargs: Additional element parameters stored on the base element.

        Raises:
            ValueError: If ``ndof`` is unsupported or if contact parameters are
                invalid.
        """
        if ndof not in (2, 3, 4, 6):
            raise ValueError("ZeroLengthContactASDimplex requires 2, 3, 4, or 6 DOFs")

        self.Kn = float(Kn)
        if self.Kn <= 0.0:
            raise ValueError("Kn must be positive")

        self.Kt = float(Kt)
        if self.Kt <= 0.0:
            raise ValueError("Kt must be positive")

        self.mu = float(mu)
        if self.mu < 0.0:
            raise ValueError("mu must be non-negative")

        self.intType = int(intType)
        if self.intType not in [0, 1]:
            raise ValueError("intType must be 0 or 1")

        if orient is not None:
            if not isinstance(orient, (list, tuple)) or len(orient) != 3:
                raise ValueError("orient must be a list/tuple of 3 floats")
            self.orient = [float(x) for x in orient]
        else:
            self.orient = None

        super().__init__("ZeroLengthContactASDimplex", ndof, material=None, **kwargs)

    def to_tcl(self, tag: int, nodes: List[int]) -> str:
        """Render the element as an OpenSees Tcl command.

        Args:
            tag: Assigned element tag.
            nodes: Two node tags defining the contact pair.

        Returns:
            str: Tcl ``element zeroLengthContactASDimplex`` command for this element.

        Raises:
            ValueError: If ``nodes`` does not contain exactly two node tags.
        """
        if len(nodes) != 2:
            raise ValueError("ZeroLengthContactASDimplex element requires 2 nodes")

        cmd = (
            f"element zeroLengthContactASDimplex {tag} {nodes[0]} {nodes[1]} "
            f"{self.Kn} {self.Kt} {self.mu}"
        )

        if self.orient is not None:
            cmd += f" -orient {self.orient[0]} {self.orient[1]} {self.orient[2]}"

        if self.intType != 0:
            cmd += f" -intType {self.intType}"

        return cmd
