"""Linear elastic nD material with modulus reduction curves (LinearElasticGGmax)."""

from __future__ import annotations

from typing import Any, Dict, List, Sequence, Tuple, Union

from femora.core.material_base import Material


class LinearElasticGGmaxMaterial(Material):
    """Linear elastic soil skeleton with shear-modulus degradation versus strain.

    OpenSees evaluates an effective modulus path using a selectable backbone:
    tabulated ``(gamma, G/Gmax)``, Hardin-Drnevich style, Vucetic-Dobry, or
    Darendeli, controlled by ``curveType``. Bulk response is supplied via
    ``K_or_nu``: values in the special OpenSees ratio range are interpreted as
    Poisson's ratio and larger magnitudes are treated as bulk modulus.

    Tcl form:
        ``nDMaterial LinearElasticGGmax <tag> G K_or_nu rho curveType [tail]; #``

    Notes:
        - For ``curveType == 0`` you may omit ``pairs`` entirely or supply a
          user-defined backbone of ``gamma`` versus normalized ``G/Gmax``.
        - Positive ``rho`` enforcement matches OpenSees mass-density usage.
        - The caller is responsible for unit consistency across ``G``, ``rho``,
          and the chosen interpretation of ``K_or_nu``.

    Attributes:
        - ``params``: Curve type, modulus inputs, density, and curve-specific
          tail values exactly as queued for Tcl.

    Examples:
        ```python
        import femora as fm

        model = fm.MeshMaker()
        mat = model.material.nd.linear_elastic_ggmax(
            user_name="site_curve",
            G=62.0,
            K_or_nu=0.3,
            rho=18.8,
            curveType=1,
            param1=1e-4,
        )
        print(mat.tag)
        ```
    """

    def __init__(
        self,
        user_name: str = "Unnamed",
        *,
        G: float | None = None,
        K_or_nu: float | None = None,
        rho: float = 0.0,
        curveType: int = 1,
        pairs: Union[
            Sequence[Tuple[float, float]],
            Sequence[float],
            None,
        ] = None,
        param1: float | None = None,
        param2: float | None = None,
        param3: float | None = None,
        **_: Any,
    ) -> None:
        """Create a LinearElasticGGmax material with backbone validation rules.

        Args:
            - user_name: Unique label referenced in Tcl export comments under
              the owning material manager.
            - G: Small-strain shear modulus ``G_max``, strictly greater than zero.
            - K_or_nu: Interpreted by OpenSees as Poisson's ratio in the special
              range, otherwise as bulk modulus.
            - rho: Saturated density for mass coupling, required to be non-negative.
            - curveType: Integer backbone selector ``{0, 1, 2, 3}``.
            - pairs: User-defined backbone data for ``curveType == 0``.
            - param1: Curve-specific scalar used by built-in backbone types.
            - param2: Darendeli-specific parameter used when ``curveType == 3``.
            - param3: Darendeli-specific parameter used when ``curveType == 3``.
            - **_: Ignored compatibility keyword arguments.

        Raises:
            ValueError: If ``G`` or ``K_or_nu`` is missing.
            ValueError: If ``rho`` is negative or ``curveType`` is unsupported.
            ValueError: If user-defined backbone data are malformed.
        """
        if G is None:
            raise ValueError("LinearElasticGGmax requires 'G'.")
        Gf = float(G)
        if Gf <= 0.0:
            raise ValueError("'G' must be positive.")

        if K_or_nu is None:
            raise ValueError("LinearElasticGGmax requires 'K_or_nu'.")
        Knu = float(K_or_nu)

        rhof = float(rho)
        if rhof < 0.0:
            raise ValueError("'rho' must be non-negative.")

        ct = int(curveType)
        if ct not in (0, 1, 2, 3):
            raise ValueError("'curveType' must be one of {0, 1, 2, 3}.")

        out: Dict[str, Any] = {
            "G": Gf,
            "K_or_nu": Knu,
            "rho": rhof,
            "curveType": ct,
        }

        if ct == 0:
            pl = pairs or []
            if pl:
                if isinstance(pl[0], (list, tuple)):
                    if len(pl) < 2:
                        raise ValueError("User curve requires >= 2 (gamma, GG) pairs.")
                else:
                    lf = list(pl)
                    if len(lf) < 4 or len(lf) % 2 != 0:
                        raise ValueError(
                            "User curve requires interleaved [g1,GG1,...] with >= 4 values."
                        )
            out["pairs"] = pl
        elif ct == 1:
            out["param1"] = float(param1) if param1 is not None else 1.0e-4
        elif ct == 2:
            out["param1"] = float(param1) if param1 is not None else 0.0
        elif ct == 3:
            out["param1"] = float(param1) if param1 is not None else 0.0
            out["param2"] = float(param2) if param2 is not None else 100.0
            out["param3"] = float(param3) if param3 is not None else 1.0

        super().__init__("nDMaterial", "LinearElasticGGmax", user_name)
        self.params = out

    def to_tcl(self) -> str:
        """Emit Tcl with modulus inputs, curve selector, then curve tail values.

        Returns:
            str: Tcl line beginning with ``nDMaterial LinearElasticGGmax``.
            Curve ``0`` appends flattened backbone pairs; curves ``1`` to ``3``
            append the corresponding built-in curve parameters.

        Raises:
            ValueError: If the material is unmanaged.
        """
        p = self.params
        parts: List[str] = [
            self.material_type,
            "LinearElasticGGmax",
            str(self._require_tag()),
            str(p["G"]),
            str(p["K_or_nu"]),
            str(p["rho"]),
            str(int(p["curveType"])),
        ]

        ct = int(p["curveType"])
        if ct == 0:
            pairs = p.get("pairs", [])
            flat: List[float] = []
            if pairs and isinstance(pairs[0], (list, tuple)):
                for gamma, gg in pairs:
                    flat.extend([float(gamma), float(gg)])
            else:
                flat = [float(x) for x in pairs]
            parts.extend(str(x) for x in flat)
        elif ct == 1:
            parts.append(str(p.get("param1", 1.0e-4)))
        elif ct == 2:
            parts.append(str(p.get("param1", 0.0)))
        elif ct == 3:
            parts.append(str(p.get("param1", 0.0)))
            parts.append(str(p.get("param2", 100.0)))
            parts.append(str(p.get("param3", 1.0)))

        return " ".join(parts) + f"; # {self.user_name}"


__all__ = ["LinearElasticGGmaxMaterial"]
