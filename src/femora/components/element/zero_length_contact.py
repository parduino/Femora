from typing import Dict, List, Union, Optional
from femora.core.material_base import Material
from femora.core.element_base import Element

class ZeroLengthContactASDimplex(Element):
    """OpenSees ZeroLengthContactASDimplex Element.

    This element is used to model contact between two nodes. It supports
    normal and tangential stiffness, and friction.
    """

    def __init__(self, ndof: int, Kn: float, Kt: float, mu: float, material: Material = None, orient: List[float] = None, intType: int = 0, **kwargs):
        """
        Args:
            ndof (int): Number of degrees of freedom per node.
            Kn (float): Penalty stiffness for normal contact.
            Kt (float): Penalty stiffness for tangential contact.
            mu (float): Friction coefficient using Mohr-Coulomb friction.
            material (Material, optional): Not used by this element, but required by base class signature.
                Defaults to None.
            orient (List[float], optional): Orientation vector [nx, ny, nz].
            intType (int, optional): Integration type (0: Implicit, 1: IMPL-EX). Defaults to 0.

        Raises:
            ValueError: If parameters are invalid.

        OpenSees command syntax:
             ``element zeroLengthContactASDimplex $tag $n1 $n2 $Kn $Kt $mu [-orient $nx $ny $nz] [-intType $type]``

        Example:
            ```python
            element = ZeroLengthContactASDimplex(ndof=3, Kn=1e8, Kt=1e8, mu=0.5)
            ```
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
        
        # Store optional path
        if orient is not None:
             # Validate orient
            if not isinstance(orient, (list, tuple)) or len(orient) != 3:
                raise ValueError("orient must be a list/tuple of 3 floats")
            self.orient = [float(x) for x in orient]
        else:
            self.orient = None

        super().__init__('ZeroLengthContactASDimplex', ndof, material=None, **kwargs)

    def to_tcl(self, tag: int, nodes: List[int]) -> str:
        """Generate the OpenSees TCL command for this element.

        Args:
            tag: Unique element tag.
            nodes: List of 2 node tags.

        Returns:
            str: TCL command string.
        """
        if len(nodes) != 2:
            raise ValueError("ZeroLengthContactASDimplex element requires 2 nodes")
        
        cmd = f"element zeroLengthContactASDimplex {tag} {nodes[0]} {nodes[1]} {self.Kn} {self.Kt} {self.mu}"
        
        if self.orient is not None:
            cmd += f" -orient {self.orient[0]} {self.orient[1]} {self.orient[2]}"
            
        if self.intType != 0:
            cmd += f" -intType {self.intType}"
            
        return cmd

