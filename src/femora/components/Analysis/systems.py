from typing import Dict, List, Optional, Type, Union

from femora.core.tagged_component_manager import TaggedComponentManager
from .base import AnalysisComponent


class System(AnalysisComponent):
    """Base class for OpenSees system solvers."""

    _systems: Dict[str, Type["System"]] = {}

    def __init__(self, system_type: str) -> None:
        super().__init__()
        self.system_type = system_type

    @staticmethod
    def register_system(name: str, system_class: Type["System"]) -> None:
        System._systems[name.lower()] = system_class


class FullGeneralSystem(System):
    """
    Full general system, is NOT optimized, uses all the matrix
    """
    def __init__(self):
        super().__init__("FullGeneral")
    
    def to_tcl(self) -> str:
        return "system FullGeneral"
    


class BandGeneralSystem(System):
    """
    Band general system, uses banded matrix storage
    """
    def __init__(self):
        super().__init__("BandGeneral")
    
    def to_tcl(self) -> str:
        return "system BandGeneral"
    


class BandSPDSystem(System):
    """
    Band SPD system, for symmetric positive definite matrices, uses banded profile storage
    """
    def __init__(self):
        super().__init__("BandSPD")
    
    def to_tcl(self) -> str:
        return "system BandSPD"
    


class ProfileSPDSystem(System):
    """
    Profile SPD system, for symmetric positive definite matrices, uses skyline storage
    """
    def __init__(self):
        super().__init__("ProfileSPD")
    
    def to_tcl(self) -> str:
        return "system ProfileSPD"
    


class SuperLUSystem(System):
    """
    SuperLU system, sparse system solver
    """
    def __init__(self):
        super().__init__("SuperLU")
    
    def to_tcl(self) -> str:
        return "system SuperLU"
    


class UmfpackSystem(System):
    """
    Umfpack system, sparse system solver
    """
    def __init__(self, lvalue_fact: Optional[float] = None):
        super().__init__("Umfpack")
        self.lvalue_fact = lvalue_fact
    
    def to_tcl(self) -> str:
        cmd = "system Umfpack"
        if self.lvalue_fact is not None:
            cmd += f" -lvalueFact {self.lvalue_fact}"
        return cmd
    


class MumpsSystem(System):
    """
    Mumps system, sparse direct solver
    """
    def __init__(self, icntl14: Optional[float] = None, icntl7: Optional[int] = None):
        """
        Initialize a Mumps System

        Args:
            icntl14 (float, optional): Controls the percentage increase in the estimated working space
            icntl7 (int, optional): Computes a symmetric permutation (ordering) for factorization
                0: AMD
                1: set by user
                2: AMF
                3: SCOTCH
                4: PORD
                5: Metis
                6: AMD with QADM
                7: automatic
        """
        super().__init__("Mumps")
        self.icntl14 = icntl14
        self.icntl7 = icntl7
    
    def to_tcl(self) -> str:
        """
        Convert the system to a TCL command string for OpenSees
        
        Returns:
            str: The TCL command string
        """
        cmd = "system Mumps"
        if self.icntl14 is not None:
            cmd += f" -ICNTL14 {self.icntl14}"
        if self.icntl7 is not None:
            cmd += f" -ICNTL7 {self.icntl7}"
        return cmd
    


class SystemManager(TaggedComponentManager[System]):
    def __init__(self, analysis_manager) -> None:
        super().__init__(analysis_manager, System, "_systems")


    def fullgeneral(self, **kwargs) -> System:
        return self.add(FullGeneralSystem(**kwargs))

    def bandgeneral(self, **kwargs) -> System:
        return self.add(BandGeneralSystem(**kwargs))

    def bandspd(self, **kwargs) -> System:
        return self.add(BandSPDSystem(**kwargs))

    def profilespd(self, **kwargs) -> System:
        return self.add(ProfileSPDSystem(**kwargs))

    def superlu(self, **kwargs) -> System:
        return self.add(SuperLUSystem(**kwargs))

    def umfpack(self, **kwargs) -> System:
        return self.add(UmfpackSystem(**kwargs))

    def mumps(self, **kwargs) -> System:
        return self.add(MumpsSystem(**kwargs))



# Register all systems
System.register_system('fullgeneral', FullGeneralSystem)
System.register_system('bandgeneral', BandGeneralSystem)
System.register_system('bandspd', BandSPDSystem)
System.register_system('profilespd', ProfileSPDSystem)
System.register_system('superlu', SuperLUSystem)
System.register_system('umfpack', UmfpackSystem)
System.register_system('mumps', MumpsSystem)