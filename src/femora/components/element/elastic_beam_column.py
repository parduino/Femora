# =============================================================================
# Femora: Fast Efficient Meta-modeling for OpenSees-based Resilience Analysis
# Copyright 2026 Amin Pakzad and Pedro Arduino
# Developed at the UW Geotechnical Lab
# SPDX-License-Identifier: Apache-2.0
# =============================================================================

from typing import List, Union

from femora.core.element_base import Element
from femora.core.section_base import Section
from femora.core.transformation_base import GeometricTransformation


class ElasticBeamColumnElement(Element):
    """Linear elastic beam-column element for frame models.

    This two-node element uses aggregate section stiffness and a geometric
    transformation to represent linear elastic frame response. It supports 2D
    models with 3 DOFs per node and 3D models with 6 DOFs per node.

    Tcl form:
        ``element elasticBeamColumn <tag> <iNode> <jNode> <secTag> <transfTag> <-mass massDens> <-cMass>``

    Note:
        - Requires a managed [Section][femora.core.section_base.Section] and
          [GeometricTransformation][femora.core.transformation_base.GeometricTransformation]
          with assigned tags before Tcl export.
        - Stiffness comes from the section definition, not a direct material
          assignment on the element.

    Attributes:
        massDens: Mass density per unit length used for optional lumped or
            consistent mass matrix formation.
        cMass: When ``True``, request a consistent mass matrix instead of the
            default lumped formulation.

    Example:
        ```python
        from femora.core.model import Model
        import femora.components.section.beam  # noqa: F401

        model = Model()
        sec = model.section.beam.elastic(
            user_name="Column",
            E=29000.0,
            A=20.0,
            Iz=500.0,
            Iy=500.0,
            G=11200.0,
            J=10.0,
        )
        transf = model.transformation.transformation3d(
            transf_type="Linear",
            vecxz_x=0.0,
            vecxz_y=0.0,
            vecxz_z=1.0,
        )
        ele = model.element.beam.elastic(
            ndof=6,
            section=sec,
            transformation=transf,
        )
        print(ele.tag)
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__", "get_mass_per_length"],
    }

    def __init__(
        self,
        ndof: int,
        section: Union[Section, int, str],
        transformation: Union[GeometricTransformation, int, str],
        massDens: float = 0.0,
        cMass: bool = False,
        **kwargs,
    ):
        """Create an ElasticBeamColumnElement with validated dependencies.

        Args:
            ndof: Number of DOFs per node. Must be 3 for 2D or 6 for 3D.
            section: Managed section object defining axial and bending stiffness.
            transformation: Managed geometric transformation defining the local
                element axis.
            massDens: Optional mass per unit length for dynamic analyses.
            cMass: When ``True``, use a consistent mass matrix.
            **kwargs: Additional element parameters stored on the base element.

        Raises:
            ValueError: If ``ndof`` is unsupported, if the section or
                transformation is missing, if mass density is negative, or if
                dependencies cannot be resolved.
        """
        if ndof not in [3, 6]:
            raise ValueError(f"ElasticBeamColumnElement requires 3 (2D) or 6 (3D) DOFs, but got {ndof}")

        if section is None:
            raise ValueError("ElasticBeamColumnElement requires a section")
        self._section = self._resolve_section(section)

        if transformation is None:
            raise ValueError("ElasticBeamColumnElement requires a geometric transformation")
        self._transformation = self._resolve_transformation(transformation)

        self.massDens = float(massDens)
        if self.massDens < 0:
            raise ValueError("Mass density must be non-negative")

        self.cMass = bool(cMass)

        super().__init__(
            "elasticBeamColumn",
            ndof,
            material=None,
            section=self._section,
            transformation=self._transformation,
            **kwargs,
        )

    @staticmethod
    def _resolve_section(section_input: Union[Section, int, str]) -> Section:
        """Resolve a managed section object from a direct section reference.

        Args:
            section_input: Section object passed to the constructor.

        Returns:
            The resolved section instance.

        Raises:
            ValueError: If the input is not a managed section object.
        """
        if isinstance(section_input, Section):
            return section_input
        raise ValueError(
            f"Cannot resolve section '{section_input}' in unmanaged element creation. "
            "Pass a managed Section object directly or use model.element.beam.elastic(...)"
        )

    @staticmethod
    def _resolve_transformation(transf_input: Union[GeometricTransformation, int, str]) -> GeometricTransformation:
        """Resolve a managed geometric transformation from a direct reference.

        Args:
            transf_input: Transformation object passed to the constructor.

        Returns:
            The resolved transformation instance.

        Raises:
            ValueError: If the input is not a managed transformation object.
        """
        if isinstance(transf_input, GeometricTransformation):
            if transf_input.tag is None:
                raise ValueError("Transformation must be managed before assigning it to an element")
            return transf_input
        raise ValueError(
            f"Cannot resolve transformation '{transf_input}' in unmanaged element creation. "
            "Pass a managed GeometricTransformation object directly or use model.element.beam.elastic(...)"
        )

    def __str__(self):
        """Return a compact parameter summary for debugging."""
        return f"{self._section.tag} {self._transformation.tag} {self.massDens} {self.cMass}"

    def to_tcl(self, tag: int, nodes: List[int]) -> str:
        """Render the element as an OpenSees Tcl command.

        Args:
            tag: Assigned element tag.
            nodes: Two node tags ``[iNode, jNode]``.

        Returns:
            str: Tcl ``element elasticBeamColumn`` command for this element.

        Raises:
            ValueError: If ``nodes`` does not contain exactly two node tags.
        """
        if len(nodes) != 2:
            raise ValueError("Elastic beam-column element requires 2 nodes")

        nodes_str = " ".join(str(node) for node in nodes)
        cmd_parts = [f"element elasticBeamColumn {tag} {nodes_str}"]
        cmd_parts.extend([str(self._section.tag), str(self._transformation.tag)])

        if self.massDens != 0.0:
            cmd_parts.extend(["-mass", str(self.massDens)])

        if self.cMass:
            cmd_parts.append("-cMass")

        return " ".join(cmd_parts)

    def get_mass_per_length(self) -> float:
        """Return the mass density per unit length.

        Returns:
            Mass per unit length assigned to this element.
        """
        return self.massDens
