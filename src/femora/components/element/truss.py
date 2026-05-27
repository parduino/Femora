from typing import List, Union

from femora.core.element_base import Element
from femora.core.section_base import Section


class TrussElement(Element):
    """Axial truss element defined by a section stiffness model.

    This two-node element carries axial force only. Cross-section area and axial
    stiffness come from the assigned section, typically an elastic section for
    braces or struts. It supports 2D, 3D, or mixed 6-DOF structural models.

    Tcl form:
        ``element trussSection <tag> <iNode> <jNode> <secTag> <-rho rho> <-cMass cFlag> <-doRayleigh rFlag>``

    Note:
        - Requires a managed section with an assigned tag before Tcl export.
        - ``rho`` supplies optional mass per unit length for dynamic analyses.

    Attributes:
        rho: Mass per unit length used when dynamic mass formation is requested.
        cMass: Consistent-mass flag passed to OpenSees (``0`` or ``1``).
        doRayleigh: Rayleigh-damping flag passed to OpenSees (``0`` or ``1``).

    Example:
        ```python
        from femora.core.model import Model
        import femora.components.section.beam  # noqa: F401

        model = Model()
        sec = model.section.beam.elastic(
            user_name="Brace",
            E=29000.0,
            A=2.5,
            Iz=0.1,
        )
        ele = model.element.beam.truss(
            ndof=3,
            section=sec,
            rho=0.01,
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
        rho: float = 0.0,
        cMass: int = 0,
        doRayleigh: int = 0,
        **kwargs,
    ):
        """Create a TrussElement with validated section and mass options.

        Args:
            ndof: Number of nodal DOFs in the surrounding model (2, 3, or 6).
            section: Managed section object defining axial stiffness and area.
            rho: Optional mass per unit length.
            cMass: Consistent mass flag, ``0`` or ``1``.
            doRayleigh: Rayleigh damping flag, ``0`` or ``1``.
            **kwargs: Additional element parameters stored on the base element.

        Raises:
            ValueError: If inputs are invalid or the section cannot be resolved.
        """
        if ndof not in (2, 3, 6):
            raise ValueError("TrussElement requires 2, 3, or 6 DOFs")

        if section is None:
            raise ValueError("TrussElement requires a section")
        resolved_section = self._resolve_section(section)

        self.rho = float(rho)
        if self.rho < 0.0:
            raise ValueError("TrussElement rho must be non-negative")

        self.cMass = int(cMass)
        if self.cMass not in (0, 1):
            raise ValueError("cMass must be 0 or 1")

        self.doRayleigh = int(doRayleigh)
        if self.doRayleigh not in (0, 1):
            raise ValueError("doRayleigh must be 0 or 1")

        super().__init__(
            "trussSection",
            ndof,
            material=None,
            section=resolved_section,
            rho=self.rho,
            cMass=self.cMass,
            doRayleigh=self.doRayleigh,
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
            "Pass a managed Section object directly or use model.element.beam.truss(...)"
        )

    def to_tcl(self, tag: int, nodes: List[int]) -> str:
        """Render the element as an OpenSees Tcl command.

        Args:
            tag: Assigned element tag.
            nodes: Two node tags ``[iNode, jNode]``.

        Returns:
            str: Tcl ``element trussSection`` command for this element.

        Raises:
            ValueError: If ``nodes`` does not contain exactly two node tags or
                if no section is assigned.
        """
        if len(nodes) != 2:
            raise ValueError("TrussElement requires exactly 2 nodes")
        if self._section is None:
            raise ValueError("TrussElement requires a section")

        cmd = [
            "element",
            "trussSection",
            str(tag),
            str(nodes[0]),
            str(nodes[1]),
            str(self._section.tag),
        ]
        if self.rho != 0.0:
            cmd.extend(["-rho", str(self.rho)])
        if self.cMass != 0:
            cmd.extend(["-cMass", str(self.cMass)])
        if self.doRayleigh != 0:
            cmd.extend(["-doRayleigh", str(self.doRayleigh)])
        return " ".join(cmd)

    def get_mass_per_length(self) -> float:
        """Return the mass per unit length assigned to this truss element.

        Returns:
            Mass per unit length from ``rho``.
        """
        return self.rho
