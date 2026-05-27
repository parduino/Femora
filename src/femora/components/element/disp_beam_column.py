from typing import List, Union

from femora.core.element_base import Element
from femora.core.section_base import Section
from femora.core.transformation_base import GeometricTransformation


class DispBeamColumnElement(Element):
    """Displacement-based beam-column element with distributed plasticity.

    This two-node element integrates section response along the member length
    using a displacement-based formulation. It is commonly used for nonlinear
    frame analysis with fiber or uniaxial sections in 2D (3 DOF/node) or 3D
    (6 DOF/node) models.

    Tcl form:
        ``element dispBeamColumn <tag> <iNode> <jNode> <numIntgrPts> <secTag> <transfTag> <-mass massDens>``

    Note:
        - Requires a managed section and geometric transformation with assigned
          tags before Tcl export.
        - ``numIntgrPts`` controls the number of Gauss points used along the
          member for section integration.

    Attributes:
        numIntgrPts: Number of integration points along the element length.
        massDens: Mass density per unit length for optional dynamic mass
            formation.

    Example:
        ```python
        from femora.core.model import Model
        import femora.components.section.beam  # noqa: F401

        model = Model()
        sec = model.section.beam.elastic(
            user_name="Beam",
            E=29000.0,
            A=15.0,
            Iz=300.0,
        )
        transf = model.transformation.transformation2d(transf_type="Linear")
        ele = model.element.beam.disp(
            ndof=3,
            section=sec,
            transformation=transf,
            numIntgrPts=5,
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
        numIntgrPts: int = 5,
        massDens: float = 0.0,
        **kwargs,
    ):
        """Create a DispBeamColumnElement with validated dependencies.

        Args:
            ndof: Number of DOFs per node. Must be 3 for 2D or 6 for 3D.
            section: Managed section object integrated along the member.
            transformation: Managed geometric transformation defining the local
                element axis.
            numIntgrPts: Number of Gauss integration points along the element.
            massDens: Optional mass per unit length for dynamic analyses.
            **kwargs: Additional element parameters stored on the base element.

        Raises:
            ValueError: If ``ndof`` is unsupported, if the section or
                transformation is missing, if integration-point or mass inputs
                are invalid, or if dependencies cannot be resolved.
        """
        if ndof not in [3, 6]:
            raise ValueError(f"DisplacementBasedBeamColumnElement requires 3 (2D) or 6 (3D) DOFs, but got {ndof}")

        if section is None:
            raise ValueError("DisplacementBasedBeamColumnElement requires a section")
        self._section = self._resolve_section(section)

        if transformation is None:
            raise ValueError("DisplacementBasedBeamColumnElement requires a geometric transformation")
        self._transformation = self._resolve_transformation(transformation)

        self.numIntgrPts = int(numIntgrPts)
        if self.numIntgrPts < 1:
            raise ValueError("Number of integration points must be positive")

        self.massDens = float(massDens)
        if self.massDens < 0:
            raise ValueError("Mass density must be non-negative")

        super().__init__(
            "dispBeamColumn",
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
            "Pass a managed Section object directly or use model.element.beam.disp(...)"
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
            "Pass a managed GeometricTransformation object directly or use model.element.beam.disp(...)"
        )

    def __str__(self):
        """Return a compact parameter summary for debugging."""
        return f"{self._section.tag} {self._transformation.tag} {self.numIntgrPts} {self.massDens}"

    def to_tcl(self, tag: int, nodes: List[int]) -> str:
        """Render the element as an OpenSees Tcl command.

        Args:
            tag: Assigned element tag.
            nodes: Two node tags ``[iNode, jNode]``.

        Returns:
            str: Tcl ``element dispBeamColumn`` command for this element.

        Raises:
            ValueError: If ``nodes`` does not contain exactly two node tags.
        """
        if len(nodes) != 2:
            raise ValueError("Displacement-based beam-column element requires 2 nodes")

        nodes_str = " ".join(str(node) for node in nodes)
        cmd_parts = [f"element dispBeamColumn {tag} {nodes_str}"]
        cmd_parts.append(str(self.numIntgrPts))
        cmd_parts.extend([str(self._section.tag), str(self._transformation.tag)])

        if self.massDens != 0.0:
            cmd_parts.extend(["-mass", str(self.massDens)])

        return " ".join(cmd_parts)

    def get_mass_per_length(self) -> float:
        """Return the mass density per unit length.

        Returns:
            Mass per unit length assigned to this element.
        """
        return self.massDens
