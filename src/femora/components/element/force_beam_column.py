from typing import List, Union

from femora.core.element_base import Element
from femora.core.section_base import Section
from femora.core.transformation_base import GeometricTransformation


class ForceBeamColumnElement(Element):
    """Force-based nonlinear beam-column element with distributed plasticity.

    This two-node element uses OpenSees' ``nonlinearBeamColumn`` formulation to
    integrate section force-deformation response along the member. It supports
    2D models with 3 DOFs per node and 3D models with 6 DOFs per node.

    Tcl form:
        ``element nonlinearBeamColumn <tag> <iNode> <jNode> <numIntgrPts> <secTag> <transfTag> <-mass massDens> <-iter maxIters tol>``

    Note:
        - Requires a managed section and geometric transformation with assigned
          tags before Tcl export.
        - The ``-iter`` parameters control the internal compatibility iteration
          used by the force-based formulation.

    Attributes:
        numIntgrPts: Number of integration points along the element length.
        massDens: Mass density per unit length for optional dynamic mass
            formation.
        maxIters: Maximum compatibility iterations for the force-based solve.
        tol: Convergence tolerance for the compatibility iteration.

    Example:
        ```python
        from femora.core.model import Model
        import femora.components.section.beam  # noqa: F401

        model = Model()
        sec = model.section.beam.elastic(
            user_name="Frame",
            E=29000.0,
            A=18.0,
            Iz=400.0,
            Iy=400.0,
            G=11200.0,
            J=8.0,
        )
        transf = model.transformation.transformation3d(
            transf_type="Linear",
            vecxz_x=0.0,
            vecxz_y=0.0,
            vecxz_z=1.0,
        )
        ele = model.element.beam.force(
            ndof=6,
            section=sec,
            transformation=transf,
            numIntgrPts=5,
            maxIters=10,
            tol=1.0e-12,
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
        maxIters: int = 10,
        tol: float = 1e-12,
        **kwargs,
    ):
        """Create a ForceBeamColumnElement with validated dependencies.

        Args:
            ndof: Number of DOFs per node. Must be 3 for 2D or 6 for 3D.
            section: Managed section object integrated along the member.
            transformation: Managed geometric transformation defining the local
                element axis.
            numIntgrPts: Number of Gauss integration points along the element.
            massDens: Optional mass per unit length for dynamic analyses.
            maxIters: Maximum number of internal compatibility iterations.
            tol: Convergence tolerance for compatibility iteration.
            **kwargs: Additional element parameters stored on the base element.

        Raises:
            ValueError: If ``ndof`` is unsupported, if the section or
                transformation is missing, if integration, mass, or iteration
                inputs are invalid, or if dependencies cannot be resolved.
        """
        if ndof not in [3, 6]:
            raise ValueError(f"ForceBasedBeamColumnElement requires 3 (2D) or 6 (3D) DOFs, but got {ndof}")

        if section is None:
            raise ValueError("ForceBasedBeamColumnElement requires a section")
        self._section = self._resolve_section(section)

        if transformation is None:
            raise ValueError("ForceBasedBeamColumnElement requires a geometric transformation")
        self._transformation = self._resolve_transformation(transformation)

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

        super().__init__(
            "nonlinearBeamColumn",
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
            "Pass a managed Section object directly or use model.element.beam.force(...)"
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
            "Pass a managed GeometricTransformation object directly or use model.element.beam.force(...)"
        )

    def __str__(self):
        """Return a compact parameter summary for debugging."""
        return f"{self._section.tag} {self._transformation.tag} {self.numIntgrPts} {self.massDens} {self.maxIters} {self.tol}"

    def to_tcl(self, tag: int, nodes: List[int]) -> str:
        """Render the element as an OpenSees Tcl command.

        Args:
            tag: Assigned element tag.
            nodes: Two node tags ``[iNode, jNode]``.

        Returns:
            str: Tcl ``element nonlinearBeamColumn`` command for this element.

        Raises:
            ValueError: If ``nodes`` does not contain exactly two node tags.
        """
        if len(nodes) != 2:
            raise ValueError("Force-based beam-column element requires 2 nodes")

        nodes_str = " ".join(str(node) for node in nodes)
        cmd_parts = [f"element nonlinearBeamColumn {tag} {nodes_str}"]
        cmd_parts.append(str(self.numIntgrPts))
        cmd_parts.extend([str(self._section.tag), str(self._transformation.tag)])

        if self.massDens != 0.0:
            cmd_parts.extend(["-mass", str(self.massDens)])

        cmd_parts.extend(["-iter", str(self.maxIters), str(self.tol)])

        return " ".join(cmd_parts)

    def get_mass_per_length(self) -> float:
        """Return the mass density per unit length.

        Returns:
            Mass per unit length assigned to this element.
        """
        return self.massDens
