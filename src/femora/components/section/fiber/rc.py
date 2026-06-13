# =============================================================================
# Femora: Fast Efficient Meta-modeling for OpenSees-based Resilience Analysis
# Copyright 2026 Amin Pakzad and Pedro Arduino
# Developed at the UW Geotechnical Lab
# SPDX-License-Identifier: Apache-2.0
# =============================================================================

"""Reinforced-concrete fiber section."""

from __future__ import annotations

from typing import List, Union

from femora.core.material_base import Material
from femora.core.section_base import Section


class RCSection(Section):
    """Template for rectangular reinforced-concrete sections.

    This section type provides a high-level abstraction for common RC beam and
    column sections. It automatically generates a fiber layout consisting of a
    confined core, an unconfined cover, and longitudinal reinforcement bars
    at a specified offset.

    Tcl form:
        ``section RC <tag> <coreMat> <coverMat> <steelMat> <d> <b> <dist>``

    Note:
        - The section is assumed to be rectangular with depth `d` and width `b`.
        - The reinforcement is placed as a single layer of fibers at the four
          corners of the core (at `cover_to_center_of_bar` distance from the
          edges).
        - This section template simplifies the creation of RC members without
          requiring manual patch or fiber definitions.

    Tip:
        - Use a confined concrete material (like `Concrete02` with high peak
          strain) for the `core_material` and an unconfined material for the
          `cover_material` to accurately model ductility.
        - If you need custom bar layouts (e.g., side bars or non-uniform
          spacing), use the general
          [FiberSection][femora.components.section.fiber.section.FiberSection]
          instead.

    Example:
        ```python
        from femora.core.model import Model
        import femora.components.section.fiber  # noqa: F401

        model = Model()
        core = model.material.uniaxial.elastic(user_name="Core", E=3600.0)
        cover = model.material.uniaxial.elastic(user_name="Cover", E=3000.0)
        steel = model.material.uniaxial.steel01(
            user_name="Steel",
            Fy=60.0,
            E0=29000.0,
            b=0.01,
        )
        sec = model.section.fiber.rc(
            user_name="Column1",
            core_material=core,
            cover_material=cover,
            steel_material=steel,
            d=24.0,
            b=24.0,
            cover_to_center_of_bar=2.5,
        )
        print(sec.tag)
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
        core_material: Union[int, str, Material],
        cover_material: Union[int, str, Material],
        steel_material: Union[int, str, Material],
        d: float,
        b: float,
        cover_to_center_of_bar: float,
    ) -> None:
        """Create an RCSection with validated materials and dimensions.

        Args:
            user_name: User-specified name for the section.
            core_material: Reference to the core concrete material.
            cover_material: Reference to the cover concrete material.
            steel_material: Reference to the reinforcement material.
            d: Total section depth.
            b: Total section width.
            cover_to_center_of_bar: Concrete cover to bar centers.

        Raises:
            ValueError: If materials cannot be resolved, if dimensions are not
                numeric, or if dimensions are non-positive.
        """
        resolved_core_material = self.resolve_material(core_material)
        if resolved_core_material is None:
            raise ValueError("RCSection requires a valid core_material")

        resolved_cover_material = self.resolve_material(cover_material)
        if resolved_cover_material is None:
            raise ValueError("RCSection requires a valid cover_material")

        resolved_steel_material = self.resolve_material(steel_material)
        if resolved_steel_material is None:
            raise ValueError("RCSection requires a valid steel_material")

        try:
            d = float(d)
            b = float(b)
            cover_to_center_of_bar = float(cover_to_center_of_bar)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "RCSection dimensions must be numeric values",
            ) from exc

        if d <= 0:
            raise ValueError("RCSection requires d > 0")
        if b <= 0:
            raise ValueError("RCSection requires b > 0")
        if cover_to_center_of_bar <= 0:
            raise ValueError("RCSection requires cover_to_center_of_bar > 0")

        super().__init__("section", "RC", user_name)
        self.core_material = resolved_core_material
        self.cover_material = resolved_cover_material
        self.steel_material = resolved_steel_material
        self.d = d
        self.b = b
        self.cover_to_center_of_bar = cover_to_center_of_bar
        self.material = self.core_material

    def to_tcl(self) -> str:
        """Render the section as an OpenSees Tcl command.

        Returns:
            str: Tcl command string for this section.

        Raises:
            ValueError: If this section has not been added to a manager.
        """
        return (
            f"section RC {self._require_tag()} {self.core_material.tag} "
            f"{self.cover_material.tag} {self.steel_material.tag} {self.d} {self.b} "
            f"{self.cover_to_center_of_bar}; # {self.user_name}"
        )

    def get_materials(self) -> List[Material]:
        """Return all unique materials used by the section.

        Returns:
            List of unique Material objects.
        """
        materials: List[Material] = []
        for material in (
            self.core_material,
            self.cover_material,
            self.steel_material,
        ):
            if material is not None and material not in materials:
                materials.append(material)
        return materials
