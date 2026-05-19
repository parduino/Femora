from typing import Dict, List, Union
from femora.core.section_base import Section
from femora.core.transformation_base import GeometricTransformation
from femora.core.element_base import Element

class DispBeamColumnElement(Element):
    """
    Displacement-Based Beam-Column Element for OpenSees.
    Uses distributed plasticity with displacement-based formulation.
    """

    def __init__(self, ndof: int, section: Union[Section, int, str],      
                 transformation: Union[GeometricTransformation, int, str],
                 numIntgrPts: int = 5,
                 massDens: float = 0.0,
                 **kwargs):
        if ndof not in [3, 6]:
            raise ValueError(f"DisplacementBasedBeamColumnElement requires 3 (2D) or 6 (3D) DOFs, but got {ndof}")

        # Resolve section - REQUIRED for beam elements
        if section is None:
            raise ValueError("DisplacementBasedBeamColumnElement requires a section")
        self._section = self._resolve_section(section)

        # Resolve transformation - REQUIRED for beam elements
        if transformation is None:
            raise ValueError("DisplacementBasedBeamColumnElement requires a geometric transformation")
        self._transformation = self._resolve_transformation(transformation)

        # Validate parameters
        self.numIntgrPts = int(numIntgrPts)
        if self.numIntgrPts < 1:
            raise ValueError("Number of integration points must be positive")
        
        self.massDens = float(massDens)
        if self.massDens < 0:
            raise ValueError("Mass density must be non-negative")

        # Material should be None for beam elements (they use sections)   
        super().__init__('dispBeamColumn', ndof, material=None,
                         section=self._section, transformation=self._transformation, **kwargs)

    @staticmethod
    def _resolve_section(section_input: Union[Section, int, str]) -> Section:
        """Resolve section from different input types"""
        if isinstance(section_input, Section):
            return section_input
        raise ValueError(f"Cannot resolve section '{section_input}' in unmanaged element creation. Pass a managed Section object directly or use model.element.beam.disp(...)")

    @staticmethod
    def _resolve_transformation(transf_input: Union[GeometricTransformation, int, str]) -> GeometricTransformation:
        """Resolve transformation from different input types"""
        if isinstance(transf_input, GeometricTransformation):
            if transf_input.tag is None:
                raise ValueError("Transformation must be managed before assigning it to an element")
            return transf_input
        raise ValueError(f"Cannot resolve transformation '{transf_input}' in unmanaged element creation. Pass a managed GeometricTransformation object directly or use model.element.beam.disp(...)")

    def __str__(self):
        """Generate the OpenSees element string representation"""
        return f"{self._section.tag} {self._transformation.tag} {self.numIntgrPts} {self.massDens}"

    def to_tcl(self, tag: int, nodes: List[int]) -> str:
        """
        Generate the OpenSees TCL command

        Example: element dispBeamColumn $tag $iNode $jNode $numIntgrPts $secTag $transfTag <-mass $massDens>
        """
        if len(nodes) != 2:
            raise ValueError("Displacement-based beam-column element requires 2 nodes")

        nodes_str = " ".join(str(node) for node in nodes)

        # Required parameters
        cmd_parts = [f"element dispBeamColumn {tag} {nodes_str}"]

        # Add number of integration points
        cmd_parts.append(str(self.numIntgrPts))

        # Add section and transformation tags
        cmd_parts.extend([str(self._section.tag), str(self._transformation.tag)])

        # Add optional mass density
        if self.massDens != 0.0:
            cmd_parts.extend(["-mass", str(self.massDens)])

        return " ".join(cmd_parts)

    def get_mass_per_length(self) -> float:
        """Retrieve mass density per unit length if defined"""
        return self.massDens


