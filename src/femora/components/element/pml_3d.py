from typing import Dict, List, Union, Optional
from femora.core.material_base import Material
from femora.core.element_base import Element

class PML3DElement(Element):
    """OpenSees 8-node Perfectly Matched Layer (PML) 3D element.

    This element augments the standard brick element with PML degrees of
    freedom (9 DOFs per node). It requires an isotropic elastic 3D
    ``nDMaterial`` (class name ``ElasticIsotropicMaterial``) and supports two
    mesh types (``box`` and ``general``) with associated parameters.
    """
    def __init__(self, ndof: int, material: Material, 
                 PML_Thickness: float, 
                 meshType: str, 
                 meshTypeParameters: Union[List[float], str],
                 gamma: float = 0.5, 
                 beta: float = 0.25, 
                 eta: float = 1.0/12.0, 
                 ksi: float = 1.0/48.0,
                 m: float = 2.0, 
                 R: float = 1.0e-8, 
                 Cp: Optional[float] = None,
                 alpha0: Optional[float] = None, 
                 beta0: Optional[float] = None,
                 **kwargs):
        """
        Args:
            ndof (int): Number of degrees of freedom per node. Must be 9.
            material (Material): Associated OpenSees material. Must be a 3D
                nDMaterial with class name ElasticIsotropicMaterial.
            PML_Thickness (float): Thickness of the PML layer. Required.
            meshType (str): 'box' or 'general' (case-insensitive). Required.
            meshTypeParameters (Union[List[float], str]): 6 values required.
            gamma (float, optional): Newmark gamma. Defaults to 0.5.
            beta (float, optional): Newmark beta. Defaults to 0.25.
            eta (float, optional): Newmark eta. Defaults to 1/12.
            ksi (float, optional): Newmark ksi. Defaults to 1/48.
            m (float, optional): PML m. Defaults to 2.0.
            R (float, optional): PML R. Defaults to 1e-8.
            Cp (float, optional): PML Cp.
            alpha0 (float, optional): PML alpha0.
            beta0 (float, optional): PML beta0.

        Raises:
            ValueError: If the material is incompatible, ndof != 9, or any
                parameter is missing/invalid.

        OpenSees command syntax:
            ``element PML $tag $n1 ... $n8 $matTag $thick "$meshType" $params "-Newmark" $g $b $e $x ...``

        Example:
            ```python
            element = PML3DElement(ndof=9, material=mat, PML_Thickness=1.0, meshType='box', meshTypeParameters=[1.0]*6)
            ```
        """
        # Validate material compatibility
        if not self._is_material_compatible(material):
            raise ValueError(f"Material {material.user_name} with type {material.material_type} is not compatible with PML3DElement")
        
        # Validate DOF requirement
        if ndof != 9:
            raise ValueError(f"PML3DElement requires 9 DOFs, but got {ndof}")
        
        # Validate and store parameters
        self.PML_Thickness = float(PML_Thickness)
        
        if meshType.lower() not in ["box", "general"]:    
            raise ValueError("meshType must be either 'box' or 'general'")
        self.meshType = meshType.lower()
        
        if isinstance(meshTypeParameters, str):
            values = [float(x.strip()) for x in meshTypeParameters.split(",")]
        else:
            values = [float(x) for x in meshTypeParameters]
        
        if len(values) < 6:
            raise ValueError("meshTypeParameters must contain at least 6 numeric values")
        self.meshTypeParameters = values[:6]
        
        self.gamma = float(gamma)
        self.beta = float(beta)
        self.eta = float(eta)
        self.ksi = float(ksi)
        self.m = float(m)
        self.R = float(R)
        self.Cp = float(Cp) if Cp is not None else None
        
        if (alpha0 is not None) != (beta0 is not None):
            raise ValueError("Both alpha0 and beta0 must be specified together")
        self.alpha0 = float(alpha0) if alpha0 is not None else None
        self.beta0 = float(beta0) if beta0 is not None else None
            
        super().__init__('PML3D', ndof, material, **kwargs)

    def to_tcl(self, tag: int, nodes: List[int]) -> str:
        """Generate the OpenSees TCL command for this PML element.

        The command follows OpenSees' ``element PML`` syntax with the Newmark
        parameters and either ``-alphabeta`` or ``-m -R [-Cp]`` depending on
        the provided parameters.
        
        Args:
            tag: Unique element tag.
            nodes: List of 8 node tags.
        
        Returns:
            str: A TCL command string for creating the PML element.
        
        Raises:
            ValueError: If ``nodes`` does not contain exactly 8 node IDn.
        """
        if len(nodes) != 8:
            raise ValueError("PML3D element requires 8 nodes")
        elestr = f"element PML {tag} "
        elestr += " ".join(str(node) for node in nodes)
        elestr += f" {self._material.tag} {self.PML_Thickness} \"{self.meshType}\" "
        elestr += " ".join(str(val) for val in self.meshTypeParameters)
        elestr += f" \"-Newmark\" {self.gamma} {self.beta} {self.eta} {self.ksi}"
        
        if self.alpha0 is not None and self.beta0 is not None:
            elestr += f" -alphabeta {self.alpha0} {self.beta0}"
        else:
            elestr += f" -m {self.m} -R {self.R}"
            if self.Cp is not None:
                elestr += f" -Cp {self.Cp}"
        return elestr

    @classmethod
    def _is_material_compatible(cls, material: Material) -> bool:
        """Check whether the provided material can be used with PML3D.
        
        Requires a 3D ``nDMaterial`` whose class name is
        ``ElasticIsotropicMaterial``.
        
        Args:
            material: Material instance to check.
        
        Returns:
            bool: ``True`` if the material satisfies the requirements.
        """
        check = (material.material_type == 'nDMaterial') and (material.__class__.__name__ == 'ElasticIsotropicMaterial')
        return check

