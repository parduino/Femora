from typing import Dict, List, Union, Optional
from femora.core.material_base import Material
from femora.core.element_base import Element

class stdBrickElement(Element):
    """OpenSees 8-node standard brick element (3D continuum).

    This element requires a 3D ``nDMaterial`` and exactly 3 DOFs per node.
    Optional body forces ``b1``, ``b2``, and ``b3`` may be supplied. A
    ``-lumped`` mass option can also be enabled via the boolean parameter
    ``lumped``.
    """
    def __init__(self, ndof: int, material: Material, b1: float = 0.0, b2: float = 0.0, b3: float = 0.0, lumped: bool = False, **kwargs):
        """
        Args:
            ndof (int): Number of degrees of freedom per node. Must be 3.
            material (Material): Associated OpenSees material. Must have
                material_type == 'nDMaterial'.
            b1 (float, optional): Constant body force in global x-direction. 
                Defaults to 0.0.
            b2 (float, optional): Constant body force in global y-direction. 
                Defaults to 0.0.
            b3 (float, optional): Constant body force in global z-direction. 
                Defaults to 0.0.
            lumped (bool, optional): If True, append the -lumped flag
                to use a lumped mass matrix. Defaults to False.

        Raises:
            ValueError: If the material is incompatible, ndof != 3, or any
                provided parameter is invalid.

        OpenSees command syntax:
            ``element stdBrick $tag $n1 $n2 $n3 $n4 $n5 $n6 $n7 $n8 $matTag [$b1 $b2 $b3] [-lumped]``

        Example:
            ```python
            element = stdBrickElement(ndof=3, material=mat, b3=-9.81, lumped=True)
            ```
        """
        # Validate material compatibility
        if not self._is_material_compatible(material):
            raise ValueError(f"Material {material.user_name} with type {material.material_type} is not compatible with stdBrickElement")
        
        # Validate DOF requirement
        if ndof != 3:
            raise ValueError(f"stdBrickElement requires 3 DOFs, but got {ndof}")
        
        # Store parameters
        self.b1 = float(b1)
        self.b2 = float(b2)
        self.b3 = float(b3)
        self.lumped = bool(lumped)
            
        super().__init__('stdBrick', ndof, material, **kwargs)
        
    def to_tcl(self, tag: int, nodes: List[int]) -> str:
        """Generate the OpenSees TCL command for this stdBrick element.
        
        Args:
            tag: Unique element tag.
            nodes: List of 8 node tags.
        
        Returns:
            str: A TCL command of the form:
                 ``element stdBrick <tag> <n1> ... <n8> <matTag> [b1] [b2] [b3]``
        
        Raises:
            ValueError: If ``nodes`` does not contain exactly 8 node IDs.
        """
        if len(nodes) != 8:
            raise ValueError("stdBrick element requires 8 nodes")

        # Build base command
        nodes_str = " ".join(str(node) for node in nodes)
        elestr = f"element stdBrick {tag} {nodes_str} {self._material.tag}"

        # Optional numeric body forces
        if self.b3 != 0.0:
             elestr += f" {self.b1} {self.b2} {self.b3}"
        elif self.b2 != 0.0:
             elestr += f" {self.b1} {self.b2}"
        elif self.b1 != 0.0:
             elestr += f" {self.b1}"

        # Optional '-lumped' flag
        if self.lumped:
            elestr += " -lumped"

        return elestr

    @classmethod
    def _is_material_compatible(cls, material: Material) -> bool:
        """Check whether the provided material can be used with stdBrick.
        
        stdBrick requires an OpenSees 3D ``nDMaterial``.
        
        Args:
            material: Material instance to check.
        
        Returns:
            bool: ``True`` if ``material.material_type == 'nDMaterial'``.
        """
        return material.material_type == 'nDMaterial'

