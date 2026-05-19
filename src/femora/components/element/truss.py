from typing import Dict, List, Union

from femora.core.section_base import Section
from femora.core.element_base import Element


class TrussElement(Element):
    """OpenSees truss element using a section definition.

    Tcl form:
        ``element trussSection <tag> <iNode> <jNode> <secTag>
        <-rho rho> <-cMass cFlag> <-doRayleigh rFlag>``

    Cross-section properties and axial stiffness come from the ``Section`` object
    (typically ``section Elastic`` for elastic struts/braces).
    """

    def __init__(
        self,
        ndof: int,
        section: Union[Section, int, str],
        rho: float = 0.0,
        cMass: int = 0,
        doRayleigh: int = 0,
        **kwargs,
    ):
        """Create a truss element definition.

        Args:
            ndof: Number of nodal DOFs in the surrounding model (2, 3, or 6).
            section: Section object, tag, or user name.
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
        """Resolve a section object."""
        if isinstance(section_input, Section):
            return section_input
        raise ValueError(f"Cannot resolve section '{section_input}' in unmanaged element creation. Pass a managed Section object directly or use model.element.beam.truss(...)")

    def to_tcl(self, tag: int, nodes: List[int]) -> str:
        """Generate the OpenSees TCL command for this truss element."""
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
        return self.rho

