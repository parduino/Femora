# =============================================================================
# Femora: Fast Efficient Meta-modeling for OpenSees-based Resilience Analysis
# Copyright 2026 Amin Pakzad and Pedro Arduino
# Developed at the UW Geotechnical Lab
# SPDX-License-Identifier: Apache-2.0
# =============================================================================

from typing import List

from femora.core.constraint_base import SPConstraint

# Ensure this module is part of the Constraint package
__all__ = [
    "SPConstraint",
    "FixConstraint",
    "FixXConstraint",
    "FixYConstraint",
    "FixZConstraint",
    "FixMacroX_max",
    "FixMacroX_min",
    "FixMacroY_max",
    "FixMacroY_min",
    "FixMacroZ_max",
    "FixMacroZ_min",
]


class FixConstraint(SPConstraint):
    """Single-point nodal boundary constraint.

    FixConstraint constrains selected degrees of freedom (DOFs) of a single node.
    It is the fundamental boundary condition component in finite element analysis.

    Tcl form:
        ``fix <nodeTag> <dof1> <dof2> ...``

    Note:
        - The DOFs list must contain only 0 (unconstrained) or 1 (constrained).
        - The length of the `dofs` list must match the node's local number of DOFs (NDF).

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        # Fix all 3 DOFs (X, Y, and rotation Z) of node 1
        constraint = model.constraint.sp.fix(
            node_tag=1,
            dofs=[1, 1, 1],
        )
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

    def __init__(self, node_tag: int, dofs: List[int]):
        """Create a single-node boundary constraint.

        Args:
            node_tag: Tag of the node to be fixed.
            dofs: List of DOF constraint states.
                0 indicates unconstrained (free).
                1 indicates constrained (fixed).
        """
        super().__init__(node_tag, dofs)

    def to_tcl(self) -> str:
        """Convert this constraint to an OpenSees TCL command.

        Returns:
            The OpenSees fix command string.
        """
        return f"fix {self.node_tag} {' '.join(map(str, self.dofs))};"


class FixXConstraint(SPConstraint):
    """Coordinate-based boundary constraint along a constant X plane.

    FixXConstraint constrains selected degrees of freedom for all nodes sharing
    a specific X coordinate within a given tolerance. It applies boundary conditions
    to planar boundaries in 2D or 3D models without requiring manual node tag lookup.

    Tcl form:
        ``fixX <xCoordinate> <dof1> <dof2> ... -tol <tol>``

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        # Fix X and Y DOFs of all nodes on the X=0.0 plane
        constraint = model.constraint.sp.fix_x(
            xCoordinate=0.0,
            dofs=[1, 1, 0],
            tol=1e-5,
        )
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

    def __init__(self, xCoordinate: float, dofs: List[int], tol: float = 1e-10):
        """Create an X-coordinate plane constraint.

        Args:
            xCoordinate: X-coordinate of nodes to be constrained.
            dofs: List of DOF constraint states.
                0 indicates unconstrained (free).
                1 indicates constrained (fixed).
            tol: Tolerance for coordinate comparison.
        """
        # Use -1 as a placeholder for node tag since it applies to multiple nodes
        super().__init__(-1, dofs)
        self.xCoordinate = xCoordinate
        self.tol = tol

    def to_tcl(self) -> str:
        """Convert this constraint to an OpenSees TCL command.

        Returns:
            The OpenSees fixX command string.
        """
        return f"fixX {self.xCoordinate} {' '.join(map(str, self.dofs))} -tol {self.tol};"


class FixYConstraint(SPConstraint):
    """Coordinate-based boundary constraint along a constant Y plane.

    FixYConstraint constrains selected degrees of freedom for all nodes sharing
    a specific Y coordinate within a given tolerance. It applies boundary conditions
    to planar boundaries in 2D or 3D models without requiring manual node tag lookup.

    Tcl form:
        ``fixY <yCoordinate> <dof1> <dof2> ... -tol <tol>``

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        # Fix Y DOF of all nodes on the Y=0.0 plane
        constraint = model.constraint.sp.fix_y(
            yCoordinate=0.0,
            dofs=[0, 1, 0],
            tol=1e-5,
        )
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

    def __init__(self, yCoordinate: float, dofs: List[int], tol: float = 1e-10):
        """Create a Y-coordinate plane constraint.

        Args:
            yCoordinate: Y-coordinate of nodes to be constrained.
            dofs: List of DOF constraint states.
                0 indicates unconstrained (free).
                1 indicates constrained (fixed).
            tol: Tolerance for coordinate comparison.
        """
        # Use -1 as a placeholder for node tag since it applies to multiple nodes
        super().__init__(-1, dofs)
        self.yCoordinate = yCoordinate
        self.tol = tol

    def to_tcl(self) -> str:
        """Convert this constraint to an OpenSees TCL command.

        Returns:
            The OpenSees fixY command string.
        """
        return f"fixY {self.yCoordinate} {' '.join(map(str, self.dofs))} -tol {self.tol};"


class FixZConstraint(SPConstraint):
    """Coordinate-based boundary constraint along a constant Z plane.

    FixZConstraint constrains selected degrees of freedom for all nodes sharing
    a specific Z coordinate within a given tolerance. It applies boundary conditions
    to planar boundaries in 3D models without requiring manual node tag lookup.

    Tcl form:
        ``fixZ <zCoordinate> <dof1> <dof2> ... -tol <tol>``

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        # Fix Z DOF of all nodes on the Z=0.0 plane
        constraint = model.constraint.sp.fix_z(
            zCoordinate=0.0,
            dofs=[0, 0, 1],
            tol=1e-5,
        )
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

    def __init__(self, zCoordinate: float, dofs: List[int], tol: float = 1e-10):
        """Create a Z-coordinate plane constraint.

        Args:
            zCoordinate: Z-coordinate of nodes to be constrained.
            dofs: List of DOF constraint states.
                0 indicates unconstrained (free).
                1 indicates constrained (fixed).
            tol: Tolerance for coordinate comparison.
        """
        # Use -1 as a placeholder for node tag since it applies to multiple nodes
        super().__init__(-1, dofs)
        self.zCoordinate = zCoordinate
        self.tol = tol

    def to_tcl(self) -> str:
        """Convert this constraint to an OpenSees TCL command.

        Returns:
            The OpenSees fixZ command string.
        """
        return f"fixZ {self.zCoordinate} {' '.join(map(str, self.dofs))} -tol {self.tol};"


class FixMacroX_max(SPConstraint):
    """Boundary constraint at the maximum X-coordinate macro boundary.

    FixMacroX_max constrains selected degrees of freedom for all nodes sharing
    the maximum X coordinate of the model. The boundary coordinate is defined
    using the global TCL variable `$X_MAX`.

    Tcl form:
        ``fixX $X_MAX <dof1> <dof2> ... -tol <tol>``

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        # Fix X and Y DOFs of all nodes at the maximum X macro boundary
        constraint = model.constraint.sp.fix_macro_x_max(
            dofs=[1, 1, 0],
            tol=1e-5,
        )
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

    def __init__(self, dofs: List[int], tol: float = 1e-10):
        """Create a maximum X macro boundary constraint.

        Args:
            dofs: List of DOF constraint states.
                0 indicates unconstrained (free).
                1 indicates constrained (fixed).
            tol: Tolerance for coordinate comparison.
        """
        # Use -1 as a placeholder for node tag since it applies to multiple nodes
        super().__init__(-1, dofs)
        self.tol = tol

    def to_tcl(self) -> str:
        """Convert this constraint to an OpenSees TCL command.

        Returns:
            The OpenSees fixX maximum boundary command string.
        """
        return f"fixX $X_MAX {' '.join(map(str, self.dofs))} -tol {self.tol};"


class FixMacroY_max(SPConstraint):
    """Boundary constraint at the maximum Y-coordinate macro boundary.

    FixMacroY_max constrains selected degrees of freedom for all nodes sharing
    the maximum Y coordinate of the model. The boundary coordinate is defined
    using the global TCL variable `$Y_MAX`.

    Tcl form:
        ``fixY $Y_MAX <dof1> <dof2> ... -tol <tol>``

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        # Fix Y DOF of all nodes at the maximum Y macro boundary
        constraint = model.constraint.sp.fix_macro_y_max(
            dofs=[0, 1, 0],
            tol=1e-5,
        )
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

    def __init__(self, dofs: List[int], tol: float = 1e-10):
        """Create a maximum Y macro boundary constraint.

        Args:
            dofs: List of DOF constraint states.
                0 indicates unconstrained (free).
                1 indicates constrained (fixed).
            tol: Tolerance for coordinate comparison.
        """
        # Use -1 as a placeholder for node tag since it applies to multiple nodes
        super().__init__(-1, dofs)
        self.tol = tol

    def to_tcl(self) -> str:
        """Convert this constraint to an OpenSees TCL command.

        Returns:
            The OpenSees fixY maximum boundary command string.
        """
        return f"fixY $Y_MAX {' '.join(map(str, self.dofs))} -tol {self.tol};"


class FixMacroZ_max(SPConstraint):
    """Boundary constraint at the maximum Z-coordinate macro boundary.

    FixMacroZ_max constrains selected degrees of freedom for all nodes sharing
    the maximum Z coordinate of the model. The boundary coordinate is defined
    using the global TCL variable `$Z_MAX`.

    Tcl form:
        ``fixZ $Z_MAX <dof1> <dof2> ... -tol <tol>``

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        # Fix Z DOF of all nodes at the maximum Z macro boundary
        constraint = model.constraint.sp.fix_macro_z_max(
            dofs=[0, 0, 1],
            tol=1e-5,
        )
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

    def __init__(self, dofs: List[int], tol: float = 1e-10):
        """Create a maximum Z macro boundary constraint.

        Args:
            dofs: List of DOF constraint states.
                0 indicates unconstrained (free).
                1 indicates constrained (fixed).
            tol: Tolerance for coordinate comparison.
        """
        # Use -1 as a placeholder for node tag since it applies to multiple nodes
        super().__init__(-1, dofs)
        self.tol = tol

    def to_tcl(self) -> str:
        """Convert this constraint to an OpenSees TCL command.

        Returns:
            The OpenSees fixZ maximum boundary command string.
        """
        return f"fixZ $Z_MAX {' '.join(map(str, self.dofs))} -tol {self.tol};"


class FixMacroX_min(SPConstraint):
    """Boundary constraint at the minimum X-coordinate macro boundary.

    FixMacroX_min constrains selected degrees of freedom for all nodes sharing
    the minimum X coordinate of the model. The boundary coordinate is defined
    using the global TCL variable `$X_MIN`.

    Tcl form:
        ``fixX $X_MIN <dof1> <dof2> ... -tol <tol>``

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        # Fix X and Y DOFs of all nodes at the minimum X macro boundary
        constraint = model.constraint.sp.fix_macro_x_min(
            dofs=[1, 1, 0],
            tol=1e-5,
        )
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

    def __init__(self, dofs: List[int], tol: float = 1e-10):
        """Create a minimum X macro boundary constraint.

        Args:
            dofs: List of DOF constraint states.
                0 indicates unconstrained (free).
                1 indicates constrained (fixed).
            tol: Tolerance for coordinate comparison.
        """
        # Use -1 as a placeholder for node tag since it applies to multiple nodes
        super().__init__(-1, dofs)
        self.tol = tol

    def to_tcl(self) -> str:
        """Convert this constraint to an OpenSees TCL command.

        Returns:
            The OpenSees fixX minimum boundary command string.
        """
        return f"fixX $X_MIN {' '.join(map(str, self.dofs))} -tol {self.tol};"


class FixMacroY_min(SPConstraint):
    """Boundary constraint at the minimum Y-coordinate macro boundary.

    FixMacroY_min constrains selected degrees of freedom for all nodes sharing
    the minimum Y coordinate of the model. The boundary coordinate is defined
    using the global TCL variable `$Y_MIN`.

    Tcl form:
        ``fixY $Y_MIN <dof1> <dof2> ... -tol <tol>``

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        # Fix Y DOF of all nodes at the minimum Y macro boundary
        constraint = model.constraint.sp.fix_macro_y_min(
            dofs=[0, 1, 0],
            tol=1e-5,
        )
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

    def __init__(self, dofs: List[int], tol: float = 1e-10):
        """Create a minimum Y macro boundary constraint.

        Args:
            dofs: List of DOF constraint states.
                0 indicates unconstrained (free).
                1 indicates constrained (fixed).
            tol: Tolerance for coordinate comparison.
        """
        # Use -1 as a placeholder for node tag since it applies to multiple nodes
        super().__init__(-1, dofs)
        self.tol = tol

    def to_tcl(self) -> str:
        """Convert this constraint to an OpenSees TCL command.

        Returns:
            The OpenSees fixY minimum boundary command string.
        """
        return f"fixY $Y_MIN {' '.join(map(str, self.dofs))} -tol {self.tol};"


class FixMacroZ_min(SPConstraint):
    """Boundary constraint at the minimum Z-coordinate macro boundary.

    FixMacroZ_min constrains selected degrees of freedom for all nodes sharing
    the minimum Z coordinate of the model. The boundary coordinate is defined
    using the global TCL variable `$Z_MIN`.

    Tcl form:
        ``fixZ $Z_MIN <dof1> <dof2> ... -tol <tol>``

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        # Fix Z DOF of all nodes at the minimum Z macro boundary
        constraint = model.constraint.sp.fix_macro_z_min(
            dofs=[0, 0, 1],
            tol=1e-5,
        )
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

    def __init__(self, dofs: List[int], tol: float = 1e-10):
        """Create a minimum Z macro boundary constraint.

        Args:
            dofs: List of DOF constraint states.
                0 indicates unconstrained (free).
                1 indicates constrained (fixed).
            tol: Tolerance for coordinate comparison.

        Raises:
            ValueError: If DOFs are not elements of [0, 1].
        """
        # Use -1 as a placeholder for node tag since it applies to multiple nodes
        super().__init__(-1, dofs)
        # check if the dofs are 0 or 1
        if not all(dof in [0, 1] for dof in dofs):
            raise ValueError("DOFs must be 0 or 1")
        self.tol = tol

    def to_tcl(self) -> str:
        """Convert this constraint to an OpenSees TCL command.

        Returns:
            The OpenSees fixZ minimum boundary command string.
        """
        return f"fixZ $Z_MIN {' '.join(map(str, self.dofs))} -tol {self.tol};"
