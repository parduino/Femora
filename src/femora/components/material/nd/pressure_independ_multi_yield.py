"""Pressure-independent multi-yield soil plasticity (OpenSees PressureIndependMultiYield)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from femora.core.material_base import Material


class PressureIndependMultiYieldMaterial(Material):
    """Nested-surface plasticity for soils without confining-stress-driven hardening.

    Use this ``nDMaterial`` when layer strength is specified through reference
    moduli, cohesion, friction, and optionally a tabular backbone instead of
    the pressure-dependent coupling used by
    [femora.components.material.nd.pressure_depend_multi_yield.PressureDependMultiYieldMaterial][].

    Tcl form:
        ``nDMaterial PressureIndependMultiYield <tag> nd rho Gr Br cohesi peakShearStra frictionAng refPress pressDependCoe noYieldSurf [gamma Gs ...]; #``

    Note:
        - Positive ``noYieldSurf`` allocates that many auto-generated surfaces.
        - Negative ``noYieldSurf`` requires ``pairs`` with ``abs(noYieldSurf)``
          backbone points.
        - ``frictionAng`` defaults to ``0``, ``refPress`` defaults to ``100``,
          and ``pressDependCoe`` defaults to ``0``.
        - [updateMaterialStage][femora.components.material.nd.pressure_independ_multi_yield.PressureIndependMultiYieldMaterial.updateMaterialStage]
          preserves ``user_name`` in an inline Tcl comment.
        - [set_parameter][femora.components.material.nd.pressure_independ_multi_yield.PressureIndependMultiYieldMaterial.set_parameter]
          emits Tcl loops for supported runtime updates.

    Attributes:
        params (dict): Final soil parameters plus optional backbone list.

    Example:
        ```python
        import femora as fm

        model = fm.Model()
        mat = model.material.nd.pressure_independ_multi_yield(
            user_name="pi_soil",
            nd=3,
            rho=2.0,
            refShearModul=1.1e5,
            refBulkModul=3.0e5,
            cohesi=5.0,
            peakShearStra=0.12,
            noYieldSurf=15,
        )
        print(mat.tag)
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__", "updateMaterialStage", "set_parameter"],
    }

    def __init__(self, user_name: str = "Unnamed", **kwargs: Any) -> None:
        """Validate soil keyword arguments before storing them for Tcl export.

        Args:
            user_name: Comment annotation and manager registry key.
            nd: ``2`` or ``3`` dimensional analysis flag.
            rho: Saturated density, strictly positive.
            refShearModul: Reference small-strain shear modulus, strictly positive.
            refBulkModul: Reference bulk modulus, strictly positive.
            cohesi: Apparent cohesion intercept, non-negative.
            peakShearStra: Octahedral shear strain marker for peak strength.
            frictionAng: Friction angle in degrees. Defaults to ``0`` when omitted.
            refPress: Positive reference mean stress. Defaults to ``100``.
            pressDependCoe: Non-negative confinement scaling coefficient.
            noYieldSurf: Surface count or negative backbone selector.
            pairs: Mandatory custom backbone list when ``noYieldSurf < 0``.

        Raises:
            ValueError: If a required keyword argument is missing.
            ValueError: If a numeric value cannot be converted correctly.
            ValueError: If any validated value falls outside the supported range.
            ValueError: If 'pairs' is malformed or invalid when required.
        """
        super().__init__("nDMaterial", "PressureIndependMultiYield", user_name)
        validated: Dict[str, Any] = {}

        required = [
            "nd",
            "rho",
            "refShearModul",
            "refBulkModul",
            "cohesi",
            "peakShearStra",
        ]

        for key in required:
            value = kwargs.get(key)
            if value is None:
                raise ValueError(f"PressureIndependMultiYield requires the '{key}' parameter.")
            try:
                value_coerced = int(value) if key == "nd" else float(value)
            except (ValueError, TypeError) as exc:
                raise ValueError(f"Invalid value for '{key}'. It must be numeric.") from exc
            if key == "nd" and value_coerced not in (2, 3):
                raise ValueError("'nd' must be 2 or 3.")
            if key in ("rho", "refShearModul", "refBulkModul", "peakShearStra") and value_coerced <= 0:
                raise ValueError(f"'{key}' must be positive.")
            if key == "cohesi" and value_coerced < 0:
                raise ValueError("'cohesi' must be non-negative.")
            validated[key] = value_coerced

        defaults = {
            "frictionAng": 0.0,
            "refPress": 100.0,
            "pressDependCoe": 0.0,
        }
        for key, default in defaults.items():
            raw = kwargs.get(key, default)
            try:
                vf = float(raw)
            except (ValueError, TypeError) as exc:
                raise ValueError(f"Invalid value for '{key}'. It must be numeric.") from exc
            if key == "frictionAng" and not (0 <= vf <= 90):
                raise ValueError("'frictionAng' must be in [0, 90].")
            if key == "refPress" and vf <= 0:
                raise ValueError("'refPress' must be positive.")
            if key == "pressDependCoe" and vf < 0:
                raise ValueError("'pressDependCoe' must be non-negative.")
            validated[key] = vf

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
            if not pairs_param:
                raise ValueError("When 'noYieldSurf' is negative, provide 'pairs'.")
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
                        pairs_list = [(float(gamma), float(gs)) for gamma, gs in pairs_param]
                    except Exception as exc:
                        raise ValueError("Invalid 'pairs' format.") from exc
            else:
                raise ValueError("'pairs' must be a list.")
            if len(pairs_list) != expected_pairs:
                raise ValueError(f"Expected {expected_pairs} pairs, got {len(pairs_list)}.")
            for gamma, gs in pairs_list:
                if gamma <= 0 or not (0 < gs <= 1.0):
                    raise ValueError("Invalid gamma (>0) or Gs (0, 1] in pairs.")
            validated["pairs"] = pairs_list

        self.params = validated

    def to_tcl(self) -> str:
        """Emit the Tcl declaration with optional backbone tail expansion.

        Returns:
            str: Tcl line including moduli, cohesion, friction defaults,
            ``noYieldSurf``, and interleaved backbone pairs when applicable.

        Raises:
            ValueError: If the material was not registered with a manager.
        """
        p = self.params
        parts = [
            self.material_type,
            "PressureIndependMultiYield",
            str(self._require_tag()),
            str(int(p["nd"])),
            str(p["rho"]),
            str(p["refShearModul"]),
            str(p["refBulkModul"]),
            str(p["cohesi"]),
            str(p["peakShearStra"]),
            str(p["frictionAng"]),
            str(p["refPress"]),
            str(p["pressDependCoe"]),
        ]

        no_yield = int(p.get("noYieldSurf", 20))
        parts.append(str(no_yield))

        if no_yield < 0:
            pairs = p.get("pairs", [])
            for gamma, gs in pairs:
                parts.append(str(gamma))
                parts.append(str(gs))

        return " ".join(parts) + f"; # {self.user_name}"

    def updateMaterialStage(self, state: str) -> str:
        """Construct Tcl for elastic/plastic modulus staging plus inline comment tag.

        Args:
            state: ``"elastic"`` maps to stage ``0`` and ``"plastic"``
                maps to stage ``1``. Other tokens return blank output.

        Returns:
            str: Tcl with `` ;# user_name`` suffix when a stage matched.

        Raises:
            ValueError: When no tag has been assigned yet.
        """
        if state.lower() == "elastic":
            return (
                f"updateMaterialStage -material {self._require_tag()} -stage 0"
                f" ;# {self.user_name}"
            )
        if state.lower() == "plastic":
            return (
                f"updateMaterialStage -material {self._require_tag()} -stage 1"
                f" ;# {self.user_name}"
            )
        return ""

    def set_parameter(
        self,
        parameter_name: str,
        new_value: Optional[float] = None,
        element_tags: Optional[List[int]] = None,
    ) -> str:
        """Build Tcl that updates material parameters element-by-element.

        Args:
            parameter_name: One of ``shearModulus``, ``bulkModulus``,
                ``cohesion``, ``frictionAngle``, or ``stressCorrection``.
            new_value: Scalar passed to ``-val`` for non-stress-correction
                modes. Ignored for ``stressCorrection``.
            element_tags: OpenSees element IDs to touch.

        Returns:
            str: Multi-line Tcl script suitable for appending to staged analyses.

        Raises:
            ValueError: If ``parameter_name`` is unsupported.
            ValueError: If the material lacks a manager-assigned tag.
        """
        valid = {
            "shearModulus",
            "bulkModulus",
            "cohesion",
            "frictionAngle",
            "stressCorrection",
        }
        if parameter_name not in valid:
            raise ValueError(
                f"Parameter '{parameter_name}' is not valid for "
                "PressureIndependMultiYieldMaterial."
            )

        tags_str = "{" + " ".join(str(t) for t in (element_tags or [])) + "}"
        tag = self._require_tag()

        tcl = " set domainEleTags [getEleTags]\n"
        tcl += f"foreach eleTag {tags_str} {{\n"
        tcl += "    if {![lsearch -exact $domainEleTags $eleTag]} {\n"
        tcl += "        continue\n"
        tcl += "    }\n"
        tcl += "    set matTag [eleMaterial $eleTag]\n"

        if parameter_name == "shearModulus":
            tcl += f"    setParameter -val {new_value} -ele $eleTag material {tag} shearModulus\n"
        elif parameter_name == "bulkModulus":
            tcl += f"    setParameter -val {new_value} -ele $eleTag material {tag} bulkModulus\n"
        elif parameter_name == "cohesion":
            tcl += f"    setParameter -val {new_value} -ele $eleTag material {tag} cohesion\n"
        elif parameter_name == "frictionAngle":
            tcl += f"    setParameter -val {new_value} -ele $eleTag material {tag} frictionAngle\n"
        elif parameter_name == "stressCorrection":
            tcl += "    set sigmaV0 [eleResponse $eleTag stress3D6]\n"
            tcl += "    set sigmaV0 [lindex $sigmaV0 2]\n"
            tcl += f"    setParameter -val $sigmaV0 -ele $eleTag material {tag} shearModulus\n"
            tcl += f"    setParameter -val $sigmaV0 -ele $eleTag material {tag} bulkModulus\n"

        tcl += "}\n"
        return tcl


__all__ = ["PressureIndependMultiYieldMaterial"]