from __future__ import annotations

from typing import Dict, Type

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


__all__ = ["System"]
