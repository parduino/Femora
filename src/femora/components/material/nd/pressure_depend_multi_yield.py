"""Pressure-dependent multi-yield soil plasticity (OpenSees PressureDependMultiYield)."""

from __future__ import annotations

from typing import Any, Dict, List

from femora.core.material_base import Material


class PressureDependMultiYieldMaterial(Material):
    """Layered-yield soil plasticity with evolving strength versus confining stress.

    This model targets saturated soil elements that require confining-stress
    dependent stiffness together with nested yield surfaces or a user-defined
    backbone to capture nonlinear soil response. Parameter names follow the
    OpenSees command vocabulary directly.

    Tcl form:
        ``nDMaterial PressureDependMultiYield <tag> nd rho Gr Br ... liquefac3 noYieldSurf [gamma Gs ...] e cs1 cs2 cs3 pa c; #``

    Notes:
        - ``nd`` must be ``2`` for plane strain or ``3`` for three-dimensional use.
        - Positive ``noYieldSurf`` requests auto-generated nested yield surfaces.
        - Negative ``noYieldSurf`` switches to user-defined backbone input with
          ``abs(noYieldSurf)`` ``(gamma, Gs)`` pairs.
        - Supplied ``pairs`` may be a flat list ``[g1, Gs1, ...]`` or a list of
          ``(gamma, Gs)`` tuples.
        - Unrecognized keyword arguments are ignored for compatibility.

    Attributes:
        - ``params``: Validated soil, backbone, and optional critical-state constants.

    Examples:
        ```python
        import femora as fm

        model = fm.MeshMaker()
        mat = model.material.nd.pressure_depend_multi_yield(
            user_name="profiled_soil",
            nd=3,
            rho=2.0,
            refShearModul=1.0e5,
            refBulkModul=3.0e5,
            frictionAng=37.0,
            peakShearStra=0.1,
            refPress=80.0,
            pressDependCoe=0.5,
            PTAng=27.0,
            contrac=0.05,
            dilat1=0.6,
            dilat2=3.0,
            liquefac1=5.0,
            liquefac2=0.003,
            liquefac3=1.0,
            noYieldSurf=20,
        )
        print(mat.tag)
        ```
    """

    def __init__(self, user_name: str = "Unnamed", **kwargs: Any) -> None:
        """Construct the material from keyword arguments matching OpenSees naming.

        Args:
            - user_name: Label placed in the trailing Tcl comment once managed.
            - nd: Spatial dimension flag, either ``2`` or ``3``.
            - rho: Saturated mass density, strictly positive in model units.
            - refShearModul: Reference low-strain shear modulus at ``refPress``.
            - refBulkModul: Reference bulk modulus at ``refPress``.
            - frictionAng: Peak friction angle in degrees.
            - peakShearStra: Octahedral shear strain at peak strength, strictly positive.
            - refPress: Reference mean effective stress, strictly positive.
            - pressDependCoe: Non-negative confinement dependence coefficient.
            - PTAng: Phase-transformation angle in degrees.
            - contrac: Contractive plasticity parameter.
            - dilat1: First dilatancy parameter.
            - dilat2: Second dilatancy parameter.
            - liquefac1: Liquefaction parameter 1.
            - liquefac2: Liquefaction parameter 2.
            - liquefac3: Liquefaction parameter 3.
            - noYieldSurf: Surface count or negative custom-backbone selector.
            - pairs: Custom backbone data required when ``noYieldSurf < 0``.
            - e: Optional void ratio, default ``0.6``.
            - cs1: Optional critical-state coefficient, default ``0.9``.
            - cs2: Optional critical-state coefficient, default ``0.02``.
            - cs3: Optional critical-state coefficient, default ``0.7``.
            - pa: Optional atmospheric or reference pressure, default ``101.0``.
            - c: Optional cohesion-like intercept, default ``0.3``.

        Raises:
            ValueError: If a required Tcl argument is missing.
            ValueError: If a numeric Tcl argument cannot be converted correctly.
            ValueError: If any validated value falls outside the supported range.
        """
        super().__init__("nDMaterial", "PressureDependMultiYield", user_name)
        validated: Dict[str, Any] = {}

        required = [
            "nd",
            "rho",
            "refShearModul",
            "refBulkModul",
            "frictionAng",
            "peakShearStra",
            "refPress",
            "pressDependCoe",
            "PTAng",
            "contrac",
            "dilat1",
            "dilat2",
            "liquefac1",
            "liquefac2",
            "liquefac3",
        ]

        for key in required:
            value = kwargs.get(key)
            if value is None:
                raise ValueError(f"PressureDependMultiYield requires the '{key}' parameter.")
            try:
                value_coerced = int(value) if key == "nd" else float(value)
            except (ValueError, TypeError) as exc:
                raise ValueError(f"Invalid value for '{key}'. It must be numeric.") from exc
            if key == "nd" and value_coerced not in (2, 3):
                raise ValueError("'nd' must be 2 (plane strain) or 3 (3D).")
            if key in ("rho", "refShearModul", "refBulkModul") and float(value_coerced) <= 0:
                raise ValueError(f"'{key}' must be positive.")
            if key in ("frictionAng", "PTAng") and not (0 <= float(value_coerced) <= 90):
                raise ValueError(f"'{key}' must be in degrees within [0, 90].")
            if key == "pressDependCoe" and float(value_coerced) < 0:
                raise ValueError("'pressDependCoe' must be non-negative.")
            if key == "peakShearStra" and float(value_coerced) <= 0:
                raise ValueError("'peakShearStra' must be positive.")
            validated[key] = value_coerced

        no_yield = kwargs.get("noYieldSurf", 20)
        try:
            no_yield_int = int(no_yield)
        except (ValueError, TypeError) as exc:
            raise ValueError("'noYieldSurf' must be an integer.") from exc
        if no_yield_int == 0 or abs(no_yield_int) >= 40:
            raise ValueError("'noYieldSurf' must be non-zero and less than 40 in magnitude.")
        validated["noYieldSurf"] = no_yield_int

        if no_yield_int < 0:
            expected_pairs = abs(no_yield_int)
            pairs_param = kwargs.get("pairs")
            if pairs_param is None:
                raise ValueError(
                    "When 'noYieldSurf' is negative, provide 'pairs' as a list of "
                    "(gamma, Gs) or a flat list of length 2N."
                )
            pairs_list: List[tuple[float, float]] = []
            if isinstance(pairs_param, list):
                if (
                    len(pairs_param) == 2 * expected_pairs
                    and all(isinstance(x, (int, float)) for x in pairs_param)
                ):
                    it = iter(pairs_param)
                    pairs_list = [(float(gamma), float(gs)) for gamma, gs in zip(it, it)]
                else:
                    try:
                        pairs_list = [
                            (float(gamma), float(gs)) for gamma, gs in pairs_param
                        ]
                    except Exception as exc:
                        raise ValueError(
                            "'pairs' must be a list of (gamma, Gs) or a flat list of "
                            "numeric values of length 2N."
                        ) from exc
            else:
                raise ValueError("'pairs' must be provided as a list.")
            if len(pairs_list) != expected_pairs:
                raise ValueError(
                    f"Expected {expected_pairs} (gamma, Gs) pairs, got {len(pairs_list)}."
                )
            for gamma, gs in pairs_list:
                if gamma <= 0:
                    raise ValueError("Each gamma must be positive.")
                if not (0 < gs <= 1.0):
                    raise ValueError("Each Gs must be in (0, 1].")
            validated["pairs"] = pairs_list

        optionals = {
            "e": 0.6,
            "cs1": 0.9,
            "cs2": 0.02,
            "cs3": 0.7,
            "pa": 101.0,
            "c": 0.3,
        }
        for key, default in optionals.items():
            raw = kwargs.get(key, default)
            try:
                vf = float(raw)
            except (ValueError, TypeError) as exc:
                raise ValueError(f"Invalid value for '{key}'. It must be numeric.") from exc
            if key in ("e", "cs1", "cs2", "cs3") and vf < 0:
                raise ValueError(f"'{key}' must be non-negative.")
            if key == "pa" and vf <= 0:
                raise ValueError("'pa' must be positive.")
            if key == "c" and vf < 0:
                raise ValueError("'c' must be non-negative.")
            validated[key] = vf

        self.params = validated

    def to_tcl(self) -> str:
        """Flatten parameters into the long OpenSees PressureDependMultiYield line.

        Returns:
            str: Tcl text beginning with ``nDMaterial PressureDependMultiYield``
            followed by the primary soil parameters, ``noYieldSurf``, optional
            backbone scalars, and the trailing ``e cs1 cs2 cs3 pa c`` block.

        Raises:
            ValueError: If the material is not yet tagged by a manager.
        """
        p = self.params
        parts = [
            self.material_type,
            "PressureDependMultiYield",
            str(self._require_tag()),
            str(int(p["nd"])),
            str(p["rho"]),
            str(p["refShearModul"]),
            str(p["refBulkModul"]),
            str(p["frictionAng"]),
            str(p["peakShearStra"]),
            str(p["refPress"]),
            str(p["pressDependCoe"]),
            str(p["PTAng"]),
            str(p["contrac"]),
            str(p["dilat1"]),
            str(p["dilat2"]),
            str(p["liquefac1"]),
            str(p["liquefac2"]),
            str(p["liquefac3"]),
        ]

        no_yield = int(p.get("noYieldSurf", 20))
        parts.append(str(no_yield))

        if no_yield < 0:
            pairs = p.get("pairs", [])
            for gamma, gs in pairs:
                parts.append(str(gamma))
                parts.append(str(gs))

        parts.extend(
            [
                str(p["e"]),
                str(p["cs1"]),
                str(p["cs2"]),
                str(p["cs3"]),
                str(p["pa"]),
                str(p["c"]),
            ]
        )

        return " ".join(parts) + f"; # {self.user_name}"

    def updateMaterialStage(self, state: str) -> str:
        """Return Tcl that toggles elastic staging for staged analysis workflows.

        Args:
            - state: ``"elastic"`` maps to stage ``0`` and ``"plastic"``
              maps to stage ``1``. Other strings yield an empty return.

        Returns:
            str: An ``updateMaterialStage`` command or an empty string.

        Raises:
            ValueError: If the material tag is still ``None``.
        """
        if state.lower() == "elastic":
            return f"updateMaterialStage -material {self._require_tag()} -stage 0"
        if state.lower() == "plastic":
            return f"updateMaterialStage -material {self._require_tag()} -stage 1"
        return ""


__all__ = ["PressureDependMultiYieldMaterial"]
