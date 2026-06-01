from __future__ import annotations

from typing import Dict, Type

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


__all__ = ["Algorithm"]
