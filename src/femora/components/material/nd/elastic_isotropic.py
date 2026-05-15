"""Isotropic linear elastic continuum material for OpenSees nD elements."""

from __future__ import annotations

from typing import Any, Dict

from femora.core.material_base import Material


class ElasticIsotropicMaterial(Material):
    """Homogeneous isotropic elastic solid with constant stiffness and density.

    This model wraps OpenSees ``ElasticIsotropic`` for use as an ``nDMaterial``.
    Stress-strain behavior is governed by Young's modulus and Poisson's ratio.
    Optional mass density is included for analyses that read material density
    for inertia or gravity effects.

    Tcl form:
        ``nDMaterial ElasticIsotropic <tag> <E> <nu> <rho>; # user_name``

    Notes:
        - Coordinate ``E``, ``nu``, and ``rho`` with the unit system used by
          the mesh and exported Tcl model.
        - ``rho`` defaults to ``0.0`` when the material is used without mass.
        - Duplicate ``user_name`` values are rejected by the owning
          :class:`~femora.core.material_manager.MaterialManager`.
        - Instances are typically created through
          :meth:`~femora.core.nd_material_manager.NDMaterialManager.elastic_isotropic`.

    Attributes:
        - ``params``: Stored validated parameters keyed by ``E``, ``nu``, and ``rho``.

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
        """Create an elastic isotropic material with validated moduli and density.

        Args:
            - user_name: Label referenced in the emitted Tcl comment and stored
              by the owning material manager.
            - E: Young's modulus. Must convert to a finite float strictly
              greater than zero.
            - nu: Poisson's ratio. Must lie in ``[0, 0.5)`` after conversion to ``float``.
            - rho: Mass density, non-negative after conversion. Defaults to
              ``0.0`` for stiffness-only use.
            - **_: Additional keyword arguments accepted and ignored for
              forward-compatible factory calls.

        Raises:
            ValueError: When ``E`` or ``nu`` is missing.
            ValueError: When ``E``, ``nu``, or ``rho`` cannot be converted to numeric values.
            ValueError: When ``E`` is not positive, ``nu`` falls outside ``[0, 0.5)``,
                or ``rho`` is negative.
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
            str: Tcl source line defining this material using the assigned tag
            and stored parameter values, ending with ``; # user_name``.

        Raises:
            ValueError: If this instance has no manager-assigned tag yet.
        """
        p = self.params
        return (
            f"{self.material_type} ElasticIsotropic "
            f"{self._require_tag()} {p['E']} {p['nu']} {p['rho']}; # {self.user_name}"
        )


__all__ = ["ElasticIsotropicMaterial"]
