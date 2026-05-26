from typing import Dict, List, Type, Union

from femora.core.tagged_component_manager import TaggedComponentManager
from femora.core.analysis_component_base import AnalysisComponent


class Algorithm(AnalysisComponent):
    """Base class for OpenSees solution algorithms."""

    _algorithms: Dict[str, Type["Algorithm"]] = {}

    def __init__(self, algorithm_type: str) -> None:
        super().__init__()
        self.algorithm_type = algorithm_type

    @staticmethod
    def register_algorithm(name: str, algorithm_class: Type["Algorithm"]) -> None:
        Algorithm._algorithms[name.lower()] = algorithm_class


class LinearAlgorithm(Algorithm):
    """Linear solution algorithm for solving linear equations in one iteration.

    LinearAlgorithm is used in linear static or transient analyses where
    the stiffness matrix does not change during the step.

    Tcl form:
        ``algorithm Linear [-initial] [-factorOnce]``

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        algo = model.analysis.algorithm.linear(initial=True)
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

    def __init__(self, initial: bool = False, factor_once: bool = False):
        """Create a Linear solution algorithm.

        Args:
            initial: If True, uses the initial structural stiffness matrix.
            factor_once: If True, sets up and factors the matrix only once.
        """
        super().__init__("Linear")
        self.initial = initial
        self.factor_once = factor_once
    
    def to_tcl(self) -> str:
        """Render this algorithm as an OpenSees Tcl command.

        Returns:
            The Tcl command string.
        """
        cmd = "algorithm Linear"
        if self.initial:
            cmd += " -initial"
        if self.factor_once:
            cmd += " -factorOnce"
        return cmd
    


class NewtonAlgorithm(Algorithm):
    """Newton-Raphson nonlinear solution algorithm.

    NewtonAlgorithm uses the classical Newton-Raphson iteration scheme to solve
    nonlinear equilibrium residual equations. It reforms the tangent stiffness
    matrix at every iteration.

    Tcl form:
        ``algorithm Newton [-initial] [-initialThenCurrent]``

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        algo = model.analysis.algorithm.newton(initial_then_current=True)
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

    def __init__(self, initial: bool = False, initial_then_current: bool = False):
        """Create a Newton-Raphson solution algorithm.

        Args:
            initial: If True, uses the initial stiffness matrix throughout the iterations.
            initial_then_current: If True, uses initial stiffness for the first iteration,
                and then reforms the tangent stiffness for subsequent iterations.

        Raises:
            ValueError: If both initial and initial_then_current are set to True.
        """
        super().__init__("Newton")
        self.initial = initial
        self.initial_then_current = initial_then_current
        
        # Check for incompatible options
        if self.initial and self.initial_then_current:
            raise ValueError("Cannot specify both -initial and -initialThenCurrent flags")
    
    def to_tcl(self) -> str:
        """Render this algorithm as an OpenSees Tcl command.

        Returns:
            The Tcl command string.
        """
        cmd = "algorithm Newton"
        if self.initial:
            cmd += " -initial"
        if self.initial_then_current:
            cmd += " -initialThenCurrent"
        return cmd
    


class ModifiedNewtonAlgorithm(Algorithm):
    """Modified Newton-Raphson nonlinear solution algorithm.

    ModifiedNewtonAlgorithm solves nonlinear equilibrium equations by reforming
    the tangent stiffness matrix only at the beginning of each analysis step,
    reducing computational cost compared to the standard Newton-Raphson method.

    Tcl form:
        ``algorithm ModifiedNewton [-initial] [-factoronce]``

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        algo = model.analysis.algorithm.modifiednewton(factor_once=True)
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

    def __init__(self, initial: bool = False, factor_once: bool = False):
        """Create a Modified Newton solution algorithm.

        Args:
            initial: If True, uses initial stiffness iterations.
            factor_once: If True, factorizes the stiffness matrix only once.
        """
        super().__init__("ModifiedNewton")
        self.initial = initial
        self.factor_once = factor_once
    
    def to_tcl(self) -> str:
        """Render this algorithm as an OpenSees Tcl command.

        Returns:
            The Tcl command string.
        """
        cmd = "algorithm ModifiedNewton"
        if self.initial:
            cmd += " -initial"
        if self.factor_once:
            cmd += " -factoronce"
        return cmd
    


class NewtonLineSearchAlgorithm(Algorithm):
    """Newton solution algorithm with line search acceleration.

    NewtonLineSearchAlgorithm introduces line search techniques to the
    standard Newton-Raphson iterations to enhance convergence robustness,
    especially in highly nonlinear problems (such as contact or plasticity).

    Tcl form:
        ``algorithm NewtonLineSearch -type <typeSearch> [-tol <tol>] [-maxIter <max>] [-minEta <min>] [-maxEta <max>]``

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        algo = model.analysis.algorithm.newtonlinesearch(
            type_search="Secant",
            tol=0.5,
        )
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

    def __init__(self, type_search: str = "InitialInterpolated", tol: float = 0.8, 
                 max_iter: int = 10, min_eta: float = 0.1, max_eta: float = 10.0):
        """Create a Newton Line Search solution algorithm.

        Args:
            type_search: Line search algorithm type. Must be one of
                `'Bisection'`, `'Secant'`, `'RegulaFalsi'`, or `'InitialInterpolated'`.
            tol: Tolerance for the line search convergence.
            max_iter: Maximum number of line search iterations per step.
            min_eta: Minimum scaling factor limit.
            max_eta: Maximum scaling factor limit.

        Raises:
            ValueError: If type_search is not a valid line search type.
        """
        super().__init__("NewtonLineSearch")
        self.type_search = type_search
        self.tol = tol
        self.max_iter = max_iter
        self.min_eta = min_eta
        self.max_eta = max_eta
        
        # Validate search type
        valid_search_types = ["Bisection", "Secant", "RegulaFalsi", "InitialInterpolated"]
        if self.type_search not in valid_search_types:
            raise ValueError(f"Invalid search type: {self.type_search}. "
                           f"Valid types are: {', '.join(valid_search_types)}")
    
    def to_tcl(self) -> str:
        """Render this algorithm as an OpenSees Tcl command.

        Returns:
            The Tcl command string.
        """
        cmd = f"algorithm NewtonLineSearch -type {self.type_search}"
        
        # Add other parameters if they're not default values
        if self.tol != 0.8:
            cmd += f" -tol {self.tol}"
        if self.max_iter != 10:
            cmd += f" -maxIter {self.max_iter}"
        if self.min_eta != 0.1:
            cmd += f" -minEta {self.min_eta}"
        if self.max_eta != 10.0:
            cmd += f" -maxEta {self.max_eta}"
            
        return cmd
    


class KrylovNewtonAlgorithm(Algorithm):
    """Krylov-Newton accelerated nonlinear solution algorithm.

    KrylovNewtonAlgorithm uses a modified Newton-Raphson method combined with
    Krylov subspace acceleration to speed up iteration convergence.

    Tcl form:
        ``algorithm KrylovNewton [-iterate <type>] [-increment <type>] [-maxDim <dim>]``

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        algo = model.analysis.algorithm.krylovnewton(max_dim=5)
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

    def __init__(self, tang_iter: str = "current", tang_incr: str = "current", max_dim: int = 3):
        """Create a Krylov-Newton solution algorithm.

        Args:
            tang_iter: Tangent to iterate on. Must be `'current'`, `'initial'`, or `'noTangent'`.
            tang_incr: Tangent to increment on. Must be `'current'`, `'initial'`, or `'noTangent'`.
            max_dim: Max number of subspace iterations before reforming the tangent.

        Raises:
            ValueError: If tang_iter or tang_incr is not a valid option.
        """
        super().__init__("KrylovNewton")
        self.tang_iter = tang_iter
        self.tang_incr = tang_incr
        self.max_dim = max_dim
        
        # Validate tangent options
        valid_tangent_options = ["current", "initial", "noTangent"]
        if self.tang_iter not in valid_tangent_options:
            raise ValueError(f"Invalid tangent iteration type: {self.tang_iter}. "
                           f"Valid types are: {', '.join(valid_tangent_options)}")
        if self.tang_incr not in valid_tangent_options:
            raise ValueError(f"Invalid tangent increment type: {self.tang_incr}. "
                           f"Valid types are: {', '.join(valid_tangent_options)}")
    
    def to_tcl(self) -> str:
        """Render this algorithm as an OpenSees Tcl command.

        Returns:
            The Tcl command string.
        """
        cmd = "algorithm KrylovNewton"
        
        # Add parameters if they're not default values
        if self.tang_iter != "current":
            cmd += f" -iterate {self.tang_iter}"
        if self.tang_incr != "current":
            cmd += f" -increment {self.tang_incr}"
        if self.max_dim != 3:
            cmd += f" -maxDim {self.max_dim}"
            
        return cmd
    


class SecantNewtonAlgorithm(Algorithm):
    """Secant-Newton accelerated solution algorithm.

    SecantNewtonAlgorithm uses two-term secant updates of the stiffness matrix
    to accelerate equilibrium iteration convergence without reforming the full tangent.

    Tcl form:
        ``algorithm SecantNewton [-iterate <type>] [-increment <type>] [-maxDim <dim>]``

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        algo = model.analysis.algorithm.secantnewton(tang_iter="initial")
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

    def __init__(self, tang_iter: str = "current", tang_incr: str = "current", max_dim: int = 3):
        """Create a Secant-Newton solution algorithm.

        Args:
            tang_iter: Tangent to iterate on. Must be `'current'`, `'initial'`, or `'noTangent'`.
            tang_incr: Tangent to increment on. Must be `'current'`, `'initial'`, or `'noTangent'`.
            max_dim: Max number of iterations before reforming the tangent.

        Raises:
            ValueError: If tang_iter or tang_incr is not a valid option.
        """
        super().__init__("SecantNewton")
        self.tang_iter = tang_iter
        self.tang_incr = tang_incr
        self.max_dim = max_dim
        
        # Validate tangent options
        valid_tangent_options = ["current", "initial", "noTangent"]
        if self.tang_iter not in valid_tangent_options:
            raise ValueError(f"Invalid tangent iteration type: {self.tang_iter}. "
                           f"Valid types are: {', '.join(valid_tangent_options)}")
        if self.tang_incr not in valid_tangent_options:
            raise ValueError(f"Invalid tangent increment type: {self.tang_incr}. "
                           f"Valid types are: {', '.join(valid_tangent_options)}")
    
    def to_tcl(self) -> str:
        """Render this algorithm as an OpenSees Tcl command.

        Returns:
            The Tcl command string.
        """
        cmd = "algorithm SecantNewton"
        
        # Add parameters if they're not default values
        if self.tang_iter != "current":
            cmd += f" -iterate {self.tang_iter}"
        if self.tang_incr != "current":
            cmd += f" -increment {self.tang_incr}"
        if self.max_dim != 3:
            cmd += f" -maxDim {self.max_dim}"
            
        return cmd
    


class BFGSAlgorithm(Algorithm):
    """Broyden-Fletcher-Goldfarb-Shanno (BFGS) solution algorithm.

    BFGSAlgorithm performs successive rank-two updates of the tangent stiffness
    matrix, optimized for symmetric systems to accelerate convergence.

    Tcl form:
        ``algorithm BFGS <count>``

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        algo = model.analysis.algorithm.bfgs(count=10)
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

    def __init__(self, count: int):
        """Create a BFGS solution algorithm.

        Args:
            count: Number of iterations before reforming the tangent stiffness matrix.

        Raises:
            ValueError: If count is not a positive integer.
        """
        super().__init__("BFGS")
        self.count = count
        
        # Validate count
        if not isinstance(self.count, int) or self.count < 1:
            raise ValueError("Count must be a positive integer")
    
    def to_tcl(self) -> str:
        """Render this algorithm as an OpenSees Tcl command.

        Returns:
            The Tcl command string.
        """
        return f"algorithm BFGS {self.count}"
    


class BroydenAlgorithm(Algorithm):
    """Broyden quasi-Newton solution algorithm.

    BroydenAlgorithm performs successive rank-one updates of the tangent stiffness
    matrix, optimized for general unsymmetric nonlinear structural systems.

    Tcl form:
        ``algorithm Broyden <count>``

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        algo = model.analysis.algorithm.broyden(count=8)
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

    def __init__(self, count: int):
        """Create a Broyden solution algorithm.

        Args:
            count: Number of iterations before reforming the tangent stiffness matrix.

        Raises:
            ValueError: If count is not a positive integer.
        """
        super().__init__("Broyden")
        self.count = count
        
        # Validate count
        if not isinstance(self.count, int) or self.count < 1:
            raise ValueError("Count must be a positive integer")
    
    def to_tcl(self) -> str:
        """Render this algorithm as an OpenSees Tcl command.

        Returns:
            The Tcl command string.
        """
        return f"algorithm Broyden {self.count}"
    


class ExpressNewtonAlgorithm(Algorithm):
    """Express Newton nonlinear solution algorithm.

    ExpressNewtonAlgorithm executes a fixed number of Newton-Raphson iterations
    and accepts the solution regardless of convergence status, speeding up
    dynamic simulations where approximate equilibrium is tolerable.

    Tcl form:
        ``algorithm ExpressNewton <iterCount> <kMultiplier> [-initialTangent] [-currentTangent] [-factorOnce]``

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        algo = model.analysis.algorithm.expressnewton(iter_count=2, k_multiplier=1.2)
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

    def __init__(self, iter_count: int = 2, k_multiplier: float = 1.0, 
                 initial_tangent: bool = False, current_tangent: bool = True, 
                 factor_once: bool = False):
        """Create an Express Newton solution algorithm.

        Args:
            iter_count: Constant number of iterations to perform.
            k_multiplier: Multiplier factor for system stiffness.
            initial_tangent: If True, uses initial stiffness matrix.
            current_tangent: If True, uses current tangent stiffness matrix.
            factor_once: If True, factors system stiffness only once.

        Raises:
            ValueError: If iter_count is not positive, or if both initial_tangent
                and current_tangent are set to True.
        """
        super().__init__("ExpressNewton")
        self.iter_count = iter_count
        self.k_multiplier = k_multiplier
        self.initial_tangent = initial_tangent
        self.current_tangent = current_tangent
        self.factor_once = factor_once
        
        # Validate iter_count
        if not isinstance(self.iter_count, int) or self.iter_count < 1:
            raise ValueError("Iteration count must be a positive integer")
        
        # Check for incompatible options
        if self.initial_tangent and self.current_tangent:
            raise ValueError("Cannot specify both -initialTangent and -currentTangent flags")
    
    def to_tcl(self) -> str:
        """Render this algorithm as an OpenSees Tcl command.

        Returns:
            The Tcl command string.
        """
        cmd = f"algorithm ExpressNewton {self.iter_count} {self.k_multiplier}"
        
        # Add optional flags
        if self.initial_tangent:
            cmd += " -initialTangent"
        if self.current_tangent and not self.initial_tangent:
            cmd += " -currentTangent"
        if self.factor_once:
            cmd += " -factorOnce"
            
        return cmd
    


class AlgorithmManager(TaggedComponentManager[Algorithm]):
    def __init__(self, analysis_manager) -> None:
        super().__init__(analysis_manager, Algorithm, "_algorithms")

    def linear(self, **kwargs) -> Algorithm:
        return self.add(LinearAlgorithm(**kwargs))

    def newton(self, **kwargs) -> Algorithm:
        return self.add(NewtonAlgorithm(**kwargs))

    def modifiednewton(self, **kwargs) -> Algorithm:
        return self.add(ModifiedNewtonAlgorithm(**kwargs))

    def newtonlinesearch(self, **kwargs) -> Algorithm:
        return self.add(NewtonLineSearchAlgorithm(**kwargs))

    def krylovnewton(self, **kwargs) -> Algorithm:
        return self.add(KrylovNewtonAlgorithm(**kwargs))

    def secantnewton(self, **kwargs) -> Algorithm:
        return self.add(SecantNewtonAlgorithm(**kwargs))

    def bfgs(self, **kwargs) -> Algorithm:
        return self.add(BFGSAlgorithm(**kwargs))

    def broyden(self, **kwargs) -> Algorithm:
        return self.add(BroydenAlgorithm(**kwargs))

    def expressnewton(self, **kwargs) -> Algorithm:
        return self.add(ExpressNewtonAlgorithm(**kwargs))


# Register all algorithms
Algorithm.register_algorithm('linear', LinearAlgorithm)
Algorithm.register_algorithm('newton', NewtonAlgorithm)
Algorithm.register_algorithm('modifiednewton', ModifiedNewtonAlgorithm)
Algorithm.register_algorithm('newtonlinesearch', NewtonLineSearchAlgorithm)
Algorithm.register_algorithm('krylovnewton', KrylovNewtonAlgorithm)
Algorithm.register_algorithm('secantnewton', SecantNewtonAlgorithm)
Algorithm.register_algorithm('bfgs', BFGSAlgorithm)
Algorithm.register_algorithm('broyden', BroydenAlgorithm)
Algorithm.register_algorithm('expressnewton', ExpressNewtonAlgorithm)
