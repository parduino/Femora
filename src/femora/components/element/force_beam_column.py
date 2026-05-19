from typing import Dict, List, Union
from femora.core.section_base import Section
from femora.core.transformation_base import GeometricTransformation
from femora.core.element_base import Element

class ForceBeamColumnElement(Element):
    """
    Force-Based Beam-Column Element for OpenSees (nonlinearBeamColumn).
    Uses force-based formulation with distributed plasticity.
    """
    
    def __init__(self, ndof: int, section: Union[Section, int, str], 
                 transformation: Union[GeometricTransformation, int, str], 
                 numIntgrPts: int = 5, 
                 massDens: float = 0.0,
                 maxIters: int = 10,
                 tol: float = 1e-12,
                 **kwargs):
        """
        Args:
            ndof (int): Number of degrees of freedom (3 for 2D, 6 for 3D).
            section (Union[Section, int, str]): Section object, tag, or name.
            transformation (Union[GeometricTransformation, int, str]): 
                Transformation object, tag, or name.
            numIntgrPts (int, optional): Number of integration points along the element. 
                Defaults to 5.
            massDens (float, optional): Element mass density per unit length. 
                Defaults to 0.0.
            maxIters (int, optional): Maximum number of iterations for element compatibility. 
                Defaults to 10.
            tol (float, optional): Tolerance for satisfaction of element compatibility. 
                Defaults to 1e-12.

        Raises:
            ValueError: If parameters are invalid.

        OpenSees command syntax:
            ``element nonlinearBeamColumn $tag $iNode $jNode $numIntgrPts $secTag $transfTag <-mass $massDens> <-iter $maxIters $tol>``

        Example:
            ```python
            element = ForceBeamColumnElement(ndof=3, section=1, transformation=1, numIntgrPts=5, maxIters=10, tol=1e-12)
            ```
        """
        # Validate DOF requirement (typically 6 for 3D, 3 for 2D)
        if ndof not in [3, 6]:
            raise ValueError(f"ForceBasedBeamColumnElement requires 3 (2D) or 6 (3D) DOFs, but got {ndof}")
        
        # Resolve section - REQUIRED for beam elements
        if section is None:
            raise ValueError("ForceBasedBeamColumnElement requires a section")
        self._section = self._resolve_section(section)
        
        # Resolve transformation - REQUIRED for beam elements  
        if transformation is None:
            raise ValueError("ForceBasedBeamColumnElement requires a geometric transformation")
        self._transformation = self._resolve_transformation(transformation)
        
        # Validate parameters
        self.numIntgrPts = int(numIntgrPts)
        if self.numIntgrPts < 1:
            raise ValueError("Number of integration points must be positive")
        
        self.massDens = float(massDens)
        if self.massDens < 0:
            raise ValueError("Mass density must be non-negative")
        
        self.maxIters = int(maxIters)
        if self.maxIters < 1:
            raise ValueError("Max iterations must be positive")
        
        self.tol = float(tol)
        if self.tol <= 0:
            raise ValueError("Tolerance must be positive")
            
        # Material should be None for beam elements (they use sections)
        super().__init__('nonlinearBeamColumn', ndof, material=None, 
                         section=self._section, transformation=self._transformation, **kwargs)

    @staticmethod
    def _resolve_section(section_input: Union[Section, int, str]) -> Section:
        """Resolve section from different input types"""
        if isinstance(section_input, Section):
            return section_input
        raise ValueError(f"Cannot resolve section '{section_input}' in unmanaged element creation. Pass a managed Section object directly or use model.element.beam.force(...)")

    @staticmethod
    def _resolve_transformation(transf_input: Union[GeometricTransformation, int, str]) -> GeometricTransformation:
        """Resolve transformation from different input types"""
        if isinstance(transf_input, GeometricTransformation):
            if transf_input.tag is None:
                raise ValueError("Transformation must be managed before assigning it to an element")
            return transf_input
        raise ValueError(f"Cannot resolve transformation '{transf_input}' in unmanaged element creation. Pass a managed GeometricTransformation object directly or use model.element.beam.force(...)")

    def __str__(self):
        """Generate the OpenSees element string representation"""
        return f"{self._section.tag} {self._transformation.tag} {self.numIntgrPts} {self.massDens} {self.maxIters} {self.tol}"
    
    def to_tcl(self, tag: int, nodes: List[int]) -> str:
        """
        Generate the OpenSees TCL command
        
        Example: element nonlinearBeamColumn $tag $iNode $jNode $numIntgrPts $secTag $transfTag <-mass $massDens> <-iter $maxIters $tol>
        """
        if len(nodes) != 2:
            raise ValueError("Force-based beam-column element requires 2 nodes")
        
        nodes_str = " ".join(str(node) for node in nodes)
        
        # Required parameters
        cmd_parts = [f"element nonlinearBeamColumn {tag} {nodes_str}"]
        
        # Add number of integration points
        cmd_parts.append(str(self.numIntgrPts))
            
        # Add section and transformation tags
        cmd_parts.extend([str(self._section.tag), str(self._transformation.tag)])
        
        # Add optional mass density
        if self.massDens != 0.0:
            cmd_parts.extend(["-mass", str(self.massDens)])
            
        # Add iteration parameters (always outputting to be safe given explicit defaults)
        cmd_parts.extend(["-iter", str(self.maxIters), str(self.tol)])
        
        return " ".join(cmd_parts)

    def get_mass_per_length(self) -> float:
        """Retrieve mass density per unit length if defined"""
        return self.massDens


