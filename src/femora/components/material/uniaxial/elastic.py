"""Uniaxial linear elastic material used with OpenSees truss, spring, and fiber models."""

from __future__ import annotations

from typing import Any, Dict

from femora.core.material_base import Material


class ElasticUniaxialMaterial(Material):
    """One-dimensional elastic stress-strain law with optional asymmetric stiffness.

    Suitable for simple bars, trusses, springs, and fiber sections needing a
    basic uniaxial constitutive rule. The tangent ``E`` controls loading
    stiffness, ``eta`` adds optional damping tangent contribution, and
    ``Eneg`` sets an optional distinct compression tangent.

    Tcl form:
        ``uniaxialMaterial Elastic <tag> E eta Eneg; # user_name``

    Note:
        - Manager ownership is required before Tcl export so the OpenSees tag
          can be inserted after ``Elastic``.
        - ``Eneg`` defaults to ``E`` when omitted.

    Attributes:
        params: Mapping of emitted ``E``, ``eta``, and ``Eneg`` values.

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        mat = model.material.uniaxial.elastic(
            user_name="rebar_truss",
            E=200000.0,
            eta=0.0,
            Eneg=200000.0,
        )
        print(mat.tag)
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

    def __init__(
        self,
        user_name: str = "Unnamed",
        *,
        E: float | None = None,
        eta: float = 0.0,
        Eneg: float | None = None,
        **_: Any,
    ) -> None:
        """Normalize moduli and damping tangent for OpenSees insertion.

        Args:
            user_name: Comment key for Tcl plus manager uniqueness constraint.
            E: Primary tensile or loading stiffness, strictly positive.
            eta: Supplemental damping tangent, non-negative after coercion.
            Eneg: Compression-side stiffness. Falls back to ``E`` when omitted.
            **_: Ignored extension keywords.

        Raises:
            ValueError: If ``E`` is missing.
            ValueError: If ``E``, ``eta``, or ``Eneg`` cannot be converted to numeric values.
            ValueError: If ``E`` or ``Eneg`` is not positive, or if ``eta`` is negative.
        """
        if E is None:
            raise ValueError("ElasticUniaxialMaterial requires the 'E' parameter.")
        try:
            Ef = float(E)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "Invalid value for 'E'. It must be a positive number."
            ) from exc
        if Ef <= 0:
            raise ValueError("Elastic modulus 'E' must be positive.")

        try:
            etaf = float(eta)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "Invalid value for 'eta'. It must be a non-negative number."
            ) from exc
        if etaf < 0:
            raise ValueError("Damping ratio 'eta' must be non-negative.")

        if Eneg is None:
            Enegf = Ef
        else:
            try:
                Enegf = float(Eneg)
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    "Invalid value for 'Eneg'. It must be a positive number."
                ) from exc
            if Enegf <= 0:
                raise ValueError("Negative elastic modulus 'Eneg' must be positive.")

        super().__init__("uniaxialMaterial", "Elastic", user_name)
        self.params: Dict[str, float] = {"E": Ef, "eta": etaf, "Eneg": Enegf}

    def to_tcl(self) -> str:
        """Return the ``uniaxialMaterial Elastic`` command for this instance.

        Returns:
            str: Tcl string with ``Elastic``, the assigned tag, and the stored
            ``E``, ``eta``, and ``Eneg`` values.

        Raises:
            ValueError: If the material is unmanaged.
        """
        p = self.params
        return (
            f"{self.material_type} Elastic "
            f"{self._require_tag()} {p['E']} {p['eta']} {p['Eneg']}; # {self.user_name}"
        )


__all__ = ["ElasticUniaxialMaterial"]
