# =============================================================================
# Femora: Fast Efficient Meta-modeling for OpenSees-based Resilience Analysis
# Copyright 2026 Amin Pakzad and Pedro Arduino
# Developed at the UW Geotechnical Lab
# SPDX-License-Identifier: Apache-2.0
# =============================================================================

from typing import Optional

from femora.core.analysis.integrator import Integrator, StaticIntegrator, TransientIntegrator


#------------------------------------------------------
# Static Integrators
#------------------------------------------------------

class LoadControlIntegrator(StaticIntegrator):
    """Load control integrator for static analysis.

    LoadControlIntegrator increments the load factor at each step of a static
    analysis to determine structural response under a specified loading scenario.

    Tcl form:
        ``integrator LoadControl <incr> <numIter> <minIncr> <maxIncr>``

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        integ = model.analysis.integrator.loadcontrol(
            incr=0.1,
            num_iter=1,
            min_incr=0.01,
            max_incr=0.2,
        )
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

    def __init__(self, incr: float, num_iter: int = 1, min_incr: Optional[float] = None, 
                 max_incr: Optional[float] = None):
        """Create a LoadControl static integrator.

        Args:
            incr: Load factor increment size.
            num_iter: Desired number of iterations in the solution algorithm.
            min_incr: Minimum allowable load factor increment size. Defaults to `incr`.
            max_incr: Maximum allowable load factor increment size. Defaults to `incr`.
        """
        super().__init__("LoadControl")
        self.incr = incr
        self.num_iter = num_iter
        self.min_incr = min_incr if min_incr is not None else incr
        self.max_incr = max_incr if max_incr is not None else incr
    
    def to_tcl(self) -> str:
        """Render this integrator as an OpenSees Tcl command.

        Returns:
            The Tcl command string.
        """
        return f"integrator LoadControl {self.incr} {self.num_iter} {self.min_incr} {self.max_incr}"
    


class DisplacementControlIntegrator(StaticIntegrator):
    """Displacement control integrator for static analysis.

    DisplacementControlIntegrator increments a specific degree of freedom at a
    target node to control the static simulation. This is especially useful for
    capturing softening behavior.

    Tcl form:
        ``integrator DisplacementControl <nodeTag> <dof> <incr> <numIter> <minIncr> <maxIncr>``

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        integ = model.analysis.integrator.displacementcontrol(
            node_tag=1,
            dof=1,
            incr=0.01,
            num_iter=1,
            min_incr=0.001,
            max_incr=0.1,
        )
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

    def __init__(self, node_tag: int, dof: int, incr: float, num_iter: int = 1, 
                 min_incr: Optional[float] = None, max_incr: Optional[float] = None):
        """Create a DisplacementControl static integrator.

        Args:
            node_tag: ID tag of the controlling node.
            dof: Degree of freedom (1-indexed) at the node that controls response.
            incr: Initial displacement increment.
            num_iter: Desired number of iterations in the solution algorithm.
            min_incr: Minimum allowable displacement increment. Defaults to `incr`.
            max_incr: Maximum allowable displacement increment. Defaults to `incr`.
        """
        super().__init__("DisplacementControl")
        self.node_tag = node_tag
        self.dof = dof
        self.incr = incr
        self.num_iter = num_iter
        self.min_incr = min_incr if min_incr is not None else incr
        self.max_incr = max_incr if max_incr is not None else incr
    
    def to_tcl(self) -> str:
        """Render this integrator as an OpenSees Tcl command.

        Returns:
            The Tcl command string.
        """
        return f"integrator DisplacementControl {self.node_tag} {self.dof} {self.incr} {self.num_iter} {self.min_incr} {self.max_incr}"
    


class ParallelDisplacementControlIntegrator(StaticIntegrator):
    """Parallel displacement control integrator for static analysis.

    ParallelDisplacementControlIntegrator is the parallel version of the displacement
    control integrator, suited for high-performance multiprocessor computations.

    Tcl form:
        ``integrator ParallelDisplacementControl <nodeTag> <dof> <incr> <numIter> <minIncr> <maxIncr>``

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        integ = model.analysis.integrator.paralleldisplacementcontrol(
            node_tag=1,
            dof=1,
            incr=0.01,
            num_iter=1,
            min_incr=0.001,
            max_incr=0.1,
        )
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

    def __init__(self, node_tag: int, dof: int, incr: float, num_iter: int = 1, 
                 min_incr: Optional[float] = None, max_incr: Optional[float] = None):
        """Create a ParallelDisplacementControl static integrator.

        Args:
            node_tag: ID tag of the controlling node.
            dof: Degree of freedom (1-indexed) at the node that controls response.
            incr: Initial displacement increment.
            num_iter: Desired number of iterations in the solution algorithm.
            min_incr: Minimum allowable displacement increment. Defaults to `incr`.
            max_incr: Maximum allowable displacement increment. Defaults to `incr`.
        """
        super().__init__("ParallelDisplacementControl")
        self.node_tag = node_tag
        self.dof = dof
        self.incr = incr
        self.num_iter = num_iter
        self.min_incr = min_incr if min_incr is not None else incr
        self.max_incr = max_incr if max_incr is not None else incr
    
    def to_tcl(self) -> str:
        """Render this integrator as an OpenSees Tcl command.

        Returns:
            The Tcl command string.
        """
        return f"integrator ParallelDisplacementControl {self.node_tag} {self.dof} {self.incr} {self.num_iter} {self.min_incr} {self.max_incr}"
    


class MinUnbalDispNormIntegrator(StaticIntegrator):
    """Minimum unbalanced displacement norm static integrator.

    MinUnbalDispNormIntegrator selects load increments such that the norm of the
    unbalanced displacement vector is minimized at the end of each step.

    Tcl form:
        ``integrator MinUnbalDispNorm <dlambda1> <jd> <minLambda> <maxLambda> [-det]``

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        integ = model.analysis.integrator.minunbaldispnorm(
            dlambda1=0.1,
            jd=1,
            min_lambda=0.01,
            max_lambda=0.2,
            det=True,
        )
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

    def __init__(self, dlambda1: float, jd: int = 1, min_lambda: Optional[float] = None, 
                 max_lambda: Optional[float] = None, det: bool = False):
        """Create a MinUnbalDispNorm static integrator.

        Args:
            dlambda1: First load increment size.
            jd: Desired number of iterations per step.
            min_lambda: Minimum allowable load increment size. Defaults to `dlambda1`.
            max_lambda: Maximum allowable load increment size. Defaults to `dlambda1`.
            det: If True, uses the determinant of the tangent matrix for step sizing.
        """
        super().__init__("MinUnbalDispNorm")
        self.dlambda1 = dlambda1
        self.jd = jd
        self.min_lambda = min_lambda if min_lambda is not None else dlambda1
        self.max_lambda = max_lambda if max_lambda is not None else dlambda1
        self.det = det
    
    def to_tcl(self) -> str:
        """Render this integrator as an OpenSees Tcl command.

        Returns:
            The Tcl command string.
        """
        det_str = " -det" if self.det else ""
        return f"integrator MinUnbalDispNorm {self.dlambda1} {self.jd} {self.min_lambda} {self.max_lambda}{det_str}"
    


class ArcLengthIntegrator(StaticIntegrator):
    """Arc-length control static integrator.

    ArcLengthIntegrator uses the arc-length method to trace equilibrium paths that
    exhibit limit points, snap-through, or snap-back behaviors.

    Tcl form:
        ``integrator ArcLength <s> <alpha>``

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        integ = model.analysis.integrator.arclength(s=0.1, alpha=1.0)
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

    def __init__(self, s: float, alpha: float):
        """Create an ArcLength static integrator.

        Args:
            s: The arc-length parameter constraint.
            alpha: Scaling parameter on the reference load vector.
        """
        super().__init__("ArcLength")
        self.s = s
        self.alpha = alpha
    
    def to_tcl(self) -> str:
        """Render this integrator as an OpenSees Tcl command.

        Returns:
            The Tcl command string.
        """
        return f"integrator ArcLength {self.s} {self.alpha}"
    


#------------------------------------------------------
# Transient Integrators
#------------------------------------------------------

class CentralDifferenceIntegrator(TransientIntegrator):
    """Central difference transient integrator.

    CentralDifferenceIntegrator performs explicit time integration using the
    central difference scheme for dynamic transient simulations.

    Warning:
        CentralDifference is an explicit integration method and is only
        conditionally stable. Ensure your time step is below the critical limit.

    Tcl form:
        ``integrator CentralDifference``

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        integ = model.analysis.integrator.centraldifference()
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

    def __init__(self):
        """Create a CentralDifference transient integrator."""
        super().__init__("CentralDifference")
    
    def to_tcl(self) -> str:
        """Render this integrator as an OpenSees Tcl command.

        Returns:
            The Tcl command string.
        """
        return "integrator CentralDifference"
    


class NewmarkIntegrator(TransientIntegrator):
    """Newmark method transient integrator.

    NewmarkIntegrator implements the classical Newmark-beta implicit method for
    second-order structural dynamic time-history equations.

    Tcl form:
        ``integrator Newmark <gamma> <beta> [-form <D|V|A>]``

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        integ = model.analysis.integrator.newmark(gamma=0.5, beta=0.25, form="D")
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

    def __init__(self, gamma: float, beta: float, form: str = "D"):
        """Create a Newmark transient integrator.

        Args:
            gamma: Gamma dynamic integration parameter.
            beta: Beta dynamic integration parameter.
            form: Primary formulation variable. 'D' for displacement (default),
                'V' for velocity, or 'A' for acceleration.

        Raises:
            ValueError: If form is not 'D', 'V', or 'A'.
        """
        super().__init__("Newmark")
        self.gamma = gamma
        self.beta = beta
        if form not in ["D", "V", "A"]:
            raise ValueError("form must be one of 'D', 'V', or 'A'")
        self.form = form
    
    def to_tcl(self) -> str:
        """Render this integrator as an OpenSees Tcl command.

        Returns:
            The Tcl command string.
        """
        if self.form == "D":
            return f"integrator Newmark {self.gamma} {self.beta}"
        else:
            return f"integrator Newmark {self.gamma} {self.beta} -form {self.form}"
    


class HHTIntegrator(TransientIntegrator):
    """Hilber-Hughes-Taylor transient integrator.

    HHTIntegrator implements the Hilber-Hughes-Taylor (alpha-method) implicit scheme
    for dynamics, introducing numerical damping for high-frequency modes while
    retaining second-order accuracy.

    Tcl form:
        ``integrator HHT <alpha> <gamma> <beta>``

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        integ = model.analysis.integrator.hht(alpha=0.67)
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

    def __init__(self, alpha: float, gamma: Optional[float] = None, beta: Optional[float] = None):
        """Create an HHT transient integrator.

        Args:
            alpha: Alpha integration parameter.
            gamma: Gamma integration parameter. Defaults to `1.5 - alpha`.
            beta: Beta integration parameter. Defaults to `(2 - alpha)**2 / 4`.
        """
        super().__init__("HHT")
        self.alpha = alpha
        # Default values if not provided
        if gamma is None:
            self.gamma = 1.5 - alpha
        else:
            self.gamma = gamma
            
        if beta is None:
            self.beta = ((2.0 - alpha) ** 2) / 4.0
        else:
            self.beta = beta
    
    def to_tcl(self) -> str:
        """Render this integrator as an OpenSees Tcl command.

        Returns:
            The Tcl command string.
        """
        return f"integrator HHT {self.alpha} {self.gamma} {self.beta}"
    


class GeneralizedAlphaIntegrator(TransientIntegrator):
    """Generalized Alpha transient integrator.

    GeneralizedAlphaIntegrator implements the Generalized Alpha dynamic integration
    method, providing user-controlled high-frequency numerical dissipation while
    minimizing low-frequency dissipation.

    Tcl form:
        ``integrator GeneralizedAlpha <alphaM> <alphaF> <gamma> <beta>``

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        integ = model.analysis.integrator.generalizedalpha(alpha_m=0.5, alpha_f=0.5)
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

    def __init__(self, alpha_m: float, alpha_f: float, gamma: Optional[float] = None, 
                 beta: Optional[float] = None):
        """Create a GeneralizedAlpha transient integrator.

        Args:
            alpha_m: Alpha_M parameter.
            alpha_f: Alpha_F parameter.
            gamma: Gamma parameter. Defaults to `0.5 + alpha_m - alpha_f`.
            beta: Beta parameter. Defaults to `(1.0 + alpha_m - alpha_f)**2 / 4.0`.
        """
        super().__init__("GeneralizedAlpha")
        self.alpha_m = alpha_m
        self.alpha_f = alpha_f
        
        # Default values if not provided
        if gamma is None:
            self.gamma = 0.5 + alpha_m - alpha_f
        else:
            self.gamma = gamma
            
        if beta is None:
            self.beta = ((1.0 + alpha_m - alpha_f) ** 2) / 4.0
        else:
            self.beta = beta
    
    def to_tcl(self) -> str:
        """Render this integrator as an OpenSees Tcl command.

        Returns:
            The Tcl command string.
        """
        return f"integrator GeneralizedAlpha {self.alpha_m} {self.alpha_f} {self.gamma} {self.beta}"
    


class TRBDF2Integrator(TransientIntegrator):
    """TRBDF2 transient integrator.

    TRBDF2Integrator uses a composite single-step implicit integration method
    combining the Trapezoidal Rule and the Backward Differentiation Formula of order 2.

    Tcl form:
        ``integrator TRBDF2``

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        integ = model.analysis.integrator.trbdf2()
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

    def __init__(self):
        """Create a TRBDF2 transient integrator."""
        super().__init__("TRBDF2")
    
    def to_tcl(self) -> str:
        """Render this integrator as an OpenSees Tcl command.

        Returns:
            The Tcl command string.
        """
        return "integrator TRBDF2"
    


class ExplicitDifferenceIntegrator(TransientIntegrator):
    """Explicit difference transient integrator.

    ExplicitDifferenceIntegrator implements explicit dynamic difference equations
    for solving transient response without factoring equations.

    Warning:
        This explicit scheme is conditionally stable and requires small time
        steps to maintain stability.

    Tcl form:
        ``integrator ExplicitDifference``

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        integ = model.analysis.integrator.explicitdifference()
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

    def __init__(self):
        """Create an ExplicitDifference transient integrator."""
        super().__init__("ExplicitDifference")
    
    def to_tcl(self) -> str:
        """Render this integrator as an OpenSees Tcl command.

        Returns:
            The Tcl command string.
        """
        return "integrator ExplicitDifference"
    


class PFEMIntegrator(TransientIntegrator):
    """Particle Finite Element Method (PFEM) fluid-structure transient integrator.

    PFEMIntegrator is designed for coupling fluid and structural dynamic solver
    matrices in particle-based finite element modeling.

    Tcl form:
        ``integrator PFEM <gamma> <beta>``

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        integ = model.analysis.integrator.pfem(gamma=0.5, beta=0.25)
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

    def __init__(self, gamma: float = 0.5, beta: float = 0.25):
        """Create a PFEM fluid-structure transient integrator.

        Args:
            gamma: Gamma integration parameter. Defaults to 0.5.
            beta: Beta integration parameter. Defaults to 0.25.
        """
        super().__init__("PFEM")
        self.gamma = gamma
        self.beta = beta
    
    def to_tcl(self) -> str:
        """Render this integrator as an OpenSees Tcl command.

        Returns:
            The Tcl command string.
        """
        return f"integrator PFEM {self.gamma} {self.beta}"
    


# Register all integrators
Integrator.register_integrator('loadcontrol', LoadControlIntegrator)
Integrator.register_integrator('displacementcontrol', DisplacementControlIntegrator)
Integrator.register_integrator('paralleldisplacementcontrol', ParallelDisplacementControlIntegrator)
Integrator.register_integrator('minunbaldispnorm', MinUnbalDispNormIntegrator)
Integrator.register_integrator('arclength', ArcLengthIntegrator)
Integrator.register_integrator('centraldifference', CentralDifferenceIntegrator)
Integrator.register_integrator('newmark', NewmarkIntegrator)
Integrator.register_integrator('hht', HHTIntegrator)
Integrator.register_integrator('generalizedalpha', GeneralizedAlphaIntegrator)
Integrator.register_integrator('trbdf2', TRBDF2Integrator)
Integrator.register_integrator('explicitdifference', ExplicitDifferenceIntegrator)
Integrator.register_integrator('pfem', PFEMIntegrator)
