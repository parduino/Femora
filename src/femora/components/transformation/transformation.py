"""Concrete OpenSees geometric transformation classes.

Concrete transformations are plain runtime objects. They do not self-register
and their ``tag`` remains ``None`` until a
``femora.core.transformation_manager.TransformationManager`` owns them.
"""

from __future__ import annotations

import math

from femora.core.transformation_base import GeometricTransformation


class GeometricTransformation2D(GeometricTransformation):
    """2D geometric transformation for OpenSees beam-column elements."""

    def __init__(
        self,
        transf_type: str,
        d_xi: float | str = 0.0,
        d_yi: float | str = 0.0,
        d_xj: float | str = 0.0,
        d_yj: float | str = 0.0,
        description: str = "",
    ):
        super().__init__(transf_type, 2, description=description)
        self.d_xi = float(d_xi)
        self.d_yi = float(d_yi)
        self.d_xj = float(d_xj)
        self.d_yj = float(d_yj)

    def has_joint_offsets(self) -> bool:
        """Return whether any joint offset is nonzero."""
        return any(abs(val) > self.eps for val in [self.d_xi, self.d_yi, self.d_xj, self.d_yj])

    def to_tcl(self) -> str:
        """Generate the Tcl command for this 2D transformation."""
        cmd = f"geomTransf {self.transformation_type} {self._require_tag()}"
        if self.has_joint_offsets():
            cmd += f" -jntOffset {self.d_xi} {self.d_yi} {self.d_xj} {self.d_yj}"
        if self.description != "":
            cmd += f"; # {self.description}"
        return cmd


class GeometricTransformation3D(GeometricTransformation):
    """3D geometric transformation for OpenSees beam-column elements."""

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
        """Return whether any joint offset is nonzero."""
        offsets = [self.d_xi, self.d_yi, self.d_zi, self.d_xj, self.d_yj, self.d_zj]
        return any(abs(val) > self.eps for val in offsets)

    def to_tcl(self) -> str:
        """Generate the Tcl command for this 3D transformation."""
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
