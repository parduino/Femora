from typing import Dict, List, Type, Union

from femora.core.tagged_component_manager import TaggedComponentManager
from femora.core.analysis_component_base import AnalysisComponent


class Test(AnalysisComponent):
    """Base class for all OpenSees convergence tests.

    Convergence tests define the mathematical criteria used by solution
    algorithms to determine if equilibrium has been reached at each iteration.
    """

    _tests: Dict[str, Type["Test"]] = {}

    def __init__(self, test_type: str) -> None:
        """Create a convergence test base instance.

        Args:
            test_type: The type name of the convergence test.
        """
        super().__init__()
        self.test_type = test_type

    @staticmethod
    def register_test(name: str, test_class: Type["Test"]) -> None:
        """Register a new convergence test class.

        Args:
            name: Lowercase registry name.
            test_class: The Test class type to register.
        """
        Test._tests[name.lower()] = test_class


class NormUnbalanceTest(Test):
    """Norm unbalance convergence test.

    NormUnbalanceTest checks the norm of the residual (unbalanced force) vector
    against a user-specified tolerance. Convergence is achieved when the norm is
    less than or equal to the tolerance.

    Tcl form:
        ``test NormUnbalance <tol> <maxIter> <printFlag> <normType>``

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        test = model.analysis.test.normunbalance(
            tol=1e-6,
            max_iter=100,
            print_flag=1,
            norm_type=2,
        )
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

    def __init__(self, tol: float, max_iter: int, print_flag: int = 0, norm_type: int = 2):
        """Create a NormUnbalance convergence test.

        Args:
            tol: Tolerance criteria for convergence.
            max_iter: Maximum number of iterations to perform before returning failure.
            print_flag: Print control flag. 0 prints nothing, 1 prints norm info
                each iteration, 2 prints norms and iterations at success, 4 prints
                norms, displacement, and residual vectors, 5 prints warnings only.
            norm_type: Mathematical norm type to use. 0 for Max-norm, 1 for 1-norm,
                2 for 2-norm (default).
        """
        super().__init__("NormUnbalance")
        self.tol = tol
        self.max_iter = max_iter
        self.print_flag = print_flag
        self.norm_type = norm_type
    
    def to_tcl(self) -> str:
        """Render this convergence test as an OpenSees Tcl command.

        Returns:
            The Tcl command string.
        """
        return f"test NormUnbalance {self.tol} {self.max_iter} {self.print_flag} {self.norm_type}"


class NormDispIncrTest(Test):
    """Norm displacement increment convergence test.

    NormDispIncrTest checks the norm of the displacement increment vector
    against a user-specified tolerance. Convergence is achieved when the norm of
    the displacement increment is less than or equal to the tolerance.

    Tcl form:
        ``test NormDispIncr <tol> <maxIter> <printFlag> <normType>``

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        test = model.analysis.test.normdispincr(
            tol=1e-6,
            max_iter=100,
            print_flag=1,
            norm_type=2,
        )
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

    def __init__(self, tol: float, max_iter: int, print_flag: int = 0, norm_type: int = 2):
        """Create a NormDispIncr convergence test.

        Args:
            tol: Tolerance criteria for convergence.
            max_iter: Maximum number of iterations to perform before returning failure.
            print_flag: Print control flag. 0 prints nothing, 1 prints norm info
                each iteration, 2 prints norms and iterations at success, 4 prints
                norms, displacement, and residual vectors, 5 prints warnings only.
            norm_type: Mathematical norm type to use. 0 for Max-norm, 1 for 1-norm,
                2 for 2-norm (default).
        """
        super().__init__("NormDispIncr")
        self.tol = tol
        self.max_iter = max_iter
        self.print_flag = print_flag
        self.norm_type = norm_type
    
    def to_tcl(self) -> str:
        """Render this convergence test as an OpenSees Tcl command.

        Returns:
            The Tcl command string.
        """
        return f"test NormDispIncr {self.tol} {self.max_iter} {self.print_flag} {self.norm_type}"


class EnergyIncrTest(Test):
    """Energy increment convergence test.

    EnergyIncrTest checks the work/energy increment against a tolerance. The
    energy increment is computed as 0.5 * dU^T * R, where dU is the displacement
    increment and R is the residual force vector.

    Tcl form:
        ``test EnergyIncr <tol> <maxIter> <printFlag>``

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        test = model.analysis.test.energyincr(
            tol=1e-6,
            max_iter=100,
            print_flag=1,
        )
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

    def __init__(self, tol: float, max_iter: int, print_flag: int = 0):
        """Create an EnergyIncr convergence test.

        Args:
            tol: Tolerance criteria for convergence.
            max_iter: Maximum number of iterations to perform before returning failure.
            print_flag: Print control flag. 0 prints nothing, 1 prints norm info
                each iteration, 2 prints norms and iterations at success, 4 prints
                norms, displacement, and residual vectors, 5 prints warnings only.
        """
        super().__init__("EnergyIncr")
        self.tol = tol
        self.max_iter = max_iter
        self.print_flag = print_flag
    
    def to_tcl(self) -> str:
        """Render this convergence test as an OpenSees Tcl command.

        Returns:
            The Tcl command string.
        """
        return f"test EnergyIncr {self.tol} {self.max_iter} {self.print_flag}"


class RelativeNormUnbalanceTest(Test):
    """Relative norm unbalance convergence test.

    RelativeNormUnbalanceTest compares the current norm of the residual vector
    against the initial residual norm scaled by a tolerance. Convergence is
    achieved when current residual norm <= tol * initial residual norm.

    Tcl form:
        ``test RelativeNormUnbalance <tol> <maxIter> <printFlag> <normType>``

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        test = model.analysis.test.relativenormunbalance(
            tol=1e-6,
            max_iter=100,
            print_flag=1,
            norm_type=2,
        )
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

    def __init__(self, tol: float, max_iter: int, print_flag: int = 0, norm_type: int = 2):
        """Create a RelativeNormUnbalance convergence test.

        Args:
            tol: Tolerance criteria for convergence.
            max_iter: Maximum number of iterations to perform before returning failure.
            print_flag: Print control flag. 0 prints nothing, 1 prints norm info
                each iteration, 2 prints norms and iterations at success, 4 prints
                norms, displacement, and residual vectors, 5 prints warnings only.
            norm_type: Mathematical norm type to use. 0 for Max-norm, 1 for 1-norm,
                2 for 2-norm (default).
        """
        super().__init__("RelativeNormUnbalance")
        self.tol = tol
        self.max_iter = max_iter
        self.print_flag = print_flag
        self.norm_type = norm_type
    
    def to_tcl(self) -> str:
        """Render this convergence test as an OpenSees Tcl command.

        Returns:
            The Tcl command string.
        """
        return f"test RelativeNormUnbalance {self.tol} {self.max_iter} {self.print_flag} {self.norm_type}"


class RelativeNormDispIncrTest(Test):
    """Relative norm displacement increment convergence test.

    RelativeNormDispIncrTest compares the current norm of the displacement increment
    against the initial displacement increment norm scaled by a tolerance.

    Tcl form:
        ``test RelativeNormDispIncr <tol> <maxIter> <printFlag> <normType>``

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        test = model.analysis.test.relativenormdispincr(
            tol=1e-6,
            max_iter=100,
            print_flag=1,
            norm_type=2,
        )
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

    def __init__(self, tol: float, max_iter: int, print_flag: int = 0, norm_type: int = 2):
        """Create a RelativeNormDispIncr convergence test.

        Args:
            tol: Tolerance criteria for convergence.
            max_iter: Maximum number of iterations to perform before returning failure.
            print_flag: Print control flag. 0 prints nothing, 1 prints norm info
                each iteration, 2 prints norms and iterations at success, 4 prints
                norms, displacement, and residual vectors, 5 prints warnings only.
            norm_type: Mathematical norm type to use. 0 for Max-norm, 1 for 1-norm,
                2 for 2-norm (default).
        """
        super().__init__("RelativeNormDispIncr")
        self.tol = tol
        self.max_iter = max_iter
        self.print_flag = print_flag
        self.norm_type = norm_type
    
    def to_tcl(self) -> str:
        """Render this convergence test as an OpenSees Tcl command.

        Returns:
            The Tcl command string.
        """
        return f"test RelativeNormDispIncr {self.tol} {self.max_iter} {self.print_flag} {self.norm_type}"


class RelativeTotalNormDispIncrTest(Test):
    """Relative total norm displacement increment convergence test.

    RelativeTotalNormDispIncrTest checks the current norm of the displacement
    increment against the cumulative total displacement increment norm.

    Tcl form:
        ``test RelativeTotalNormDispIncr <tol> <maxIter> <printFlag> <normType>``

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        test = model.analysis.test.relativetotalnormdispincr(
            tol=1e-6,
            max_iter=100,
            print_flag=1,
            norm_type=2,
        )
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

    def __init__(self, tol: float, max_iter: int, print_flag: int = 0, norm_type: int = 2):
        """Create a RelativeTotalNormDispIncr convergence test.

        Args:
            tol: Tolerance criteria for convergence.
            max_iter: Maximum number of iterations to perform before returning failure.
            print_flag: Print control flag. 0 prints nothing, 1 prints norm info
                each iteration, 2 prints norms and iterations at success, 4 prints
                norms, displacement, and residual vectors, 5 prints warnings only.
            norm_type: Mathematical norm type to use. 0 for Max-norm, 1 for 1-norm,
                2 for 2-norm (default).
        """
        super().__init__("RelativeTotalNormDispIncr")
        self.tol = tol
        self.max_iter = max_iter
        self.print_flag = print_flag
        self.norm_type = norm_type
    
    def to_tcl(self) -> str:
        """Render this convergence test as an OpenSees Tcl command.

        Returns:
            The Tcl command string.
        """
        return f"test RelativeTotalNormDispIncr {self.tol} {self.max_iter} {self.print_flag} {self.norm_type}"


class RelativeEnergyIncrTest(Test):
    """Relative energy increment convergence test.

    RelativeEnergyIncrTest compares the current energy increment against the
    initial energy increment scaled by a tolerance.

    Tcl form:
        ``test RelativeEnergyIncr <tol> <maxIter> <printFlag>``

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        test = model.analysis.test.relativeenergyincr(
            tol=1e-6,
            max_iter=100,
            print_flag=1,
        )
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

    def __init__(self, tol: float, max_iter: int, print_flag: int = 0):
        """Create a RelativeEnergyIncr convergence test.

        Args:
            tol: Tolerance criteria for convergence.
            max_iter: Maximum number of iterations to perform before returning failure.
            print_flag: Print control flag. 0 prints nothing, 1 prints norm info
                each iteration, 2 prints norms and iterations at success, 4 prints
                norms, displacement, and residual vectors, 5 prints warnings only.
        """
        super().__init__("RelativeEnergyIncr")
        self.tol = tol
        self.max_iter = max_iter
        self.print_flag = print_flag
    
    def to_tcl(self) -> str:
        """Render this convergence test as an OpenSees Tcl command.

        Returns:
            The Tcl command string.
        """
        return f"test RelativeEnergyIncr {self.tol} {self.max_iter} {self.print_flag}"


class FixedNumIterTest(Test):
    """Fixed number of iterations convergence test.

    FixedNumIterTest performs a fixed number of iterations without assessing
    actual physical or numerical convergence.

    Warning:
        This test does not guarantee structural equilibrium and should only be
        used for benchmarking, testing, or specific state updating steps.

    Tcl form:
        ``test FixedNumIter <numIter>``

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        test = model.analysis.test.fixednumiter(num_iter=5)
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

    def __init__(self, num_iter: int):
        """Create a FixedNumIter convergence test.

        Args:
            num_iter: Exact number of iterations to perform at each step.
        """
        super().__init__("FixedNumIter")
        self.num_iter = num_iter
    
    def to_tcl(self) -> str:
        """Render this convergence test as an OpenSees Tcl command.

        Returns:
            The Tcl command string.
        """
        return f"test FixedNumIter {self.num_iter}"


class NormDispAndUnbalanceTest(Test):
    """Norm displacement increment AND unbalance force convergence test.

    NormDispAndUnbalanceTest requires both the displacement increment norm and the
    unbalanced force norm to satisfy their respective tolerances.

    Tcl form:
        ``test NormDispAndUnbalance <tolIncr> <tolR> <maxIter> <printFlag> <normType> <maxIncr>``

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        test = model.analysis.test.normdispandunbalance(
            tol_incr=1e-6,
            tol_r=1e-6,
            max_iter=100,
            print_flag=1,
            norm_type=2,
            max_incr=-1,
        )
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

    def __init__(self, tol_incr: float, tol_r: float, max_iter: int, 
                 print_flag: int = 0, norm_type: int = 2, max_incr: int = -1):
        """Create a NormDispAndUnbalance convergence test.

        Args:
            tol_incr: Tolerance for displacement increment norm.
            tol_r: Tolerance for unbalanced force residual norm.
            max_iter: Maximum number of iterations to perform before returning failure.
            print_flag: Print control flag. 0 prints nothing, 1 prints norm info
                each iteration, 2 prints norms and iterations at success, 4 prints
                norms, displacement, and residual vectors, 5 prints warnings only.
            norm_type: Mathematical norm type to use. 0 for Max-norm, 1 for 1-norm,
                2 for 2-norm (default).
            max_incr: Maximum times the error can increase before giving up.
                Use -1 for default.
        """
        super().__init__("NormDispAndUnbalance")
        self.tol_incr = tol_incr
        self.tol_r = tol_r
        self.max_iter = max_iter
        self.print_flag = print_flag
        self.norm_type = norm_type
        self.max_incr = max_incr
    
    def to_tcl(self) -> str:
        """Render this convergence test as an OpenSees Tcl command.

        Returns:
            The Tcl command string.
        """
        return f"test NormDispAndUnbalance {self.tol_incr} {self.tol_r} {self.max_iter} {self.print_flag} {self.norm_type} {self.max_incr}"


class NormDispOrUnbalanceTest(Test):
    """Norm displacement increment OR unbalance force convergence test.

    NormDispOrUnbalanceTest achieves convergence if either the displacement
    increment norm OR the unbalanced force norm satisfies its respective tolerance.

    Tcl form:
        ``test NormDispOrUnbalance <tolIncr> <tolR> <maxIter> <printFlag> <normType> <maxIncr>``

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        test = model.analysis.test.normdisporunbalance(
            tol_incr=1e-6,
            tol_r=1e-6,
            max_iter=100,
            print_flag=1,
            norm_type=2,
            max_incr=-1,
        )
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

    def __init__(self, tol_incr: float, tol_r: float, max_iter: int, 
                 print_flag: int = 0, norm_type: int = 2, max_incr: int = -1):
        """Create a NormDispOrUnbalance convergence test.

        Args:
            tol_incr: Tolerance for displacement increment norm.
            tol_r: Tolerance for unbalanced force residual norm.
            max_iter: Maximum number of iterations to perform before returning failure.
            print_flag: Print control flag. 0 prints nothing, 1 prints norm info
                each iteration, 2 prints norms and iterations at success, 4 prints
                norms, displacement, and residual vectors, 5 prints warnings only.
            norm_type: Mathematical norm type to use. 0 for Max-norm, 1 for 1-norm,
                2 for 2-norm (default).
            max_incr: Maximum times the error can increase before giving up.
                Use -1 for default.
        """
        super().__init__("NormDispOrUnbalance")
        self.tol_incr = tol_incr
        self.tol_r = tol_r
        self.max_iter = max_iter
        self.print_flag = print_flag
        self.norm_type = norm_type
        self.max_incr = max_incr
    
    def to_tcl(self) -> str:
        """Render this convergence test as an OpenSees Tcl command.

        Returns:
            The Tcl command string.
        """
        return f"test NormDispOrUnbalance {self.tol_incr} {self.tol_r} {self.max_iter} {self.print_flag} {self.norm_type} {self.max_incr}"


class TestManager(TaggedComponentManager[Test]):
    """Manager for convergence tests on the Analysis model."""

    def __init__(self, analysis_manager) -> None:
        """Initialize the TestManager.

        Args:
            analysis_manager: The parent AnalysisManager instance.
        """
        super().__init__(analysis_manager, Test, "_tests")

    def normunbalance(self, **kwargs) -> Test:
        """Add a NormUnbalanceTest convergence test.

        Args:
            **kwargs: Keyword arguments passed to NormUnbalanceTest.

        Returns:
            The convergence test instance.
        """
        return self.add(NormUnbalanceTest(**kwargs))

    def normdispincr(self, **kwargs) -> Test:
        """Add a NormDispIncrTest convergence test.

        Args:
            **kwargs: Keyword arguments passed to NormDispIncrTest.

        Returns:
            The convergence test instance.
        """
        return self.add(NormDispIncrTest(**kwargs))

    def energyincr(self, **kwargs) -> Test:
        """Add an EnergyIncrTest convergence test.

        Args:
            **kwargs: Keyword arguments passed to EnergyIncrTest.

        Returns:
            The convergence test instance.
        """
        return self.add(EnergyIncrTest(**kwargs))

    def relativenormunbalance(self, **kwargs) -> Test:
        """Add a RelativeNormUnbalanceTest convergence test.

        Args:
            **kwargs: Keyword arguments passed to RelativeNormUnbalanceTest.

        Returns:
            The convergence test instance.
        """
        return self.add(RelativeNormUnbalanceTest(**kwargs))

    def relativenormdispincr(self, **kwargs) -> Test:
        """Add a RelativeNormDispIncrTest convergence test.

        Args:
            **kwargs: Keyword arguments passed to RelativeNormDispIncrTest.

        Returns:
            The convergence test instance.
        """
        return self.add(RelativeNormDispIncrTest(**kwargs))

    def relativetotalnormdispincr(self, **kwargs) -> Test:
        """Add a RelativeTotalNormDispIncrTest convergence test.

        Args:
            **kwargs: Keyword arguments passed to RelativeTotalNormDispIncrTest.

        Returns:
            The convergence test instance.
        """
        return self.add(RelativeTotalNormDispIncrTest(**kwargs))

    def relativeenergyincr(self, **kwargs) -> Test:
        """Add a RelativeEnergyIncrTest convergence test.

        Args:
            **kwargs: Keyword arguments passed to RelativeEnergyIncrTest.

        Returns:
            The convergence test instance.
        """
        return self.add(RelativeEnergyIncrTest(**kwargs))

    def fixednumiter(self, **kwargs) -> Test:
        """Add a FixedNumIterTest convergence test.

        Args:
            **kwargs: Keyword arguments passed to FixedNumIterTest.

        Returns:
            The convergence test instance.
        """
        return self.add(FixedNumIterTest(**kwargs))

    def normdispandunbalance(self, **kwargs) -> Test:
        """Add a NormDispAndUnbalanceTest convergence test.

        Args:
            **kwargs: Keyword arguments passed to NormDispAndUnbalanceTest.

        Returns:
            The convergence test instance.
        """
        return self.add(NormDispAndUnbalanceTest(**kwargs))

    def normdisporunbalance(self, **kwargs) -> Test:
        """Add a NormDispOrUnbalanceTest convergence test.

        Args:
            **kwargs: Keyword arguments passed to NormDispOrUnbalanceTest.

        Returns:
            The convergence test instance.
        """
        return self.add(NormDispOrUnbalanceTest(**kwargs))


# Register all tests
Test.register_test('normunbalance', NormUnbalanceTest)
Test.register_test('normdispincr', NormDispIncrTest)
Test.register_test('energyincr', EnergyIncrTest)
Test.register_test('relativenormunbalance', RelativeNormUnbalanceTest)
Test.register_test('relativenormdispincr', RelativeNormDispIncrTest)
Test.register_test('relativetotalnormdispincr', RelativeTotalNormDispIncrTest)
Test.register_test('relativeenergyincr', RelativeEnergyIncrTest)
Test.register_test('fixednumiter', FixedNumIterTest)
Test.register_test('normdispandunbalance', NormDispAndUnbalanceTest)
Test.register_test('normdisporunbalance', NormDispOrUnbalanceTest)
