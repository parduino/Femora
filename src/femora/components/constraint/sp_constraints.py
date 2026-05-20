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
    """Fix constraint"""
    
    def __init__(self, node_tag: int, dofs: List[int]):
        """
        Initialize Fix constraint
        
        Args:
            node_tag: Tag of the node to be fixed
            dofs: List of DOF constraint values (0 or 1)
                  0 unconstrained (or free)
                  1 constrained (or fixed)
        """
        super().__init__(node_tag, dofs)
    
    def to_tcl(self) -> str:
        """Convert constraint to TCL command for OpenSees"""
        return f"fix {self.node_tag} {' '.join(map(str, self.dofs))};"


class FixXConstraint(SPConstraint):
    """FixX constraint"""
    
    def __init__(self, xCoordinate: float, dofs: List[int], tol: float = 1e-10):
        """
        Initialize FixX constraint
        
        Args:
            xCoordinate: x-coordinate of nodes to be constrained
            dofs: List of DOF constraint values (0 or 1)
                  0 unconstrained (or free)
                  1 constrained (or fixed)
            tol: Tolerance for coordinate comparison (default: 1e-10)
        """
        # Use -1 as a placeholder for node tag since it applies to multiple nodes
        super().__init__(-1, dofs)
        self.xCoordinate = xCoordinate
        self.tol = tol
    
    def to_tcl(self) -> str:
        """Convert constraint to TCL command for OpenSees"""
        return f"fixX {self.xCoordinate} {' '.join(map(str, self.dofs))} -tol {self.tol};"


class FixYConstraint(SPConstraint):
    """FixY constraint"""
    
    def __init__(self, yCoordinate: float, dofs: List[int], tol: float = 1e-10):
        """
        Initialize FixY constraint
        
        Args:
            yCoordinate: y-coordinate of nodes to be constrained
            dofs: List of DOF constraint values (0 or 1)
                  0 unconstrained (or free)
                  1 constrained (or fixed)
            tol: Tolerance for coordinate comparison (default: 1e-10)
        """
        # Use -1 as a placeholder for node tag since it applies to multiple nodes
        super().__init__(-1, dofs)
        self.yCoordinate = yCoordinate
        self.tol = tol
    
    def to_tcl(self) -> str:
        """Convert constraint to TCL command for OpenSees"""
        return f"fixY {self.yCoordinate} {' '.join(map(str, self.dofs))} -tol {self.tol};"


class FixZConstraint(SPConstraint):
    """FixZ constraint"""
    
    def __init__(self, zCoordinate: float, dofs: List[int], tol: float = 1e-10):
        """
        Initialize FixZ constraint
        
        Args:
            zCoordinate: z-coordinate of nodes to be constrained
            dofs: List of DOF constraint values (0 or 1)
                  0 unconstrained (or free)
                  1 constrained (or fixed)
            tol: Tolerance for coordinate comparison (default: 1e-10)
        """
        # Use -1 as a placeholder for node tag since it applies to multiple nodes
        super().__init__(-1, dofs)
        self.zCoordinate = zCoordinate
        self.tol = tol
    
    def to_tcl(self) -> str:
        """Convert constraint to TCL command for OpenSees"""
        return f"fixZ {self.zCoordinate} {' '.join(map(str, self.dofs))} -tol {self.tol};"
    

class FixMacroX_max(SPConstraint):
    """
    FixX constraint for maximum X coordinate which is 
    defined as macro with name X_MAX in the TCL file
    """
    def __init__(self, dofs: List[int], tol: float = 1e-10):
        """
        Initialize FixX constraint
        
        Args:
            dofs: List of DOF constraint values (0 or 1)
                  0 unconstrained (or free)
                  1 constrained (or fixed)
            tol: Tolerance for coordinate comparison (default: 1e-10)
        """
        # Use -1 as a placeholder for node tag since it applies to multiple nodes
        super().__init__(-1, dofs)
        self.tol = tol
    
    def to_tcl(self) -> str:
        """Convert constraint to TCL command for OpenSees"""
        return f"fixX $X_MAX {' '.join(map(str, self.dofs))} -tol {self.tol};"
    
class FixMacroY_max(SPConstraint):
    """
    FixY constraint for maximum Y coordinate which is 
    defined as macro with name Y_MAX in the TCL file
    """
    def __init__(self, dofs: List[int], tol: float = 1e-10):
        """
        Initialize FixY constraint
        
        Args:
            dofs: List of DOF constraint values (0 or 1)
                  0 unconstrained (or free)
                  1 constrained (or fixed)
            tol: Tolerance for coordinate comparison (default: 1e-10)
        """
        # Use -1 as a placeholder for node tag since it applies to multiple nodes
        super().__init__(-1, dofs)
        self.tol = tol
    
    def to_tcl(self) -> str:
        """Convert constraint to TCL command for OpenSees"""
        return f"fixY $Y_MAX {' '.join(map(str, self.dofs))} -tol {self.tol};"
    
class FixMacroZ_max(SPConstraint):
    """
    FixZ constraint for maximum Z coordinate which is 
    defined as macro with name Z_MAX in the TCL file
    """
    def __init__(self, dofs: List[int], tol: float = 1e-10):
        """
        Initialize FixZ constraint
        
        Args:
            dofs: List of DOF constraint values (0 or 1)
                  0 unconstrained (or free)
                  1 constrained (or fixed)
            tol: Tolerance for coordinate comparison (default: 1e-10)
        """
        # Use -1 as a placeholder for node tag since it applies to multiple nodes
        super().__init__(-1, dofs)
        self.tol = tol
    
    def to_tcl(self) -> str:
        """Convert constraint to TCL command for OpenSees"""
        return f"fixZ $Z_MAX {' '.join(map(str, self.dofs))} -tol {self.tol};"


class FixMacroX_min(SPConstraint):
    """
    FixX constraint for minimum X coordinate which is 
    defined as macro with name X_MIN in the TCL file
    """
    def __init__(self, dofs: List[int], tol: float = 1e-10):
        """
        Initialize FixX constraint
        
        Args:
            dofs: List of DOF constraint values (0 or 1)
                  0 unconstrained (or free)
                  1 constrained (or fixed)
            tol: Tolerance for coordinate comparison (default: 1e-10)
        """
        # Use -1 as a placeholder for node tag since it applies to multiple nodes
        super().__init__(-1, dofs)
        self.tol = tol
    
    def to_tcl(self) -> str:
        """Convert constraint to TCL command for OpenSees"""
        return f"fixX $X_MIN {' '.join(map(str, self.dofs))} -tol {self.tol};"
    

class FixMacroY_min(SPConstraint):
    """
    FixY constraint for minimum Y coordinate which is 
    defined as macro with name Y_MIN in the TCL file
    """
    def __init__(self, dofs: List[int], tol: float = 1e-10):
        """
        Initialize FixY constraint
        
        Args:
            dofs: List of DOF constraint values (0 or 1)
                  0 unconstrained (or free)
                  1 constrained (or fixed)
            tol: Tolerance for coordinate comparison (default: 1e-10)
        """
        # Use -1 as a placeholder for node tag since it applies to multiple nodes
        super().__init__(-1, dofs)
        self.tol = tol
    
    def to_tcl(self) -> str:
        """Convert constraint to TCL command for OpenSees"""
        return f"fixY $Y_MIN {' '.join(map(str, self.dofs))} -tol {self.tol};"
    

class FixMacroZ_min(SPConstraint):
    """
    FixZ constraint for minimum Z coordinate which is 
    defined as macro with name Z_MIN in the TCL file
    """
    def __init__(self, dofs: List[int], tol: float = 1e-10):
        """
        Initialize FixZ constraint
        
        Args:
            dofs: List of DOF constraint values (0 or 1)
                  0 unconstrained (or free)
                  1 constrained (or fixed)
            tol: Tolerance for coordinate comparison (default: 1e-10)
        """
        # Use -1 as a placeholder for node tag since it applies to multiple nodes
        super().__init__(-1, dofs)
        # check if the dofs are 0 or 1
        if not all(dof in [0, 1] for dof in dofs):
            raise ValueError("DOFs must be 0 or 1")
        self.tol = tol
    
    def to_tcl(self) -> str:
        """Convert constraint to TCL command for OpenSees"""
        return f"fixZ $Z_MIN {' '.join(map(str, self.dofs))} -tol {self.tol};"
    


