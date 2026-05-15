Understood — I’ll review the target file and related material manager/base context first, then update only docstrings in the target file.

I’ve confirmed the manager usage path and will now normalize the target file docstrings to the project format without changing any code behavior.

"""Isotropic linear elastic continuum material for OpenSees nD elements."""

from __future__ import annotations

from typing import Any, Dict

from femora.core.material_base import Material


class ElasticIsotropicMaterial(Material):
    """Homogeneous isotropic elastic material for continuum nD analysis.

    This class represents the OpenSees ``ElasticIsotropic`` nD material model.
    The constitutive response is defined by Young's modulus and Poisson's ratio,
    with optional density for analyses that require material mass.

    Tcl form:
        ``nDMaterial ElasticIsotropic <tag> <E> <nu> <rho>; # user_name``

    Notes:
        - Coordinate ``E``, ``nu``, and ``rho`` with the unit system used by
          the mesh and exported Tcl model.
        - ``rho`` defaults to ``0.0`` for stiffness-only definitions.
        - Instances are typically created through
          :meth:`~femora.core.nd_material_manager.NDMaterialManager.elastic_isotropic`.

    Attributes:
        tag: Manager-assigned identifier after registration with the owning
            material manager.
        params: Validated parameter values keyed by ``E``, ``nu``, and ``rho``.

    Examples:
        ```python
        import femora as fm

        model = fm.MeshMaker()
        mat = model.material.nd.elastic_isotropic(
            user_name="sand",
            E=3.0e7,
            nu=0.3,
            rho=2000.0,
        )
        print(mat.tag)
        ```
    """

    def __init__(
        self,
        user_name: str = "Unnamed",
        *,
        E: float | None = None,
        nu: float | None = None,
        rho: float = 0.0,
        **_: Any,
    ) -> None:
        """Create an elastic isotropic material with validated parameters.

        Args:
            user_name: Label included in the emitted Tcl comment and stored by
                the owning material manager.
            E: Young's modulus. Must be a positive numeric value.
            nu: Poisson's ratio. Must be numeric and in the range ``[0, 0.5)``.
            rho: Mass density. Must be a non-negative numeric value.
            **_: Additional keyword arguments accepted and ignored for
                forward-compatible factory calls.

        Raises:
            ValueError: If ``E`` or ``nu`` is missing, if any numeric parameter
                cannot be converted to ``float``, if ``E`` is not positive, if
                ``nu`` is outside ``[0, 0.5)``, or if ``rho`` is negative.
        """
        if E is None:
            raise ValueError("ElasticIsotropicMaterial requires the 'E' parameter.")
        try:
            Ef = float(E)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "Invalid value for 'E'. It must be a positive number."
            ) from exc
        if Ef <= 0:
            raise ValueError("Elastic modulus 'E' must be positive.")

        if nu is None:
            raise ValueError("ElasticIsotropicMaterial requires the 'nu' parameter.")
        try:
            nuf = float(nu)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "Invalid value for 'nu'. It must be a number in range [0, 0.5)."
            ) from exc
        if not (0 <= nuf < 0.5):
            raise ValueError("Poisson's ratio 'nu' must be in the range [0, 0.5).")

        try:
            rhof = float(rho)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "Invalid value for 'rho'. It must be a non-negative number."
            ) from exc
        if rhof < 0:
            raise ValueError("Density 'rho' must be non-negative.")

        super().__init__("nDMaterial", "ElasticIsotropic", user_name)
        self.params: Dict[str, float] = {"E": Ef, "nu": nuf, "rho": rhof}

    def to_tcl(self) -> str:
        """Render the OpenSees ``nDMaterial ElasticIsotropic`` command.

        Returns:
            str: Tcl command defining this material with its assigned tag and
                validated parameters, ending with ``; # user_name``.

        Raises:
            ValueError: If this instance has no manager-assigned tag yet.
        """
        p = self.params
        return (
            f"{self.material_type} ElasticIsotropic "
            f"{self._require_tag()} {p['E']} {p['nu']} {p['rho']}; # {self.user_name}"
        )


__all__ = ["ElasticIsotropicMaterial"]
