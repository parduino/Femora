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

    This class defines how beam-column elements transform nodal displacements and
    forces between local and global coordinate systems in a 2D analysis. It supports
    various transformation types (e.g., 'Linear', 'PDelta', 'Corotational') and
    optional joint offsets at the element's start and end nodes.

    Tcl form:
        ``geomTransf <transf_type> <tag> [-jntOffset <d_xi> <d_yi> <d_xj> <d_yj>]``

    Attributes:
        tag: Manager-assigned identifier after the object is added to a Femora
            manager.
        transformation_type: The type of geometric transformation (e.g., 'Linear').
        ndm: The number of dimensions for the transformation (always 2 for this class).
        description: An optional description string for the transformation.

    Examples:
        ```python
        import femora as fm

        model = fm.MeshMaker()
        transf2d_linear = model.transformation.geometric_2d(transf_type="Linear")
        print(transf2d_linear.tag)

        transf2d_pdelta = model.transformation.geometric_2d(
            transf_type="PDelta", d_xi=0.1, d_yi=0.05, description="P-Delta with offsets"
        )
        print(transf2d_pdelta.to_tcl())
        ```
    """

    def __init__(
        self,
        transf_type: str,
        d_xi: float | str = 0.0,
        d_yi: float | str = 0.0,
        d_xj: float | str = 0.0,
        d_yj: float | str = 0.0,
        description: str = "",
    ):
        """Create a 2D geometric transformation object.

        Args:
            transf_type: The type of geometric transformation (e.g., 'Linear',
                'PDelta', 'Corotational').
            d_xi: Offset in the x-direction at the 'i' node (start node).
            d_yi: Offset in the y-direction at the 'i' node (start node).
            d_xj: Offset in the x-direction at the 'j' node (end node).
            d_yj: Offset in the y-direction at the 'j' node (end node).
            description: An optional description for the transformation.
        """
        super().__init__(transf_type, 2, description=description)
        self.d_xi = float(d_xi)
        self.d_yi = float(d_yi)
        self.d_xj = float(d_xj)
        self.d_yj = float(d_yj)

    def has_joint_offsets(self) -> bool:
        """Checks if any joint offset is non-zero.

        Returns:
            True if any `d_xi`, `d_yi`, `d_xj`, or `d_yj` is numerically
            greater than zero, False otherwise.
        """
        return any(abs(val) > self.eps for val in [self.d_xi, self.d_yi, self.d_xj, self.d_yj])

    def to_tcl(self) -> str:
        """Renders this 2D geometric transformation as an OpenSees Tcl command.

        Returns:
            The Tcl command string for this 2D transformation.
        """
        cmd = f"geomTransf {self.transformation_type} {self._require_tag()}"
        if self.has_joint_offsets():
            cmd += f" -jntOffset {self.d_xi} {self.d_yi} {self.d_xj} {self.d_yj}"
        if self.description != "":
            cmd += f"; # {self.description}"
        return cmd


class GeometricTransformation3D(GeometricTransformation):
    """Represents a 3D geometric transformation for OpenSees beam-column elements.

    This class defines how beam-column elements transform nodal displacements and
    forces between local and global coordinate systems in a 3D analysis. It requires
    a `vecxz` vector to define the local x-z plane of the element and supports
    various transformation types (e.g., 'Linear', 'PDelta', 'Corotational')
    along with optional joint offsets.

    Tcl form:
        ``geomTransf <transf_type> <tag> <vecxz_x> <vecxz_y> <vecxz_z> [-jntOffset <d_xi> <d_yi> <d_zi> <d_xj> <d_yj> <d_zj>]``

    Attributes:
        tag: Manager-assigned identifier after the object is added to a Femora
            manager.
        transformation_type: The type of geometric transformation (e.g., 'Linear').
        ndm: The number of dimensions for the transformation (always 3 for this class).
        description: An optional description string for the transformation.

    Examples:
        ```python
        import femora as fm

        model = fm.MeshMaker()
        transf3d_linear = model.transformation.geometric_3d(
            transf_type="Linear", vecxz_x=0.0, vecxz_y=0.0, vecxz_z=1.0
        )
        print(transf3d_linear.tag)

        transf3d_pdelta = model.transformation.geometric_3d(
            transf_type="PDelta",
            vecxz_x=0.0, vecxz_y=1.0, vecxz_z=0.0,
            d_xi=0.1, d_yi=0.05, d_zi=0.0,
            description="3D P-Delta with Y-axis as local Z"
        )
        print(transf3d_pdelta.to_tcl())
        ```
    """

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
        """Create a 3D geometric transformation object.

        Args:
            transf_type: The type of geometric transformation (e.g., 'Linear',
                'PDelta', 'Corotational').
            vecxz_x: The x-component of a vector in the global XZ-plane that defines
                the local x-z plane for the element.
            vecxz_y: The y-component of a vector in the global XZ-plane that defines
                the local x-z plane for the element.
            vecxz_z: The z-component of a vector in the global XZ-plane that defines
                the local x-z plane for the element.
            d_xi: Offset in the x-direction at the 'i' node (start node).
            d_yi: Offset in the y-direction at the 'i' node (start node).
            d_zi: Offset in the z-direction at the 'i' node (start node).
            d_xj: Offset in the x-direction at the 'j' node (end node).
            d_yj: Offset in the y-direction at the 'j' node (end node).
            d_zj: Offset in the z-direction at the 'j' node (end node).
            description: An optional description for the transformation.

        Raises:
            ValueError: If the `vecxz` vector components result in a zero-magnitude vector.
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
        """Checks if any joint offset is non-zero.

        Returns:
            True if any `d_xi`, `d_yi`, `d_zi`, `d_xj`, `d_yj`, or `d_zj` is
            numerically greater than zero, False otherwise.
        """
        offsets = [self.d_xi, self.d_yi, self.d_zi, self.d_xj, self.d_yj, self.d_zj]
        return any(abs(val) > self.eps for val in offsets)

    def to_tcl(self) -> str:
        """Renders this 3D geometric transformation as an OpenSees Tcl command.

        Returns:
            The Tcl command string for this 3D transformation.
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