from typing import Dict, List, Type, Union

from femora.core.tagged_component_manager import TaggedComponentManager
from .base import AnalysisComponent


class Test(AnalysisComponent):
    """Base class for OpenSees convergence tests."""

    _tests: Dict[str, Type["Test"]] = {}

    def __init__(self, test_type: str) -> None:
        super().__init__()
        self.test_type = test_type

    @staticmethod
    def register_test(name: str, test_class: Type["Test"]) -> None:
        Test._tests[name.lower()] = test_class


class NormUnbalanceTest(Test):
    """
    Norm unbalance test, checks the norm of the residual (unbalanced forces) vector 
    against a tolerance.
    """
    def __init__(self, tol: float, max_iter: int, print_flag: int = 0, norm_type: int = 2):
        """
        Initialize a NormUnbalance test.
        
        Args:
            tol (float): Tolerance criteria for convergence
            max_iter (int): Maximum iterations before failure
            print_flag (int, optional): Print control flag:
                0: Print nothing (default)
                1: Print norm information each iteration
                2: Print norms and iterations at successful test end
                4: Print norms, displacement vector, and residual vector
                5: Print error message but return successful test
            norm_type (int, optional): Norm type to use:
                0: Max-norm
                1: 1-norm
                2: 2-norm (default)
        """
        super().__init__("NormUnbalance")
        self.tol = tol
        self.max_iter = max_iter
        self.print_flag = print_flag
        self.norm_type = norm_type
    
    def to_tcl(self) -> str:
        """
        Convert the test to a TCL command string for OpenSees
        
        Returns:
            str: The TCL command string
        """
        return f"test NormUnbalance {self.tol} {self.max_iter} {self.print_flag} {self.norm_type}"


class NormDispIncrTest(Test):
    """
    Norm displacement increment test, checks the norm of the displacement 
    increment vector against a tolerance.
    """
    def __init__(self, tol: float, max_iter: int, print_flag: int = 0, norm_type: int = 2):
        """
        Initialize a NormDispIncr test.
        
        Args:
            tol (float): Tolerance criteria for convergence
            max_iter (int): Maximum iterations before failure
            print_flag (int, optional): Print control flag:
                0: Print nothing (default)
                1: Print norm information each iteration
                2: Print norms and iterations at successful test end
                4: Print norms, displacement vector, and residual vector
                5: Print error message but return successful test
            norm_type (int, optional): Norm type to use:
                0: Max-norm
                1: 1-norm
                2: 2-norm (default)
        """
        super().__init__("NormDispIncr")
        self.tol = tol
        self.max_iter = max_iter
        self.print_flag = print_flag
        self.norm_type = norm_type
    
    def to_tcl(self) -> str:
        """
        Convert the test to a TCL command string for OpenSees
        
        Returns:
            str: The TCL command string
        """
        return f"test NormDispIncr {self.tol} {self.max_iter} {self.print_flag} {self.norm_type}"


class EnergyIncrTest(Test):
    """
    Energy increment test, checks the energy increment (0.5 * x^T * b) against a tolerance.
    """
    def __init__(self, tol: float, max_iter: int, print_flag: int = 0):
        """
        Initialize an EnergyIncr test.
        
        Args:
            tol (float): Tolerance criteria for convergence
            max_iter (int): Maximum iterations before failure
            print_flag (int, optional): Print control flag:
                0: Print nothing (default)
                1: Print norm information each iteration
                2: Print norms and iterations at successful test end
                4: Print norms, displacement vector, and residual vector
                5: Print error message but return successful test
        """
        super().__init__("EnergyIncr")
        self.tol = tol
        self.max_iter = max_iter
        self.print_flag = print_flag
    
    def to_tcl(self) -> str:
        """
        Convert the test to a TCL command string for OpenSees
        
        Returns:
            str: The TCL command string
        """
        return f"test EnergyIncr {self.tol} {self.max_iter} {self.print_flag}"


class RelativeNormUnbalanceTest(Test):
    """
    Relative norm unbalance test, compares current unbalance to initial unbalance.
    """
    def __init__(self, tol: float, max_iter: int, print_flag: int = 0, norm_type: int = 2):
        """
        Initialize a RelativeNormUnbalance test.
        
        Args:
            tol (float): Tolerance criteria for convergence
            max_iter (int): Maximum iterations before failure
            print_flag (int, optional): Print control flag:
                0: Print nothing (default)
                1: Print norm information each iteration
                2: Print norms and iterations at successful test end
                4: Print norms, displacement vector, and residual vector
                5: Print error message but return successful test
            norm_type (int, optional): Norm type to use:
                0: Max-norm
                1: 1-norm
                2: 2-norm (default)
        """
        super().__init__("RelativeNormUnbalance")
        self.tol = tol
        self.max_iter = max_iter
        self.print_flag = print_flag
        self.norm_type = norm_type
    
    def to_tcl(self) -> str:
        """
        Convert the test to a TCL command string for OpenSees
        
        Returns:
            str: The TCL command string
        """
        return f"test RelativeNormUnbalance {self.tol} {self.max_iter} {self.print_flag} {self.norm_type}"


class RelativeNormDispIncrTest(Test):
    """
    Relative norm displacement increment test, tracks relative changes in displacement.
    """
    def __init__(self, tol: float, max_iter: int, print_flag: int = 0, norm_type: int = 2):
        """
        Initialize a RelativeNormDispIncr test.
        
        Args:
            tol (float): Tolerance criteria for convergence
            max_iter (int): Maximum iterations before failure
            print_flag (int, optional): Print control flag:
                0: Print nothing (default)
                1: Print norm information each iteration
                2: Print norms and iterations at successful test end
                4: Print norms, displacement vector, and residual vector
                5: Print error message but return successful test
            norm_type (int, optional): Norm type to use:
                0: Max-norm
                1: 1-norm
                2: 2-norm (default)
        """
        super().__init__("RelativeNormDispIncr")
        self.tol = tol
        self.max_iter = max_iter
        self.print_flag = print_flag
        self.norm_type = norm_type
    
    def to_tcl(self) -> str:
        """
        Convert the test to a TCL command string for OpenSees
        
        Returns:
            str: The TCL command string
        """
        return f"test RelativeNormDispIncr {self.tol} {self.max_iter} {self.print_flag} {self.norm_type}"


class RelativeTotalNormDispIncrTest(Test):
    """
    Relative total norm displacement increment test, tracks cumulative displacement changes.
    """
    def __init__(self, tol: float, max_iter: int, print_flag: int = 0, norm_type: int = 2):
        """
        Initialize a RelativeTotalNormDispIncr test.
        
        Args:
            tol (float): Tolerance criteria for convergence
            max_iter (int): Maximum iterations before failure
            print_flag (int, optional): Print control flag:
                0: Print nothing (default)
                1: Print norm information each iteration
                2: Print norms and iterations at successful test end
                4: Print norms, displacement vector, and residual vector
                5: Print error message but return successful test
            norm_type (int, optional): Norm type to use:
                0: Max-norm
                1: 1-norm
                2: 2-norm (default)
        """
        super().__init__("RelativeTotalNormDispIncr")
        self.tol = tol
        self.max_iter = max_iter
        self.print_flag = print_flag
        self.norm_type = norm_type
    
    def to_tcl(self) -> str:
        """
        Convert the test to a TCL command string for OpenSees
        
        Returns:
            str: The TCL command string
        """
        return f"test RelativeTotalNormDispIncr {self.tol} {self.max_iter} {self.print_flag} {self.norm_type}"


class RelativeEnergyIncrTest(Test):
    """
    Relative energy increment test, compares energy increment relative to first iteration.
    """
    def __init__(self, tol: float, max_iter: int, print_flag: int = 0):
        """
        Initialize a RelativeEnergyIncr test.
        
        Args:
            tol (float): Tolerance criteria for convergence
            max_iter (int): Maximum iterations before failure
            print_flag (int, optional): Print control flag:
                0: Print nothing (default)
                1: Print norm information each iteration
                2: Print norms and iterations at successful test end
                4: Print norms, displacement vector, and residual vector
                5: Print error message but return successful test
        """
        super().__init__("RelativeEnergyIncr")
        self.tol = tol
        self.max_iter = max_iter
        self.print_flag = print_flag
    
    def to_tcl(self) -> str:
        """
        Convert the test to a TCL command string for OpenSees
        
        Returns:
            str: The TCL command string
        """
        return f"test RelativeEnergyIncr {self.tol} {self.max_iter} {self.print_flag}"


class FixedNumIterTest(Test):
    """
    Fixed number iterations test, runs a fixed number of iterations without checking convergence.
    """
    def __init__(self, num_iter: int):
        """
        Initialize a FixedNumIter test.
        
        Args:
            num_iter (int): Number of iterations to perform
        """
        super().__init__("FixedNumIter")
        self.num_iter = num_iter
    
    def to_tcl(self) -> str:
        """
        Convert the test to a TCL command string for OpenSees
        
        Returns:
            str: The TCL command string
        """
        return f"test FixedNumIter {self.num_iter}"


class NormDispAndUnbalanceTest(Test):
    """
    Norm displacement and unbalance test, requires both displacement and unbalance norms to converge.
    """
    def __init__(self, tol_incr: float, tol_r: float, max_iter: int, 
                 print_flag: int = 0, norm_type: int = 2, max_incr: int = -1):
        """
        Initialize a NormDispAndUnbalance test.
        
        Args:
            tol_incr (float): Tolerance for left-hand solution increments
            tol_r (float): Tolerance for right-hand residual
            max_iter (int): Maximum iterations before failure
            print_flag (int, optional): Print control flag:
                0: Print nothing (default)
                1: Print norm information each iteration
                2: Print norms and iterations at successful test end
                4: Print norms, displacement vector, and residual vector
                5: Print error message but return successful test
            norm_type (int, optional): Norm type to use:
                0: Max-norm
                1: 1-norm
                2: 2-norm (default)
            max_incr (int, optional): Maximum times error can increase 
                                     (-1 for default behavior)
        """
        super().__init__("NormDispAndUnbalance")
        self.tol_incr = tol_incr
        self.tol_r = tol_r
        self.max_iter = max_iter
        self.print_flag = print_flag
        self.norm_type = norm_type
        self.max_incr = max_incr
    
    def to_tcl(self) -> str:
        """
        Convert the test to a TCL command string for OpenSees
        
        Returns:
            str: The TCL command string
        """
        return f"test NormDispAndUnbalance {self.tol_incr} {self.tol_r} {self.max_iter} {self.print_flag} {self.norm_type} {self.max_incr}"


class NormDispOrUnbalanceTest(Test):
    """
    Norm displacement or unbalance test, convergence achieved if either displacement 
    or unbalance norm criterion is met.
    """
    def __init__(self, tol_incr: float, tol_r: float, max_iter: int, 
                 print_flag: int = 0, norm_type: int = 2, max_incr: int = -1):
        """
        Initialize a NormDispOrUnbalance test.
        
        Args:
            tol_incr (float): Tolerance for left-hand solution increments
            tol_r (float): Tolerance for right-hand residual
            max_iter (int): Maximum iterations before failure
            print_flag (int, optional): Print control flag:
                0: Print nothing (default)
                1: Print norm information each iteration
                2: Print norms and iterations at successful test end
                4: Print norms, displacement vector, and residual vector
                5: Print error message but return successful test
            norm_type (int, optional): Norm type to use:
                0: Max-norm
                1: 1-norm
                2: 2-norm (default)
            max_incr (int, optional): Maximum times error can increase 
                                     (-1 for default behavior)
        """
        super().__init__("NormDispOrUnbalance")
        self.tol_incr = tol_incr
        self.tol_r = tol_r
        self.max_iter = max_iter
        self.print_flag = print_flag
        self.norm_type = norm_type
        self.max_incr = max_incr
    
    def to_tcl(self) -> str:
        """
        Convert the test to a TCL command string for OpenSees
        
        Returns:
            str: The TCL command string
        """
        return f"test NormDispOrUnbalance {self.tol_incr} {self.tol_r} {self.max_iter} {self.print_flag} {self.norm_type} {self.max_incr}"


class TestManager(TaggedComponentManager[Test]):
    def __init__(self, analysis_manager) -> None:
        super().__init__(analysis_manager, Test, "_tests")

    def normunbalance(self, **kwargs) -> Test:
        return self.add(NormUnbalanceTest(**kwargs))

    def normdispincr(self, **kwargs) -> Test:
        return self.add(NormDispIncrTest(**kwargs))

    def energyincr(self, **kwargs) -> Test:
        return self.add(EnergyIncrTest(**kwargs))

    def relativenormunbalance(self, **kwargs) -> Test:
        return self.add(RelativeNormUnbalanceTest(**kwargs))

    def relativenormdispincr(self, **kwargs) -> Test:
        return self.add(RelativeNormDispIncrTest(**kwargs))

    def relativetotalnormdispincr(self, **kwargs) -> Test:
        return self.add(RelativeTotalNormDispIncrTest(**kwargs))

    def relativeenergyincr(self, **kwargs) -> Test:
        return self.add(RelativeEnergyIncrTest(**kwargs))

    def fixednumiter(self, **kwargs) -> Test:
        return self.add(FixedNumIterTest(**kwargs))

    def normdispandunbalance(self, **kwargs) -> Test:
        return self.add(NormDispAndUnbalanceTest(**kwargs))

    def normdisporunbalance(self, **kwargs) -> Test:
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