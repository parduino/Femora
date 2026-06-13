# =============================================================================
# Femora: Fast Efficient Meta-modeling for OpenSees-based Resilience Analysis
# Copyright 2026 Amin Pakzad and Pedro Arduino
# Developed at the UW Geotechnical Lab
# SPDX-License-Identifier: Apache-2.0
# =============================================================================

"""Concrete OpenSees geometric transformation classes.

Concrete geometric transformations are runtime objects that represent the `geomTransf`
command in OpenSees. They define how beam-column elements transform nodal
displacements and forces between local and global coordinate systems.

These objects do not self-register; their `tag` is assigned when they are
managed by a `femora.core.transformation_manager.TransformationManager`.
"""

from __future__ import annotations

import math

from femora.core.transformation_base import GeometricTransformation


class GeometricTransformation2D(GeometricTransformation):
    """Represents a 2D geometric transformation for OpenSees beam-column elements.

    GeometricTransformation2D defines how 2D beam-column elements transform nodal forces
    and displacements between local and global coordinate systems. It supports
    transformation formulations (such as 'Linear', 'PDelta', or 'Corotational')
    and optional joint offsets at the element ends.

    Tcl form:
        ``geomTransf <transf_type> <tag> [-jntOffset <d_xi> <d_yi> <d_xj> <d_yj>]``

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        transf2d = model.transformation.transformation2d(
            transf_type="Linear",
            d_xi=0.1,
            d_yi=0.05,
            description="Linear transformation with offsets",
        )
        print(transf2d.tag)
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__", "has_joint_offsets"],
    }

    def __init__(
        self,
        transf_type: str,
        d_xi: float | str = 0.0,
        d_yi: float | str = 0.0,
        d_xj: float | str = 0.0,
        d_yj: float | str = 0.0,
        description: str = "",
    ):
        """Create a 2D geometric transformation.

        Args:
            transf_type: Type of geometric transformation (e.g., 'Linear',
                'PDelta', 'Corotational').
            d_xi: Joint offset in the local x-direction at start node I.
            d_yi: Joint offset in the local y-direction at start node I.
            d_xj: Joint offset in the local x-direction at end node J.
            d_yj: Joint offset in the local y-direction at end node J.
            description: Optional description for the transformation.
        """
        super().__init__(transf_type, 2, description=description)
        self.d_xi = float(d_xi)
        self.d_yi = float(d_yi)
        self.d_xj = float(d_xj)
        self.d_yj = float(d_yj)

    def has_joint_offsets(self) -> bool:
        """Check if the transformation has non-zero joint offsets.

        Returns:
            True if any joint offset exceeds `self.eps` in absolute magnitude,
            False otherwise.
        """
        return any(abs(val) > self.eps for val in [self.d_xi, self.d_yi, self.d_xj, self.d_yj])

    def to_tcl(self) -> str:
        """Render this 2D geometric transformation as an OpenSees Tcl command.

        Returns:
            The Tcl command string.
        """
        cmd = f"geomTransf {self.transformation_type} {self._require_tag()}"
        if self.has_joint_offsets():
            cmd += f" -jntOffset {self.d_xi} {self.d_yi} {self.d_xj} {self.d_yj}"
        if self.description != "":
            cmd += f"; # {self.description}"
        return cmd


class GeometricTransformation3D(GeometricTransformation):
    """Represents a 3D geometric transformation for OpenSees beam-column elements.

    GeometricTransformation3D defines how 3D beam-column elements transform nodal forces
    and displacements between local and global coordinate systems. It requires a
    `vecxz` vector to define the orientation of the local x-z plane, and supports
    optional joint offsets at the element ends.

    Tcl form:
        ``geomTransf <transf_type> <tag> <vecxz_x> <vecxz_y> <vecxz_z> [-jntOffset <d_xi> <d_yi> <d_zi> <d_xj> <d_yj> <d_zj>]``

    Warning:
        - The local z-axis orientation vector `vecxz` cannot have a zero magnitude.

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        transf3d = model.transformation.transformation3d(
            transf_type="Linear",
            vecxz_x=0.0,
            vecxz_y=0.0,
            vecxz_z=1.0,
            d_xi=0.1,
            d_yj=0.05,
        )
        print(transf3d.tag)
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__", "has_joint_offsets"],
    }

    def __init__(
        self,
        transf_type: str,
        vecxz_x: float | str,
        vecxz_y: float | str,
        vecxz_z: float | str,
        d_xi: float | str = 0.0,
        d_yi: float | str = 0.0,
        d_zi: float | str = 0.0,
        d_xj: float | str = 0.0,
        d_yj: float | str = 0.0,
        d_zj: float | str = 0.0,
        description: str = "",
    ):
        """Create a 3D geometric transformation.

        Args:
            transf_type: Type of geometric transformation (e.g., 'Linear',
                'PDelta', 'Corotational').
            vecxz_x: X-component of a vector in the global coordinate system that
                defines the local x-z plane.
            vecxz_y: Y-component of the local z-orientation vector.
            vecxz_z: Z-component of the local z-orientation vector.
            d_xi: Joint offset in the local x-direction at start node I.
            d_yi: Joint offset in the local y-direction at start node I.
            d_zi: Joint offset in the local z-direction at start node I.
            d_xj: Joint offset in the local x-direction at end node J.
            d_yj: Joint offset in the local y-direction at end node J.
            d_zj: Joint offset in the local z-direction at end node J.
            description: Optional description for the transformation.

        Raises:
            ValueError: If the `vecxz` vector components define a zero-magnitude vector.
        """
        super().__init__(transf_type, 3, description=description)
        self.vecxz_x = float(vecxz_x)
        self.vecxz_y = float(vecxz_y)
        self.vecxz_z = float(vecxz_z)
        self.d_xi = float(d_xi)
        self.d_yi = float(d_yi)
        self.d_zi = float(d_zi)
        self.d_xj = float(d_xj)
        self.d_yj = float(d_yj)
        self.d_zj = float(d_zj)

        mag = math.sqrt(self.vecxz_x**2 + self.vecxz_y**2 + self.vecxz_z**2)
        if mag < self.eps:
            raise ValueError("vecxz vector cannot be zero")

    def has_joint_offsets(self) -> bool:
        """Check if the transformation has non-zero joint offsets.

        Returns:
            True if any joint offset exceeds `self.eps` in absolute magnitude,
            False otherwise.
        """
        offsets = [self.d_xi, self.d_yi, self.d_zi, self.d_xj, self.d_yj, self.d_zj]
        return any(abs(val) > self.eps for val in offsets)

    def to_tcl(self) -> str:
        """Render this 3D geometric transformation as an OpenSees Tcl command.

        Returns:
            The Tcl command string.
        """
        cmd = (
            f"geomTransf {self.transformation_type} {self._require_tag()} "
            f"{self.vecxz_x} {self.vecxz_y} {self.vecxz_z}"
        )
        if self.has_joint_offsets():
            cmd += f" -jntOffset {self.d_xi} {self.d_yi} {self.d_zi} {self.d_xj} {self.d_yj} {self.d_zj}"
        if self.description != "":
            cmd += f"; # {self.description}"
        return cmd


__all__ = [
    "GeometricTransformation",
    "GeometricTransformation2D",
    "GeometricTransformation3D",
]