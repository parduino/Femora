# =============================================================================
# Femora: Fast Efficient Meta-modeling for OpenSees-based Resilience Analysis
# Copyright 2026 Amin Pakzad and Pedro Arduino
# Developed at the UW Geotechnical Lab
# SPDX-License-Identifier: Apache-2.0
# =============================================================================

from typing import Optional

from femora.core.analysis.constraint_handler import ConstraintHandler


class PlainConstraintHandler(ConstraintHandler):
    """Plain constraint handler.

    PlainConstraintHandler enforces single-point boundary conditions (such as fix commands)
    and homogeneous multi-point constraints (such as equalDOF commands) in OpenSees,
    but does not handle non-homogeneous multi-point constraints dynamically during analysis evolution.

    Tcl form:
        ``constraints Plain``

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        handler = model.analysis.constraint.plain()
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

    def __init__(self):
        """Create a Plain constraint handler."""
        super().__init__("Plain")
    
    def to_tcl(self) -> str:
        """Render this constraint handler as an OpenSees Tcl command.

        Returns:
            The Tcl command string.
        """
        return "constraints Plain"
    


class TransformationConstraintHandler(ConstraintHandler):
    """Transformation constraint handler.

    TransformationConstraintHandler enforces both single-point and multi-point boundary
    conditions by performing static condensation of the constrained degrees of freedom,
    reducing the total number of equations in the system.

    Tcl form:
        ``constraints Transformation``

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        handler = model.analysis.constraint.transformation()
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

    def __init__(self):
        """Create a Transformation constraint handler."""
        super().__init__("Transformation")
    
    def to_tcl(self) -> str:
        """Render this constraint handler as an OpenSees Tcl command.

        Returns:
            The Tcl command string.
        """
        return "constraints Transformation"
    


class PenaltyConstraintHandler(ConstraintHandler):
    """Penalty-based constraint handler.

    PenaltyConstraintHandler enforces boundary constraints by adding very large stiffness
    (penalty numbers) along the constrained degrees of freedom, keeping the original size
    of the system matrix.

    Tcl form:
        ``constraints Penalty <alphaS> <alphaM>``

    Note:
        - Choosing penalty numbers too small can lead to constraint violations.
        - Choosing penalty numbers too large can result in numerical ill-conditioning.

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        handler = model.analysis.constraint.penalty(alpha_s=1e10, alpha_m=1e10)
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

    def __init__(self, alpha_s: float, alpha_m: float):
        """Create a Penalty constraint handler.

        Args:
            alpha_s: Penalty scale factor for single-point (SP) constraints.
            alpha_m: Penalty scale factor for multi-point (MP) constraints.
        """
        super().__init__("Penalty")
        self.alpha_s = alpha_s
        self.alpha_m = alpha_m
    
    def to_tcl(self) -> str:
        """Render this constraint handler as an OpenSees Tcl command.

        Returns:
            The Tcl command string.
        """
        return f"constraints Penalty {self.alpha_s} {self.alpha_m}"
    


class LagrangeConstraintHandler(ConstraintHandler):
    """Lagrange multipliers constraint handler.

    LagrangeConstraintHandler enforces constraints exactly by introducing new degrees
    of freedom (Lagrange multipliers) representing the constraint forces.

    Tcl form:
        ``constraints Lagrange [<alphaS> <alphaM>]``

    Note:
        - Introduces additional equations, which changes the size of the system matrix.
        - Can result in zero diagonal terms in the system matrix.

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        handler = model.analysis.constraint.lagrange(alpha_s=1.0, alpha_m=1.0)
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

    def __init__(self, alpha_s: float = 1.0, alpha_m: float = 1.0):
        """Create a Lagrange constraint handler.

        Args:
            alpha_s: Scaling factor for single-point constraints.
            alpha_m: Scaling factor for multi-point constraints.
        """
        super().__init__("Lagrange")
        self.alpha_s = alpha_s
        self.alpha_m = alpha_m
    
    def to_tcl(self) -> str:
        """Render this constraint handler as an OpenSees Tcl command.

        Returns:
            The Tcl command string.
        """
        return f"constraints Lagrange {self.alpha_s} {self.alpha_m}"
    


class AutoConstraintHandler(ConstraintHandler):
    """Automatic constraint handler.

    AutoConstraintHandler automatically selects appropriate penalty numbers for compatibility
    constraints based on the surrounding structural stiffness elements.

    Tcl form:
        ``constraints Auto [-verbose] [-autoPenalty <value>] [-userPenalty <value>]``

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        handler = model.analysis.constraint.auto(verbose=True, auto_penalty=1e8)
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

    def __init__(self, verbose: bool = False, auto_penalty: Optional[float] = None, 
                 user_penalty: Optional[float] = None):
        """Create an Auto constraint handler.

        Args:
            verbose: If True, outputs diagnostic selection steps.
            auto_penalty: Optional automatic penalty scaling value.
            user_penalty: Optional user override penalty value.
        """
        super().__init__("Auto")
        self.verbose = verbose
        self.auto_penalty = auto_penalty
        self.user_penalty = user_penalty
    
    def to_tcl(self) -> str:
        """Render this constraint handler as an OpenSees Tcl command.

        Returns:
            The Tcl command string.
        """
        cmd = "constraints Auto"
        if self.verbose:
            cmd += " -verbose"
        if self.auto_penalty is not None:
            cmd += f" -autoPenalty {self.auto_penalty}"
        if self.user_penalty is not None:
            cmd += f" -userPenalty {self.user_penalty}"
        return cmd
    


# Register all constraint handlers
ConstraintHandler.register_handler('plain', PlainConstraintHandler)
ConstraintHandler.register_handler('transformation', TransformationConstraintHandler)
ConstraintHandler.register_handler('penalty', PenaltyConstraintHandler)
ConstraintHandler.register_handler('lagrange', LagrangeConstraintHandler)
ConstraintHandler.register_handler('auto', AutoConstraintHandler)
