from typing import Dict, List, Union
from femora.core.section_base import Section
from femora.core.transformation_base import GeometricTransformation
from femora.core.element_base import Element

class ElasticBeamColumnElement(Element):
    """
    Elastic Beam-Column Element for OpenSees with Section.
    Uses elastic formulation with section properties.
    """
    
    def __init__(self, ndof: int, section: Union[Section, int, str], 
                 transformation: Union[GeometricTransformation, int, str], 
                 massDens: float = 0.0,
                 cMass: bool = False,
                 **kwargs):
        """
        Args:
            ndof (int): Number of degrees of freedom (3 for 2D, 6 for 3D).
            section (Union[Section, int, str]): Section object. Tag/name requires using manager factory.
            transformation (Union[GeometricTransformation, int, str]): 
                Transformation object. Tag/name requires using manager factory.
            massDens (float, optional): Element mass density per unit length. 
                Defaults to 0.0.
            cMass (bool, optional): Use consistent mass matrix instead of lumped. 
                Defaults to False.

        Raises:
            ValueError: If parameters are invalid.

        OpenSees command syntax:
            ``element elasticBeamColumn $tag $iNode $jNode $secTag $transfTag <-mass $massDens> <-cMass>``
        """
        # Validate DOF requirement (typically 6 for 3D, 3 for 2D)
        if ndof not in [3, 6]:
            raise ValueError(f"ElasticBeamColumnElement requires 3 (2D) or 6 (3D) DOFs, but got {ndof}")
        
        # Resolve section - REQUIRED for beam elements
        if section is None:
            raise ValueError("ElasticBeamColumnElement requires a section")
        self._section = self._resolve_section(section)
        
        # Resolve transformation - REQUIRED for beam elements  
        if transformation is None:
            raise ValueError("ElasticBeamColumnElement requires a geometric transformation")
        self._transformation = self._resolve_transformation(transformation)
        
        # Validate parameters
        self.massDens = float(massDens)
        if self.massDens < 0:
            raise ValueError("Mass density must be non-negative")
            
        self.cMass = bool(cMass)
            
        # Material should be None for beam elements (they use sections)
        super().__init__('elasticBeamColumn', ndof, material=None, 
                         section=self._section, transformation=self._transformation, **kwargs)

    @staticmethod
    def _resolve_section(section_input: Union[Section, int, str]) -> Section:
        """Resolve section from different input types"""
        if isinstance(section_input, Section):
            return section_input
        raise ValueError(f"Cannot resolve section '{section_input}' in unmanaged element creation. Pass a managed Section object directly or use model.element.beam.elastic(...)")

    @staticmethod
    def _resolve_transformation(transf_input: Union[GeometricTransformation, int, str]) -> GeometricTransformation:
        """Resolve transformation from different input types"""
        if isinstance(transf_input, GeometricTransformation):
            if transf_input.tag is None:
                raise ValueError("Transformation must be managed before assigning it to an element")
            return transf_input
        raise ValueError(f"Cannot resolve transformation '{transf_input}' in unmanaged element creation. Pass a managed GeometricTransformation object directly or use model.element.beam.elastic(...)")

    def __str__(self):
        """Generate the OpenSees element string representation"""
        return f"{self._section.tag} {self._transformation.tag} {self.massDens} {self.cMass}"
    
    def to_tcl(self, tag: int, nodes: List[int]) -> str:
        """
        Generate the OpenSees TCL command
        
        Example: element elasticBeamColumn $tag $iNode $jNode $secTag $transfTag <-mass $massDens> <-cMass>
        """
        if len(nodes) != 2:
            raise ValueError("Elastic beam-column element requires 2 nodes")
        
        nodes_str = " ".join(str(node) for node in nodes)
        
        # Required parameters
        cmd_parts = [f"element elasticBeamColumn {tag} {nodes_str}"]
        
        # Add section and transformation tags
        cmd_parts.extend([str(self._section.tag), str(self._transformation.tag)])
        
        # Add optional mass density
        if self.massDens != 0.0:
            cmd_parts.extend(["-mass", str(self.massDens)])
            
        # Add optional consistent mass flag
        if self.cMass:
            cmd_parts.append("-cMass")
            
        return " ".join(cmd_parts)

    def get_mass_per_length(self) -> float:
        return self.massDens

