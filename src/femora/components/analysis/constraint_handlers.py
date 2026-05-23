from typing import Dict, List, Optional, Type, Union

from femora.core.tagged_component_manager import TaggedComponentManager
from .base import AnalysisComponent


class ConstraintHandler(AnalysisComponent):
    """Base class for OpenSees constraint handlers."""

    _handlers: Dict[str, Type["ConstraintHandler"]] = {}

    def __init__(self, handler_type: str) -> None:
        super().__init__()
        self.handler_type = handler_type

    @staticmethod
    def register_handler(name: str, handler_class: Type["ConstraintHandler"]) -> None:
        ConstraintHandler._handlers[name.lower()] = handler_class


class PlainConstraintHandler(ConstraintHandler):
    """
    Plain constraint handler, does not follow the constraint definitions across the model evolution
    """
    def __init__(self):
        super().__init__("Plain")
    
    def to_tcl(self) -> str:
        return "constraints Plain"
    


class TransformationConstraintHandler(ConstraintHandler):
    """
    Transformation constraint handler, performs static condensation of the constraint degrees of freedom
    """
    def __init__(self):
        super().__init__("Transformation")
    
    def to_tcl(self) -> str:
        return "constraints Transformation"
    


class PenaltyConstraintHandler(ConstraintHandler):
    """
    Penalty constraint handler, uses penalty numbers to enforce constraints
    """
    def __init__(self, alpha_s: float, alpha_m: float):
        super().__init__("Penalty")
        self.alpha_s = alpha_s
        self.alpha_m = alpha_m
    
    def to_tcl(self) -> str:
        return f"constraints Penalty {self.alpha_s} {self.alpha_m}"
    


class LagrangeConstraintHandler(ConstraintHandler):
    """
    Lagrange multipliers constraint handler, uses Lagrange multipliers to enforce constraints
    """
    def __init__(self, alpha_s: float = 1.0, alpha_m: float = 1.0):
        super().__init__("Lagrange")
        self.alpha_s = alpha_s
        self.alpha_m = alpha_m
    
    def to_tcl(self) -> str:
        return f"constraints Lagrange {self.alpha_s} {self.alpha_m}"
    


class AutoConstraintHandler(ConstraintHandler):
    """
    Automatic constraint handler, automatically selects the penalty value for compatibility constraints
    """
    def __init__(self, verbose: bool = False, auto_penalty: Optional[float] = None, 
                 user_penalty: Optional[float] = None):
        super().__init__("Auto")
        self.verbose = verbose
        self.auto_penalty = auto_penalty
        self.user_penalty = user_penalty
    
    def to_tcl(self) -> str:
        cmd = "constraints Auto"
        if self.verbose:
            cmd += " -verbose"
        if self.auto_penalty is not None:
            cmd += f" -autoPenalty {self.auto_penalty}"
        if self.user_penalty is not None:
            cmd += f" -userPenalty {self.user_penalty}"
        return cmd
    


class ConstraintHandlerManager(TaggedComponentManager[ConstraintHandler]):
    def __init__(self, analysis_manager) -> None:
        super().__init__(analysis_manager, ConstraintHandler, "_handlers")

    def plain(self, **kwargs) -> ConstraintHandler:
        return self.add(PlainConstraintHandler(**kwargs))

    def transformation(self, **kwargs) -> ConstraintHandler:
        return self.add(TransformationConstraintHandler(**kwargs))

    def penalty(self, **kwargs) -> ConstraintHandler:
        return self.add(PenaltyConstraintHandler(**kwargs))

    def lagrange(self, **kwargs) -> ConstraintHandler:
        return self.add(LagrangeConstraintHandler(**kwargs))

    def auto(self, **kwargs) -> ConstraintHandler:
        return self.add(AutoConstraintHandler(**kwargs))


# Register all constraint handlers
ConstraintHandler.register_handler('plain', PlainConstraintHandler)
ConstraintHandler.register_handler('transformation', TransformationConstraintHandler)
ConstraintHandler.register_handler('penalty', PenaltyConstraintHandler)
ConstraintHandler.register_handler('lagrange', LagrangeConstraintHandler)
ConstraintHandler.register_handler('auto', AutoConstraintHandler)
