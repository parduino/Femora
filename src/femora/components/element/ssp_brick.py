from typing import Dict, List, Union, Optional
from femora.core.material_base import Material
from femora.core.element_base import Element

class SSPbrickElement(Element):
    """OpenSees 8-node stabilized single-point integration brick (SSPbrick).

    The SSPbrick element is an eight-node hexahedral 3D continuum element that
    uses a physically stabilized single-point integration scheme ("Stabilized
    Single Point"). The stabilization employs an enhanced assumed strain field
    to eliminate both volumetric and shear locking, improving coarse mesh
    accuracy for bending-dominated and nearly-incompressible problems while
    typically providing faster analysis times than full integration elements.
    """
    def __init__(self, ndof: int, material: Material, b1: float = 0.0, b2: float = 0.0, b3: float = 0.0, **kwargs):
        """
        Args:
            ndof (int): Number of degrees of freedom per node. Must be 3.
            material (Material): Associated OpenSees material. Must have
                material_type == 'nDMaterial' (3D material).
            b1 (float, optional): Constant body force in global x-direction. 
                Defaults to 0.0.
            b2 (float, optional): Constant body force in global y-direction. 
                Defaults to 0.0.
            b3 (float, optional): Constant body force in global z-direction. 
                Defaults to 0.0.

        Raises:
            ValueError: If the material is incompatible, ndof != 3, or any
                provided parameter is invalid.

        OpenSees command syntax:
            ``element SSPbrick $tag $n1 $n2 $n3 $n4 $n5 $n6 $n7 $n8 $matTag [$b1 $b2 $b3]``

        Note:
            1. Body forces are constant in the global coordinate directions and
               default to 0.0 when omitted.
            2. Recorder queries (e.g. ``stress``, ``strain``) correspond to those of
               the assigned ``nDMaterial`` and are evaluated at the single
               integration point located at the element center.
            3. Designed to duplicate functionality of ``stdBrick``; report any
               discrepancies to developers.
            
            Reference:
                SSPbrick Element documentation – https://opensees.berkeley.edu/wiki/index.php/SSPbrick_Element

        Example:
            ```python
            element = SSPbrickElement(ndof=3, material=my_material, b3=-9.81)
            ```
        """
        if not self._is_material_compatible(material):
            raise ValueError(
                f"Material {material.user_name} with type {material.material_type} is not compatible with SSPbrickElement"
            )
        if ndof != 3:
            raise ValueError(f"SSPbrickElement requires 3 DOFs, but got {ndof}")
        
        # Store parameters
        self.b1 = float(b1)
        self.b2 = float(b2)
        self.b3 = float(b3)
        
        super().__init__('SSPbrick', ndof, material, **kwargs)

    def to_tcl(self, tag: int, nodes: List[int]) -> str:
        """Generate the OpenSees TCL command for this SSPbrick element.

        Args:
            tag: Unique element tag.
            nodes: List of 8 node tags.

        Returns:
            str: TCL command of the form:
                ``element SSPbrick <tag> <n1> ... <n8> <matTag> [b1] [b2] [b3]``

        Raises:
            ValueError: If ``nodes`` does not contain exactly 8 node IDs.
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
        """Check whether the provided material can be used with SSPbrick.

        Requires an OpenSees 3D ``nDMaterial``.

        Args:
            material: Material instance to check.

        Returns:
            bool: ``True`` if ``material.material_type == 'nDMaterial'``.
        """
        return material.material_type == 'nDMaterial'

