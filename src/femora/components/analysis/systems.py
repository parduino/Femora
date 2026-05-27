from typing import Dict, List, Optional, Type, Union

from femora.core.tagged_component_manager import TaggedComponentManager
from femora.core.analysis_component_base import AnalysisComponent


class System(AnalysisComponent):
    """Base class for OpenSees solver systems."""

    _systems: Dict[str, Type["System"]] = {}

    def __init__(self, system_type: str) -> None:
        """Create a System base instance.

        Args:
            system_type: The type name of the system solver.
        """
        super().__init__()
        self.system_type = system_type

    @staticmethod
    def register_system(name: str, system_class: Type["System"]) -> None:
        """Register a new solver system class.

        Args:
            name: Lowercase registry name.
            system_class: The System class type to register.
        """
        System._systems[name.lower()] = system_class


class FullGeneralSystem(System):
    """Full general linear system solver.

    FullGeneralSystem stores and solves the complete dense matrix equations
    without any optimization. It is primarily suitable only for very small systems.

    Tcl form:
        ``system FullGeneral``

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        system = model.analysis.system.fullgeneral()
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

    def __init__(self):
        """Create a FullGeneral solver system."""
        super().__init__("FullGeneral")
    
    def to_tcl(self) -> str:
        """Render this system solver as an OpenSees Tcl command.

        Returns:
            The Tcl command string.
        """
        return "system FullGeneral"
    


class BandGeneralSystem(System):
    """Banded general linear system solver.

    BandGeneralSystem optimizes storage and solving time by working only within
    the bandwidth of a non-symmetric general matrix structure.

    Tcl form:
        ``system BandGeneral``

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        system = model.analysis.system.bandgeneral()
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

    def __init__(self):
        """Create a BandGeneral solver system."""
        super().__init__("BandGeneral")
    
    def to_tcl(self) -> str:
        """Render this system solver as an OpenSees Tcl command.

        Returns:
            The Tcl command string.
        """
        return "system BandGeneral"
    


class BandSPDSystem(System):
    """Banded symmetric positive definite linear system solver.

    BandSPDSystem utilizes banded profile storage tailored specifically for
    symmetric positive definite (SPD) system matrices to accelerate solution.

    Tcl form:
        ``system BandSPD``

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        system = model.analysis.system.bandspd()
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

    def __init__(self):
        """Create a BandSPD solver system."""
        super().__init__("BandSPD")
    
    def to_tcl(self) -> str:
        """Render this system solver as an OpenSees Tcl command.

        Returns:
            The Tcl command string.
        """
        return "system BandSPD"
    


class ProfileSPDSystem(System):
    """Profile symmetric positive definite linear system solver.

    ProfileSPDSystem utilizes active column (skyline) storage and a profile solver
    specifically optimized for symmetric positive definite (SPD) system matrices.

    Tcl form:
        ``system ProfileSPD``

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        system = model.analysis.system.profilespd()
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

    def __init__(self):
        """Create a ProfileSPD solver system."""
        super().__init__("ProfileSPD")
    
    def to_tcl(self) -> str:
        """Render this system solver as an OpenSees Tcl command.

        Returns:
            The Tcl command string.
        """
        return "system ProfileSPD"
    


class SuperLUSystem(System):
    """SuperLU sparse linear system solver.

    SuperLUSystem is a sparse direct solver designed to solve general
    non-symmetric sparse systems of linear equations.

    Tcl form:
        ``system SuperLU``

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        system = model.analysis.system.superlu()
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

    def __init__(self):
        """Create a SuperLU solver system."""
        super().__init__("SuperLU")
    
    def to_tcl(self) -> str:
        """Render this system solver as an OpenSees Tcl command.

        Returns:
            The Tcl command string.
        """
        return "system SuperLU"
    


class UmfpackSystem(System):
    """UMFPACK sparse linear system solver.

    UmfpackSystem is an unsymmetric multi-frontal sparse direct solver used to
    efficiently solve sparse linear systems.

    Tcl form:
        ``system Umfpack [-lvalueFact <lvalueFact>]``

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        system = model.analysis.system.umfpack(lvalue_fact=4.0)
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

    def __init__(self, lvalue_fact: Optional[float] = None):
        """Create a Umfpack sparse solver system.

        Args:
            lvalue_fact: Factor controlling matrix storage reallocation sizing.
                Defaults to None.
        """
        super().__init__("Umfpack")
        self.lvalue_fact = lvalue_fact
    
    def to_tcl(self) -> str:
        """Render this system solver as an OpenSees Tcl command.

        Returns:
            The Tcl command string.
        """
        cmd = "system Umfpack"
        if self.lvalue_fact is not None:
            cmd += f" -lvalueFact {self.lvalue_fact}"
        return cmd
    


class MumpsSystem(System):
    """MUMPS sparse direct linear system solver.

    MumpsSystem implements the MUMPS (MUltifrontal Massively Parallel Solver)
    high-performance direct sparse solver for symmetric or unsymmetric equations.

    Tcl form:
        ``system Mumps [-ICNTL14 <icntl14>] [-ICNTL7 <icntl7>]``

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        system = model.analysis.system.mumps(icntl14=20.0, icntl7=5)
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

    def __init__(self, icntl14: Optional[float] = None, icntl7: Optional[int] = None):
        """Create a MUMPS direct solver system.

        Args:
            icntl14: Percentage increase in estimated workspace during solver setup.
            icntl7: Ordering symmetric permutation algorithm flag.
                0 for AMD, 1 set by user, 2 AMF, 3 SCOTCH, 4 PORD, 5 Metis,
                6 AMD with QADM, 7 automatic.
        """
        super().__init__("Mumps")
        self.icntl14 = icntl14
        self.icntl7 = icntl7
    
    def to_tcl(self) -> str:
        """Render this system solver as an OpenSees Tcl command.

        Returns:
            The Tcl command string.
        """
        cmd = "system Mumps"
        if self.icntl14 is not None:
            cmd += f" -ICNTL14 {self.icntl14}"
        if self.icntl7 is not None:
            cmd += f" -ICNTL7 {self.icntl7}"
        return cmd
    


class SystemManager(TaggedComponentManager[System]):
    """Manager for system solvers on the Analysis model."""

    def __init__(self, analysis_manager) -> None:
        """Initialize the SystemManager.

        Args:
            analysis_manager: The parent AnalysisManager instance.
        """
        super().__init__(analysis_manager, System, "_systems")

    def fullgeneral(self, **kwargs) -> System:
        """Add a FullGeneralSystem solver.

        Args:
            **kwargs: Keyword arguments passed to FullGeneralSystem.

        Returns:
            The solver system instance.
        """
        return self.add(FullGeneralSystem(**kwargs))

    def bandgeneral(self, **kwargs) -> System:
        """Add a BandGeneralSystem solver.

        Args:
            **kwargs: Keyword arguments passed to BandGeneralSystem.

        Returns:
            The solver system instance.
        """
        return self.add(BandGeneralSystem(**kwargs))

    def bandspd(self, **kwargs) -> System:
        """Add a BandSPDSystem solver.

        Args:
            **kwargs: Keyword arguments passed to BandSPDSystem.

        Returns:
            The solver system instance.
        """
        return self.add(BandSPDSystem(**kwargs))

    def profilespd(self, **kwargs) -> System:
        """Add a ProfileSPDSystem solver.

        Args:
            **kwargs: Keyword arguments passed to ProfileSPDSystem.

        Returns:
            The solver system instance.
        """
        return self.add(ProfileSPDSystem(**kwargs))

    def superlu(self, **kwargs) -> System:
        """Add a SuperLUSystem solver.

        Args:
            **kwargs: Keyword arguments passed to SuperLUSystem.

        Returns:
            The solver system instance.
        """
        return self.add(SuperLUSystem(**kwargs))

    def umfpack(self, **kwargs) -> System:
        """Add a UmfpackSystem solver.

        Args:
            **kwargs: Keyword arguments passed to UmfpackSystem.

        Returns:
            The solver system instance.
        """
        return self.add(UmfpackSystem(**kwargs))

    def mumps(self, **kwargs) -> System:
        """Add a MumpsSystem solver.

        Args:
            **kwargs: Keyword arguments passed to MumpsSystem.

        Returns:
            The solver system instance.
        """
        return self.add(MumpsSystem(**kwargs))


# Register all systems
System.register_system('fullgeneral', FullGeneralSystem)
System.register_system('bandgeneral', BandGeneralSystem)
System.register_system('bandspd', BandSPDSystem)
System.register_system('profilespd', ProfileSPDSystem)
System.register_system('superlu', SuperLUSystem)
System.register_system('umfpack', UmfpackSystem)
System.register_system('mumps', MumpsSystem)
