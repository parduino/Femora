from typing import Dict, List, Type

from femora.core.analysis_component_base import AnalysisComponent


class Numberer(AnalysisComponent):
    """Base class for OpenSees degree-of-freedom (DOF) numberers.

    Numberers map structural node and equation definitions to solver system indices.
    """

    _numberers: Dict[str, Type["Numberer"]] = {}

    def __init__(self) -> None:
        """Create a Numberer base instance."""
        super().__init__()

    @staticmethod
    def register_numberer(name: str, numberer_class: Type["Numberer"]) -> None:
        """Register a new numberer class.

        Args:
            name: Lowercase registry name.
            numberer_class: The Numberer class type to register.
        """
        Numberer._numberers[name.lower()] = numberer_class

    @staticmethod
    def get_available_types() -> List[str]:
        """Get available registered numberer type names.

        Returns:
            A list of registered numberer names.
        """
        return list(Numberer._numberers.keys())


class PlainNumberer(Numberer):
    """Plain degree-of-freedom (DOF) numberer.

    PlainNumberer assigns equation numbers to nodes in the order they were
    defined in the model input, without any optimization.

    Tcl form:
        ``numberer Plain``

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        numberer = model.analysis.numberer.plain()
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

    def __init__(self) -> None:
        """Create a Plain degree-of-freedom numberer."""
        super().__init__()

    def to_tcl(self) -> str:
        """Render this numberer as an OpenSees Tcl command.

        Returns:
            The Tcl command string.
        """
        return "numberer Plain"


class RCMNumberer(Numberer):
    """Reverse Cuthill-McKee (RCM) degree-of-freedom numberer.

    RCMNumberer uses the Reverse Cuthill-McKee algorithm to optimize nodal numbering,
    reducing the bandwidth of the system equations and accelerating solver time.

    Tcl form:
        ``numberer RCM``

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        numberer = model.analysis.numberer.rcm()
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

    def __init__(self) -> None:
        """Create an RCM degree-of-freedom numberer."""
        super().__init__()

    def to_tcl(self) -> str:
        """Render this numberer as an OpenSees Tcl command.

        Returns:
            The Tcl command string.
        """
        return "numberer RCM"


class AMDNumberer(Numberer):
    """Approximate Minimum Degree (AMD) degree-of-freedom numberer.

    AMDNumberer uses the Approximate Minimum Degree ordering algorithm to minimize
    fill-in of the sparse system stiffness matrix.

    Tcl form:
        ``numberer AMD``

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        numberer = model.analysis.numberer.amd()
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

    def __init__(self) -> None:
        """Create an AMD degree-of-freedom numberer."""
        super().__init__()

    def to_tcl(self) -> str:
        """Render this numberer as an OpenSees Tcl command.

        Returns:
            The Tcl command string.
        """
        return "numberer AMD"


class ParallelRCMNumberer(Numberer):
    """Parallel Reverse Cuthill-McKee degree-of-freedom numberer.

    ParallelRCMNumberer is the parallel version of the RCM node numbering algorithm,
    suited for multi-processor simulations.

    Tcl form:
        ``numberer ParallelRCM``

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        numberer = model.analysis.numberer.parallelrcm()
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

    def __init__(self) -> None:
        """Create a ParallelRCM degree-of-freedom numberer."""
        super().__init__()

    def to_tcl(self) -> str:
        """Render this numberer as an OpenSees Tcl command.

        Returns:
            The Tcl command string.
        """
        return "numberer ParallelRCM"


Numberer.register_numberer("plain", PlainNumberer)
Numberer.register_numberer("rcm", RCMNumberer)
Numberer.register_numberer("amd", AMDNumberer)
Numberer.register_numberer("parallelrcm", ParallelRCMNumberer)
