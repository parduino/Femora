from typing import Dict, List, Type

from femora.core.analysis_component_base import AnalysisComponent


class Numberer(AnalysisComponent):
    """Base class for OpenSees DOF numberers."""

    _numberers: Dict[str, Type["Numberer"]] = {}

    def __init__(self) -> None:
        super().__init__()

    @staticmethod
    def register_numberer(name: str, numberer_class: Type["Numberer"]) -> None:
        Numberer._numberers[name.lower()] = numberer_class

    @staticmethod
    def get_available_types() -> List[str]:
        return list(Numberer._numberers.keys())


class PlainNumberer(Numberer):
    def to_tcl(self) -> str:
        return "numberer Plain"


class RCMNumberer(Numberer):
    def to_tcl(self) -> str:
        return "numberer RCM"


class AMDNumberer(Numberer):
    def to_tcl(self) -> str:
        return "numberer AMD"


class ParallelRCMNumberer(Numberer):
    def to_tcl(self) -> str:
        return "numberer ParallelRCM"


Numberer.register_numberer("plain", PlainNumberer)
Numberer.register_numberer("rcm", RCMNumberer)
Numberer.register_numberer("amd", AMDNumberer)
Numberer.register_numberer("parallelrcm", ParallelRCMNumberer)
