"""J2 cyclic bounding surface plasticity for OpenSees nD elements."""

from __future__ import annotations

from typing import Any, Dict

from femora.core.material_base import Material


class J2CyclicBoundingSurfaceMaterial(Material):
    """Bounding-surface J2 plasticity for undrained cyclic loading.

    Combines translational hardening on an inner yield surface with a bounding
    surface formulation suitable for cyclic clay-like behavior, with optional
    viscous damping term ``chi``. Use this material when cyclic stiffness and
    strength degradation are needed but a full pressure-sensitive cap model is
    not required.

    Tcl form:
        ``nDMaterial J2CyclicBoundingSurface <tag> G K Su Den h m h0 chi beta; #``

    Notes:
        - ``beta`` selects explicit (0), implicit (1), or midpoint (0.5)
          integration of the constitutive update.
        - Typical staged workflows use ``elastic`` and ``plastic`` states via
          :meth:`updateMaterialStage`.
        - ``Den`` may be zero for stiffness-only analyses.

    Attributes:
        - ``params``: Validated stiffness, strength, density, hardening,
          damping, and integration parameters keyed for Tcl emission.

    Examples:
        ```python
        import femora as fm

        model = fm.MeshMaker()
        mat = model.material.nd.j2_cyclic_bounding_surface(
            user_name="clay_cyclic",
            G=12000.0,
            K=30000.0,
            Su=15.0,
            Den=1.82,
            h=20.0,
            m=0.2,
            h0=0.5,
            chi=0.02,
            beta=0.5,
        )
        print(mat.tag)
        ```
    """

    def __init__(
        self,
        user_name: str = "Unnamed",
        *,
        G: float | None = None,
        K: float | None = None,
        Su: float | None = None,
        Den: float | None = None,
        h: float | None = None,
        m: float | None = None,
        h0: float | None = None,
        chi: float | None = None,
        beta: float = 0.5,
        **_: Any,
    ) -> None:
        """Create a J2 cyclic bounding surface material with validated parameters.

        Args:
            - user_name: Instance label appended to Tcl and stored by the owning manager.
            - G: Shear modulus, strictly positive.
            - K: Bulk modulus, strictly positive.
            - Su: Undrained shear strength, strictly positive.
            - Den: Mass density for inertia or body-force coupling, ``>= 0``.
            - h: Hardening parameter controlling plastic modulus evolution.
            - m: Hardening exponent shaping the nonlinear hardening curve.
            - h0: Initial or reference hardening level.
            - chi: Viscous damping coefficient used by the OpenSees model.
            - beta: Implicit-explicit blending weight on ``[0, 1]``.
            - **_: Ignored forward-compatibility keywords.

        Raises:
            ValueError: If any mandatory parameter is missing.
            ValueError: If a numeric parameter cannot be converted to ``float``.
            ValueError: If ``G``, ``K``, or ``Su`` is not positive, if ``Den``
                is negative, or if ``beta`` falls outside ``[0, 1]``.
        """
        required = {
            "G": G,
            "K": K,
            "Su": Su,
            "Den": Den,
            "h": h,
            "m": m,
            "h0": h0,
            "chi": chi,
        }
        out: Dict[str, float] = {}
        for name, raw in required.items():
            if raw is None:
                raise ValueError(
                    f"J2CyclicBoundingSurfaceMaterial requires the '{name}' parameter."
                )
            try:
                val = float(raw)
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    f"Invalid value for '{name}'. It must be a number."
                ) from exc
            if name in {"G", "K", "Su"} and val <= 0:
                raise ValueError(f"'{name}' must be positive.")
            if name == "Den" and val < 0:
                raise ValueError("Mass density 'Den' must be non-negative.")
            out[name] = val

        try:
            betaf = float(beta)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "Invalid value for 'beta'. It must be a number in range [0, 1]."
            ) from exc
        if not (0 <= betaf <= 1):
            raise ValueError("Integration variable 'beta' must be in range [0, 1].")
        out["beta"] = betaf

        super().__init__("nDMaterial", "J2CyclicBoundingSurface", user_name)
        self.params = out

    def to_tcl(self) -> str:
        """Render the defining Tcl command with parameters in fixed order.

        Returns:
            str: Tcl line ``nDMaterial J2CyclicBoundingSurface`` followed by the
            tag and ``G K Su Den h m h0 chi beta`` values.

        Raises:
            ValueError: If the material is unmanaged.
        """
        p = self.params
        keys = ["G", "K", "Su", "Den", "h", "m", "h0", "chi", "beta"]
        params_str = " ".join(str(p[k]) for k in keys)
        return (
            f"{self.material_type} J2CyclicBoundingSurface "
            f"{self._require_tag()} {params_str}; # {self.user_name}"
        )

    def updateMaterialStage(self, state: str) -> str:
        """Emit Tcl to switch elastic versus plastic modulus stages.

        Args:
            - state: Case-insensitive stage name. ``"elastic"`` selects stage
              ``0`` and ``"plastic"`` selects stage ``1``.

        Returns:
            str: The ``updateMaterialStage`` Tcl snippet for the matched state,
            or an empty string when ``state`` is unrecognized.

        Raises:
            ValueError: If the material is unmanaged when a supported state is requested.
        """
        if state.lower() == "elastic":
            return f"updateMaterialStage -material {self._require_tag()} -stage 0"
        if state.lower() == "plastic":
            return f"updateMaterialStage -material {self._require_tag()} -stage 1"
        return ""


__all__ = ["J2CyclicBoundingSurfaceMaterial"]
