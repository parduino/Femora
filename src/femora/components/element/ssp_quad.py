from typing import Dict, List, Union, Optional
from femora.core.material_base import Material
from femora.core.element_base import Element

class SSPQuadElement(Element):
    """OpenSees 4-node stabilized single-point integration quadrilateral (SSPquad).

    This element represents a 2D continuum element that can operate in
    PlaneStrain or PlaneStress. It requires materials of type ``nDMaterial``
    and exactly 2 DOFs per node.
    """
    def __init__(self, ndof: int, material: Material, Type: str, Thickness: float, b1: float = 0.0, b2: float = 0.0, **kwargs):
        """
        Args:
            ndof (int): Number of degrees of freedom per node. Must be 2.
            material (Material): Associated OpenSees material. Must have
                material_type == 'nDMaterial'.
            Type (str): Either 'PlaneStrain' or 'PlaneStress'. Required.
            Thickness (float): Element thickness (out-of-plane). Required.
            b1 (float, optional): Constant body force in global x-direction. 
                Defaults to 0.0.
            b2 (float, optional): Constant body force in global y-direction. 
                Defaults to 0.0.

        Raises:
            ValueError: If the material is incompatible, ndof != 2, or any
                parameter is missing/invalid.

        OpenSees command syntax:
            ``element SSPquad $tag $n1 $n2 $n3 $n4 $matTag $Type $Thickness [$b1 $b2]``

        Example:
            ```python
            element = SSPQuadElement(ndof=2, material=mat, Type='PlaneStrain', Thickness=1.0)
            ```
        """
        # Validate material compatibility
        if not self._is_material_compatible(material):
            raise ValueError(f"Material {material.user_name} with type {material.material_type} is not compatible with SSPQuadElement")
        
        # Validate DOF requirement
        if ndof != 2:
            raise ValueError(f"SSPQuadElement requires 2 DOFs, but got {ndof}")
        
        # Validate and store parameters
        if Type not in ['PlaneStrain', 'PlaneStress']:
            raise ValueError("Element type must be either 'PlaneStrain' or 'PlaneStress'")
        self.Type = Type
        
        self.Thickness = float(Thickness)
        self.b1 = float(b1)
        self.b2 = float(b2)
            
        super().__init__('SSPQuad', ndof, material, **kwargs)

    def __str__(self):
        """Return a compact string with material tag and parameters.
        
        Returns:
            str: String representation.
        """
        params_str = f"{self.Type} {self.Thickness}"
        if self.b2 != 0.0:
            params_str += f" {self.b1} {self.b2}"
        elif self.b1 != 0.0:
            params_str += f" {self.b1}"
            
        return f"{self._material.tag} {params_str}"
    
    def to_tcl(self, tag: int, nodes: List[int]) -> str:
        """Generate the OpenSees TCL command for this SSPquad element.
        
        Args:
            tag: Unique element tag.
            nodes: List of 4 node tags in counter-clockwise order.
        
        Returns:
            str: A TCL command of the form:
                 ``element SSPquad <tag> <n1> <n2> <n3> <n4> <matTag> <Type> <Thickness> [b1] [b2]``
        
        Raises:
            ValueError: If ``nodes`` does not contain exactly 4 node IDs.
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
        """Check whether the provided material can be used with SSPQuad.
        
        SSPQuad requires an OpenSees ``nDMaterial``.
        
        Args:
            material: Material instance to check.
        
        Returns:
            bool: ``True`` if ``material.material_type == 'nDMaterial'``.
        """
        return material.material_type == 'nDMaterial'

