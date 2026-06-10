# =============================================================================
# Femora: Fast Efficient Meta-modeling for OpenSees-based Resilience Analysis
# Copyright 2026 Amin Pakzad and Pedro Arduino
# Developed at the UW Geotechnical Lab
# SPDX-License-Identifier: Apache-2.0
# =============================================================================

from typing import List, Optional, Union

from femora.core.element_base import Element
from femora.core.material_base import Material


class PML3DElement(Element):
    """Three-dimensional perfectly matched layer continuum element.

    This eight-node element augments the standard brick with additional PML
    degrees of freedom, requiring 9 DOFs per node. It is used to absorb outgoing
    waves at domain boundaries in 3D wave-propagation analyses.

    Tcl form:
        ``element PML <tag> <n1> ... <n8> <matTag> <thick> "<meshType>" <params...> "-Newmark" <gamma> <beta> <eta> <ksi> [-alphabeta alpha0 beta0 | -m m -R R [-Cp Cp]]``

    Warning:
        The assigned material must be a 3D
        [ElasticIsotropicMaterial][femora.components.material.nd.elastic_isotropic.ElasticIsotropicMaterial].
        Other ``nDMaterial`` types are rejected at construction time.

    Note:
        - ``meshType`` must be ``box`` or ``general`` (case-insensitive).
        - ``meshTypeParameters`` must provide six numeric values describing the
          local PML mesh orientation and extent.
        - Either ``alpha0`` and ``beta0`` must both be supplied, or neither.

    Attributes:
        PML_Thickness: Physical thickness of the PML layer.
        meshType: PML mesh type passed to OpenSees (``box`` or ``general``).
        meshTypeParameters: Six numeric mesh-orientation parameters.
        gamma: Newmark gamma parameter.
        beta: Newmark beta parameter.
        eta: Newmark eta parameter.
        ksi: Newmark ksi parameter.
        m: PML attenuation parameter used when ``alpha0``/``beta0`` are omitted.
        R: PML reflection parameter used when ``alpha0``/``beta0`` are omitted.
        Cp: Optional P-wave speed override for the PML formulation.
        alpha0: Optional PML alpha parameter paired with ``beta0``.
        beta0: Optional PML beta parameter paired with ``alpha0``.

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        mat = model.material.nd.elastic_isotropic(
            user_name="PMLMat",
            E=2.0e7,
            nu=0.25,
            rho=2200.0,
        )
        ele = model.element.brick.pml3d(
            ndof=9,
            material=mat,
            PML_Thickness=1.0,
            meshType="box",
            meshTypeParameters=[1.0, 0.0, 0.0, 0.0, 1.0, 0.0],
        )
        print(ele.tag)
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

    def __init__(
        self,
        ndof: int,
        material: Material,
        PML_Thickness: float,
        meshType: str,
        meshTypeParameters: Union[List[float], str],
        gamma: float = 0.5,
        beta: float = 0.25,
        eta: float = 1.0 / 12.0,
        ksi: float = 1.0 / 48.0,
        m: float = 2.0,
        R: float = 1.0e-8,
        Cp: Optional[float] = None,
        alpha0: Optional[float] = None,
        beta0: Optional[float] = None,
        **kwargs,
    ):
        """Create a PML3DElement with validated PML and Newmark parameters.

        Args:
            ndof: Number of DOFs per node. Must be 9 for this element.
            material: Managed isotropic elastic 3D ``nDMaterial``.
            PML_Thickness: Thickness of the PML layer.
            meshType: ``box`` or ``general`` mesh type passed to OpenSees.
            meshTypeParameters: Six numeric values or a comma-separated string
                describing the PML mesh orientation.
            gamma: Newmark gamma parameter.
            beta: Newmark beta parameter.
            eta: Newmark eta parameter.
            ksi: Newmark ksi parameter.
            m: PML attenuation parameter when ``alpha0``/``beta0`` are omitted.
            R: PML reflection parameter when ``alpha0``/``beta0`` are omitted.
            Cp: Optional P-wave speed override.
            alpha0: Optional PML alpha parameter; must be paired with ``beta0``.
            beta0: Optional PML beta parameter; must be paired with ``alpha0``.
            **kwargs: Additional element parameters stored on the base element.

        Raises:
            ValueError: If the material is incompatible, if ``ndof`` is not 9,
                or if any PML or Newmark parameter is invalid.
        """
        if not self._is_material_compatible(material):
            raise ValueError(
                f"Material {material.user_name} with type {material.material_type} "
                "is not compatible with PML3DElement"
            )

        if ndof != 9:
            raise ValueError(f"PML3DElement requires 9 DOFs, but got {ndof}")

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

        super().__init__("PML3D", ndof, material, **kwargs)

    def to_tcl(self, tag: int, nodes: List[int]) -> str:
        """Render the element as an OpenSees Tcl command.

        Args:
            tag: Assigned element tag.
            nodes: Eight node tags in OpenSees PML order.

        Returns:
            str: Tcl ``element PML`` command for this element.

        Raises:
            ValueError: If ``nodes`` does not contain exactly eight node tags.
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
        """Check whether the material is compatible with ``PML3D``.

        Args:
            material: Material instance to validate.

        Returns:
            bool: ``True`` when the material is a 3D elastic isotropic
            ``nDMaterial``.
        """
        check = (material.material_type == "nDMaterial") and (
            material.__class__.__name__ == "ElasticIsotropicMaterial"
        )
        return check
